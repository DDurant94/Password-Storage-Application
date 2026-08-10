from database import db

from flask import request
from sqlalchemy.orm import Session
from sqlalchemy import select
import ast

from utils.utils import time, find_user
from utils.circuitbreaker import CircuitBreaker
from utils.encryption_utils import decrypted, encrypted, make_key, rekey_collection

from models.auditLog import AuditLog


class AuditLogService:
  """Encapsulates audit-log business logic with injectable collaborators."""

  def __init__(self, session_factory=None, clock=None, request_context=None):
    self._session_factory = session_factory
    self._clock = clock
    self._request_context = request_context

  @staticmethod
  def _token_to_storage(token):
    if isinstance(token, bytes):
      return token.decode('utf-8')
    return token

  @staticmethod
  def _storage_to_token(value):
    if isinstance(value, bytes):
      return value

    if isinstance(value, str):
      stripped_value = value.strip()
      if stripped_value.startswith(("b'", 'b"')):
        try:
          evaluated = ast.literal_eval(stripped_value)
          if isinstance(evaluated, (bytes, bytearray)):
            return bytes(evaluated)
        except (SyntaxError, ValueError):
          pass
      return stripped_value.encode('utf-8')

    raise ValueError('Unsupported audit token format')

  def save(self, user_data, action, detail):
    clock = self._clock or time
    request_context = self._request_context or request
    key = make_key(user_data.key, user_data.password)
    encrypted_ip = self._token_to_storage(encrypted(key, request_context.remote_addr))

    return AuditLog(
      user_id=user_data.user_id,
      action=action,
      time_stamp=clock(),
      details=detail,
      ip_address=encrypted_ip
    )

  def find(self, user_id, limit=50, offset=0):
    user = find_user(user_id)
    query = db.session.query(AuditLog).filter(AuditLog.user_id == user[0].user_id)
    if offset != 0 or limit != 50:
      query = query.order_by(AuditLog.time_stamp.desc()).offset(offset).limit(limit)
    else:
      query = query
    query = query.all()

    for log in query:
      try:
        encrypted_token = self._storage_to_token(log.ip_address)
        log.ip_address = decrypted(user[1], encrypted_token)
      except ValueError:
        log.ip_address = '[unable to decrypt]'

    return query

  def finder(self, key, user, rekeyed, limit=50):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        audits = session.execute(db.select(AuditLog).where(AuditLog.user_id == user.user_id).order_by(AuditLog.time_stamp.desc()).limit(limit)).scalars().all()

        for log in audits:
          encrypted_token = self._storage_to_token(log.ip_address)
          decrypted_ip = decrypted(key, encrypted_token)
          log.ip_address = self._token_to_storage(encrypted(rekeyed, decrypted_ip))
    return audits


audit_log_service = AuditLogService()
service_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=10)


@service_breaker
def save(user_data, action, detail):
  return audit_log_service.save(user_data, action, detail)


@service_breaker
def find(user_id, limit=50, offset=0):
  return audit_log_service.find(user_id, limit=limit, offset=offset)


@service_breaker
def finder(key, user, rekeyed, limit=50):
  return audit_log_service.finder(key, user, rekeyed, limit=limit)
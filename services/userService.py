from database import db

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

from utils.utils import encode_token, encode_refresh_token, decode_refresh_token, time, salt_maker as salt, find_user, make_key, INVALID_TOKEN_MESSAGE
from utils.circuitbreaker import CircuitBreaker
from utils.errorHandlers import ApiError

from services.auditLogService import save as audit_log, finder as fal
from services.passwordService import finder as fp
from services.passwordHistService import finder as fph
from services.securityQuestionService import finder as fsq

from models.user import User
from models.role import Role
from models.userManagement import UserManagementRole as UMR
from models.refreshToken import RefreshToken


class UserService:
  """Encapsulates user-related business logic with injectable collaborators."""

  def __init__(self, session_factory=None, audit_logger=None, password_hasher=None,
               password_verifier=None, token_encoder=None, rekeyer=None, clock=None):
    self._session_factory = session_factory
    self._audit_logger = audit_logger
    self._password_hasher = password_hasher
    self._password_verifier = password_verifier
    self._token_encoder = token_encoder
    self._rekeyer = rekeyer
    self._clock = clock

  def _non_business_failure(self, exc_type, _):
    """Treat non-ValueError exceptions as circuit-breaker failures."""
    return not issubclass(exc_type, ValueError)

  def _rekey_user_data(self, user, new_password):
    key = make_key(user.key, user.password)
    rekeyed = make_key(user.key, new_password)
    audits = fal(key, user, rekeyed)
    passwords = fp(key, user, rekeyed)
    history = fph(key, user, rekeyed)
    questions = fsq(key, user, rekeyed)
    return [audits, passwords, history, questions]

  def _resolve_rekeyer(self):
    return self._rekeyer if self._rekeyer is not None else update_getter

  def _execute_query(self, session, statement):
    target_session = session if session is not None else db.session
    execute = getattr(target_session, 'execute', None)

    if callable(execute):
      return execute(statement)

    raise TypeError("Session object must provide an execute() method")

  def _get_user_by_username(self, session, username):
    return self._execute_query(session, db.select(User).where(User.username == username)).unique().scalar_one_or_none()

  def _get_user_by_id(self, session, user_id):
    return self._execute_query(session, db.select(User).where(User.user_id == int(user_id))).unique().scalar_one_or_none()

  def _get_role_by_name(self, session, role_name):
    return self._execute_query(session, db.select(Role).where(Role.role_name == role_name)).scalar_one_or_none()

  def _refresh_exp_from_payload(self, payload):
    exp = payload.get('exp')
    if isinstance(exp, (int, float)):
      return datetime.fromtimestamp(exp, tz=timezone.utc)
    if isinstance(exp, datetime):
      return exp
    raise ValueError("Invalid refresh token")

  def _persist_refresh_token(self, session, user_id, payload):
    jti = payload.get('jti')
    if not jti:
      raise ValueError("Invalid refresh token")

    expires_at = self._refresh_exp_from_payload(payload)
    session.add(
      RefreshToken(
        user_id=user_id,
        jti=str(jti),
        expires_at=expires_at,
        revoked=False
      )
    )

  def save(self, user_data):
    if user_data['username'] == "Failure":
      raise RuntimeError("Failure condition triggered")

    session_factory = self._session_factory or Session
    audit_logger = self._audit_logger if self._audit_logger is not None else audit_log
    password_hasher = self._password_hasher if self._password_hasher is not None else generate_password_hash
    clock = self._clock if self._clock is not None else time

    with session_factory(db.engine) as session:
      with session.begin():
        user = self._get_user_by_username(session, user_data['username'])

        if user:
          raise ValueError("User Already Exists!")

        user_role = user_data.get('role', 'user')
        savepoint = session.begin_nested()

        new_user = User(username=user_data['username'],
                        password=password_hasher(user_data['password']),
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        email=user_data['email'],
                        create_date=clock(),
                        updated_date=clock(),
                        role=user_role,
                        key=salt())
        session.add(new_user)
        session.flush()

        role = self._get_role_by_name(session, new_user.role)

        if role is not None:
          session.add(UMR(user_management_id=new_user.user_id, role_id=role.role_id))
          session.add(audit_logger(new_user, "Creation", "Creating User Account"))
        else:
          savepoint.rollback()
          raise ValueError("Role Not Found! Add Role or Change Role")
      session.refresh(new_user)
    return new_user

  def find_by_id(self, user_id):
    user = find_user(user_id)
    return user[0]

  def update(self, user_data, user_id):
    session_factory = self._session_factory or Session
    audit_logger = self._audit_logger if self._audit_logger is not None else audit_log
    password_verifier = self._password_verifier if self._password_verifier is not None else check_password_hash
    password_hasher = self._password_hasher if self._password_hasher is not None else generate_password_hash
    clock = self._clock if self._clock is not None else time
    rekeyer = self._resolve_rekeyer()

    with session_factory(db.engine) as session:
      with session.begin():
        user = self._get_user_by_id(session, user_id)

        if user is None:
          raise ValueError("User not Found!")

        details = f"'{user.username}' updated "

        if user.first_name != user_data['first_name']:
          user.first_name = user_data['first_name']
          details += 'first name, '

        if user.last_name != user_data['last_name']:
          user.last_name = user_data['last_name']
          details += 'last name, '

        if user.email != user_data['email']:
          user.email = user_data['email']
          details += 'email, '

        if not password_verifier(user.password, user_data['password']):
          new_password = password_hasher(user_data['password'])
          rekeyer(user, new_password)
          user.password = new_password
          details += 'password '

        user.updated_date = clock()

        audit = audit_logger(user, 'Update', details)
        session.add(audit)
      session.refresh(user)
    return user

  def login_user(self, username, password):
    session_factory = self._session_factory or Session
    audit_logger = self._audit_logger if self._audit_logger is not None else audit_log
    password_verifier = self._password_verifier if self._password_verifier is not None else check_password_hash
    token_encoder = self._token_encoder if self._token_encoder is not None else encode_token

    with session_factory(db.engine) as session:
      with session.begin():
        login_outcome = [None, 'success']
        user = self._get_user_by_username(session, username)
        if user:
          detail = f"'{user.username}' "
          if password_verifier(user.password, password):
            role_names = [role.role_name for role in user.roles]
            auth_token = token_encoder(user.user_id, role_names)
            refresh_token = encode_refresh_token(user.user_id)
            refresh_payload = decode_refresh_token(refresh_token)
            self._persist_refresh_token(session, user.user_id, refresh_payload)
            resp = {
              "status": "success",
              "message": "Successfully logged in",
              "auth_token": auth_token,
              "refresh_token": refresh_token
            }

            login_outcome[0] = resp
            detail += 'Successfully logged in'

          else:
            login_outcome[1] = 'Password'
            detail += 'Failed login Password'

          audit = audit_logger(user, "Login", detail)

          session.add(audit)

        else:
          login_outcome[1] = 'Username'
    return login_outcome

  def refresh_user_token(self, refresh_token):
    payload = decode_refresh_token(refresh_token)
    user_id = int(payload['sub'])
    incoming_jti = str(payload.get('jti', ''))
    if not incoming_jti:
      raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401)

    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = self._get_user_by_id(session, user_id)
        if user is None:
          raise ValueError("User not Found!")

        current_refresh = self._execute_query(
          session,
          db.select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.jti == incoming_jti
          )
        ).scalar_one_or_none()

        if current_refresh is None or current_refresh.revoked:
          raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401)

        now = datetime.now(timezone.utc)
        expires_at = current_refresh.expires_at
        if expires_at.tzinfo is None:
          expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
          raise ApiError("Token has expired", status_code=401)

        current_refresh.revoked = True

        role_names = [role.role_name for role in user.roles]
        new_access_token = encode_token(user.user_id, role_names)
        new_refresh_token = encode_refresh_token(user.user_id)
        new_refresh_payload = decode_refresh_token(new_refresh_token)
        self._persist_refresh_token(session, user.user_id, new_refresh_payload)

    return {
      "status": "success",
      "message": "Token refreshed successfully",
      "auth_token": new_access_token,
      "refresh_token": new_refresh_token
    }

  def revoke_refresh_token(self, refresh_token):
    payload = decode_refresh_token(refresh_token)
    user_id = int(payload['sub'])
    incoming_jti = str(payload.get('jti', ''))
    if not incoming_jti:
      raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401)

    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        token_row = self._execute_query(
          session,
          db.select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.jti == incoming_jti
          )
        ).scalar_one_or_none()

        if token_row is not None and not token_row.revoked:
          token_row.revoked = True

    return {
      "status": "success",
      "message": "Logged out successfully"
    }

  def revoke_all_refresh_tokens(self, user_id):
    session_factory = self._session_factory or Session
    revoked_count = 0

    with session_factory(db.engine) as session:
      with session.begin():
        tokens = self._execute_query(
          session,
          db.select(RefreshToken).where(
            RefreshToken.user_id == int(user_id),
            RefreshToken.revoked.is_(False)
          )
        ).scalars().all()

        for token_row in tokens:
          token_row.revoked = True
          revoked_count += 1

    return {
      "status": "success",
      "message": "Logged out from all devices",
      "revoked_tokens": revoked_count
    }

  def delete(self, user_id):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = self._get_user_by_id(session, user_id)
        if not user:
          return None
        session.delete(user)
    return "successful"


user_service = UserService()
service_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=10)


def update_getter(user, new_password):
  key = make_key(user.key, user.password)
  rekeyed = make_key(user.key, new_password)
  audits = fal(key, user, rekeyed)
  passwords = fp(key, user, rekeyed)
  history = fph(key, user, rekeyed)
  questions = fsq(key, user, rekeyed)
  return [audits, passwords, history, questions]


@service_breaker
def save(user_data):
  return user_service.save(user_data)


@service_breaker
def update(user_data, user_id):
  return user_service.update(user_data, user_id)


def find_by_id(user_id):
  return user_service.find_by_id(user_id)


@service_breaker
def login_user(username, password):
  return user_service.login_user(username, password)


@service_breaker
def refresh_user_token(refresh_token):
  return user_service.refresh_user_token(refresh_token)


@service_breaker
def revoke_refresh_token(refresh_token):
  return user_service.revoke_refresh_token(refresh_token)


@service_breaker
def revoke_all_refresh_tokens(user_id):
  return user_service.revoke_all_refresh_tokens(user_id)


@service_breaker
def delete(user_id):
  return user_service.delete(user_id)
  
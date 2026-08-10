from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit  # type: ignore

from utils.circuitbreaker import protected_call
from caching import (
  LONG_CACHE_TIMEOUT,
  cached_result,
  build_cache_key,
  invalidate_cache,
)


def _clear_role_cache():
  invalidate_cache()

from models.role import Role
from models.user import User
from models.userManagement import UserManagementRole as UMR


class RoleService:
  """Encapsulates role-related business logic with injectable dependencies."""

  def __init__(self, session_factory=None):
    self._session_factory = session_factory

  def _execute_query(self, session, statement):
    target_session = session if session is not None else db.session
    execute = getattr(target_session, 'execute', None)

    if callable(execute):
      return execute(statement)

    raise TypeError("Session object must provide an execute() method")

  def save(self, role_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        role = self._execute_query(session, db.select(Role).where(Role.role_name == role_data['role_name'])).unique().scalar_one_or_none()

        if role is not None:
          raise ValueError("Role already In Database")

        new_role = Role(role_name=role_data['role_name'])

        session.add(new_role)
      session.refresh(new_role)
    invalidate_cache()
    return new_role

  def find(self, _user_id=None):
    cache_key = build_cache_key('role', 'list')
    return cached_result(cache_key, lambda: self._load_roles(), timeout=LONG_CACHE_TIMEOUT)

  def clear_cache(self):
    _clear_role_cache()

  def _load_roles(self):
    query = select(Role)
    roles = db.session.execute(query).scalars().all()
    return roles

  def update(self, _user_id, role_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        role = self._execute_query(session, db.select(Role).where(Role.role_id == role_data['role_id'])).unique().scalar_one_or_none()

        if role is None:
          raise ValueError("Role Not Found!")

        users = session.query(User).where(User.role == role.role_name).all()

        if users != []:
          for user in users:
            user.role = role_data['role_name']

        role.role_name = role_data['role_name']
      session.refresh(role)
    invalidate_cache()
    return role

  def delete(self, _user_id, role_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        role = self._execute_query(session, db.select(Role).where(Role.role_id == role_data['role_id'])).unique().scalar_one_or_none()

        if role is None:
          raise ValueError("Role Not Found!")

        if role.role_name in ['admin', 'user']:
          raise ValueError(f"Can not delete '{role.role_name}' role!")

        users = session.query(User).where(User.role == role.role_name).all()
        user_role = session.query(Role).where(Role.role_name == 'user').one_or_none()

        umr = self._execute_query(session, db.select(UMR).where(UMR.role_id == role.role_id)).scalars().all()

        for mng_role in umr:
          mng_role.role_id = user_role.role_id

        if users != []:
          for user in users:
            user.role = 'user'

        session.delete(role)
    invalidate_cache()
    return 'successful'


role_service = RoleService()


def fallback_function(*user):
  return None


@circuit(failure_threshold=1, recovery_timeout=10, fallback_function=fallback_function)
def save(role_data):
  return protected_call(role_service.save, role_data)


def find(user_id):
  return protected_call(role_service.find, user_id)


def update(user_id, role_data):
  return protected_call(role_service.update, user_id, role_data)


def delete(user_id, role_data):
  return protected_call(role_service.delete, user_id, role_data)
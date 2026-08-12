from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from services.passwordHistService import save as history_log, delete as hist_delete

from utils.utils import find_user, time
from utils.encryption import decrypted, encrypted, rekey_collection
from utils.circuitbreaker import CircuitBreaker
from caching import (
  DEFAULT_CACHE_TIMEOUT,
  SHORT_CACHE_TIMEOUT,
  cached_result,
  build_cache_key,
  invalidate_cache,
)

from models.folder import Folder
from models.passwords import Password


class PasswordService:
  """Encapsulates password business logic with injectable collaborators."""

  def __init__(self, session_factory=None, clock=None, history_logger=None, history_deleter=None):
    self._session_factory = session_factory
    self._clock = clock
    self._history_logger = history_logger
    self._history_deleter = history_deleter

  def hist_func(self, data):
    history_logger = self._history_logger if self._history_logger is not None else hist_func
    return history_logger(data)

  def save(self, user_id, password_data):
    session_factory = self._session_factory or Session
    clock = self._clock or time
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)

        if password_data['folder_id'] is not None:
          folder = session.execute(db.select(Folder).where(Folder.folder_id == password_data['folder_id'],
                                                Folder.user_id == user[0].user_id)).unique().scalar_one_or_none()

          if folder is None:
            raise ValueError('Folder not found!')

        stamp = clock()
        action = 'Create'
        details = f"'{user[0].username}' created a new saved password"
        encrypted_password = encrypted(user[1], password_data['encripted_password'])

        new_password = Password(
          folder_id=password_data['folder_id'],
          user_id=user[0].user_id,
          password_name=password_data['password_name'],
          username=password_data['username'],
          email=password_data['email'],
          encripted_password=encrypted_password,
          created_date=stamp,
          last_updated_date=stamp
        )

        session.add(new_password)
        session.flush()
        session.add(self.hist_func([new_password, stamp, details, action]))

      session.refresh(new_password)
    invalidate_cache()
    return new_password

  def find_passwords(self, user_id, limit=50, offset=0):
    user = find_user(user_id)
    cache_key = build_cache_key('password', 'list', user[0].user_id, limit, offset)

    return cached_result(cache_key, lambda: self._load_passwords(user, limit, offset), timeout=SHORT_CACHE_TIMEOUT)

  def _load_passwords(self, user, limit, offset):
    query = db.session.query(Password).filter(Password.user_id == user[0].user_id)
    if offset != 0 or limit != 50:
      password_data = query.order_by(Password.password_id).offset(offset).limit(limit).all()
    else:
      password_data = query.all()

    for password in password_data:
      password.encripted_password = decrypted(user[1], password.encripted_password)

    return password_data

  def find_password(self, user_id, name):
    user = find_user(user_id)
    cache_key = build_cache_key('password', 'single', user[0].user_id, name)

    return cached_result(cache_key, lambda: self._load_password(user, name), timeout=DEFAULT_CACHE_TIMEOUT)

  def _load_password(self, user, name):
    password_data = db.session.query(Password).filter(Password.user_id == user[0].user_id,
                                                      Password.password_name == name).one_or_none()

    if password_data is None:
      return None

    password_data.encripted_password = decrypted(user[1], password_data.encripted_password)

    return password_data

  def update(self, user_id, password_data):
    session_factory = self._session_factory or Session
    clock = self._clock or time
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)
        password = session.execute(db.select(Password).where(Password.password_id == password_data['password_id'],
                                                             Password.user_id == user[0].user_id)).unique().scalar_one_or_none()

        if password is None:
          raise ValueError('Invalid Password!')

        if password_data['folder_id'] is not None:
          folder = session.query(Folder).filter(Folder.folder_id == password_data['folder_id'],
                                                Folder.user_id == user[0].user_id).one_or_none()

          if folder is None:
            raise ValueError('Folder not found!')

        stamp = clock()
        check = decrypted(user[1], password.encripted_password)
        action = 'Update'
        details = f"'{user[0].username}' updated: password "

        if password.folder_id != password_data['folder_id']:
          password.folder_id = password_data['folder_id']
          details += 'folder, '

        if password.password_name != password_data['password_name']:
          password.password_name = password_data['password_name']
          details += 'password_name, '

        if password.username != password_data['username']:
          password.username = password_data['username']
          details += 'username, '

        if password.email != password_data['email']:
          password.email = password_data['email']
          details += 'email, '

        if check != password_data['encripted_password']:
          encrypted_password = encrypted(user[1], password_data['encripted_password'])
          password.encripted_password = encrypted_password
          details += 'ecripted_password'

        history = self.hist_func([password, stamp, details, action])
        session.add(history)

        password.last_updated_date = stamp

      session.refresh(password)
    invalidate_cache()
    return password

  def delete(self, user_id, password_data):
    history_deleter = self._history_deleter if self._history_deleter is not None else hist_delete
    history = history_deleter(user_id, password_data)

    if int(user_id) != password_data['user_id']:
      raise ValueError("Invalid User")

    if history != 'successful':
      return None

    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        password = session.execute(db.select(Password).where(Password.password_id == password_data['password_id'],
                                                             Password.user_id == int(user_id))).unique().scalar_one_or_none()

        if not password:
          return None

        session.delete(password)
    invalidate_cache()
    return 'successful'

  def finder(self, key, user, rekeyed, limit=50):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        passwords = session.execute(db.select(Password).where(Password.user_id == user.user_id).order_by(Password.password_id).limit(limit)).scalars().all()
        rekey_collection(passwords, key, rekeyed, 'encripted_password', limit=limit)
    return passwords


password_service = PasswordService()
service_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=10)


def hist_func(data):
  return history_log(data)


@service_breaker
def save(user_id, password_data):
  return password_service.save(user_id, password_data)


@service_breaker
def find_passwords(user_id, limit=50, offset=0):
  return password_service.find_passwords(user_id, limit=limit, offset=offset)


@service_breaker
def find_password(user_id, name):
  return password_service.find_password(user_id, name)


@service_breaker
def update(user_id, password_data):
  return password_service.update(user_id, password_data)


@service_breaker
def delete(user_id, password_data):
  return password_service.delete(user_id, password_data)


@service_breaker
def finder(key, user, rekeyed, limit=50):
  return password_service.finder(key, user, rekeyed, limit=limit)
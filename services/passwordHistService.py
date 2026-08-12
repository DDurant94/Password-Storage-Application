from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from utils.utils import find_user
from utils.encryption import decrypted, encrypted, decrypt, rekey_collection

from models.passwordHist import PasswordHistory


class PasswordHistoryService:
  """Encapsulates password-history business logic with injectable collaborators."""

  def __init__(self, session_factory=None):
    self._session_factory = session_factory

  def save(self, data):
    return PasswordHistory(
      user_id=data[0].user_id,
      action=data[3],
      details=data[2],
      password_id=data[0].password_id,
      password_name=data[0].password_name,
      username=data[0].username,
      email=data[0].email,
      old_encripted_password=data[0].encripted_password,
      changed_date=data[1]
    )

  def find_passwords_history(self, user_id, limit=50, offset=0):
    user = find_user(user_id)
    query = db.session.query(PasswordHistory).filter(PasswordHistory.user_id == user[0].user_id)
    if offset != 0 or limit != 50:
      result = query.order_by(PasswordHistory.password_id, PasswordHistory.changed_date).offset(offset).limit(limit).all()
    else:
      result = query.order_by(PasswordHistory.password_id, PasswordHistory.changed_date).all()
    return decrypt(user[1], result)

  def find_password_history(self, user_id, search_name, limit=50, offset=0):
    user = find_user(user_id)
    query = db.session.query(PasswordHistory).filter(PasswordHistory.user_id == user[0].user_id,
                                                     PasswordHistory.password_name == search_name)
    if offset != 0 or limit != 50:
      result = query.order_by(PasswordHistory.password_id, PasswordHistory.changed_date).offset(offset).limit(limit).all()
    else:
      result = query.order_by(PasswordHistory.password_id, PasswordHistory.changed_date).all()
    return decrypt(user[1], result)

  def delete(self, user_id, password_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)
        password_history = session.execute(db.select(PasswordHistory).where(PasswordHistory.password_id == password_data['password_id'],
                                                                            PasswordHistory.user_id == user[0].user_id)).scalars().all()
        if password_history == []:
          raise ValueError('No Password History!')

        for password in password_history:
          session.delete(password)
    return 'successful'

  def finder(self, key, user, rekeyed, limit=50):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        histories = session.execute(db.select(PasswordHistory).where(PasswordHistory.user_id == user.user_id).order_by(PasswordHistory.password_id, PasswordHistory.changed_date).limit(limit)).scalars().all()
        rekey_collection(histories, key, rekeyed, 'old_encripted_password', limit=limit)

    return histories


password_history_service = PasswordHistoryService()


def save(data):
  return password_history_service.save(data)


def find_passwords_history(user_id, limit=50, offset=0):
  return password_history_service.find_passwords_history(user_id, limit=limit, offset=offset)


def find_password_history(user_id, search_name, limit=50, offset=0):
  return password_history_service.find_password_history(user_id, search_name, limit=limit, offset=offset)


def delete(user_id, password_data):
  return password_history_service.delete(user_id, password_data)


def finder(key, user, rekeyed, limit=50):
  return password_history_service.finder(key, user, rekeyed, limit=limit)
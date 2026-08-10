from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from utils.utils import find_user, time
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


class FolderService:
  """Encapsulates folder business logic with injectable dependencies."""

  def __init__(self, session_factory=None, clock=None):
    self._session_factory = session_factory
    self._clock = clock

  def save(self, user_id, folder_data):
    session_factory = self._session_factory or Session
    clock = self._clock or time
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)
        folder = session.execute(db.select(Folder).where(Folder.folder_name == folder_data['folder_name'],
                                                         Folder.user_id == user[0].user_id)).scalar_one_or_none()

        if folder:
          raise ValueError("Folder name should be unique")

        if folder_data['parent_folder_id'] is not None:
          parent_folder = session.execute(db.select(Folder).where(Folder.folder_id == folder_data['parent_folder_id'],
                                                                  Folder.user_id == user[0].user_id)).scalar_one_or_none()

          if parent_folder is None:
            raise ValueError("Parent folder doesn't exist")

        new_folder = Folder(
          user_id=user[0].user_id,
          parent_folder_id=folder_data['parent_folder_id'],
          folder_name=folder_data['folder_name'],
          created_date=clock()
        )

        session.add(new_folder)

      session.refresh(new_folder)

    invalidate_cache()
    return new_folder

  def find_user_folders(self, user_id):
    user = find_user(user_id)
    cache_key = build_cache_key('folder', 'list', user[0].user_id)

    return cached_result(cache_key, lambda: self._load_user_folders(user), timeout=SHORT_CACHE_TIMEOUT)

  def _load_user_folders(self, user):
    folders = db.session.query(Folder).filter(Folder.user_id == user[0].user_id).order_by(Folder.parent_folder_id).all()

    if folders == []:
      return None

    return folders

  def update(self, user_id, folder_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)
        folder = session.execute(db.select(Folder).where(Folder.folder_id == folder_data['folder_id'],
                                                         Folder.user_id == user[0].user_id)).unique().scalar_one_or_none()

        if not folder:
          raise ValueError("Folder not found!")

        if folder_data['folder_name']:
          existing_folder = session.execute(db.select(Folder).where(Folder.folder_name == folder_data['folder_name'],
                                                                    Folder.user_id == user[0].user_id)).unique().scalar_one_or_none()

          if existing_folder and existing_folder.folder_id != folder.folder_id:
            raise ValueError("Folder name should be unique")

          folder.folder_name = folder_data['folder_name']

        if folder_data['parent_folder_id'] is not None:
          parent_folder = session.execute(db.select(Folder).where(Folder.folder_id == folder_data['parent_folder_id'],
                                                                  Folder.user_id == user[0].user_id)).unique().scalar_one_or_none()

          if parent_folder is None:
            raise ValueError("Parent folder doesn't exist")

          folder.parent_folder_id = folder_data['parent_folder_id']

        else:
          folder.parent_folder_id = None

        for child in folder.children_folders:
          child.parent_folder_id = folder.folder_id

      session.refresh(folder)

    invalidate_cache()
    return folder

  def delete(self, user_id, folder_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)
        folder = session.execute(db.select(Folder).where(Folder.folder_name == folder_data['folder_name'],
                                                Folder.user_id == user[0].user_id,
                                                Folder.folder_id == folder_data['folder_id'])).unique().scalar_one_or_none()

        if not folder:
          return None

        for child in list(folder.children_folders):
          child.parent_folder_id = folder.parent_folder_id

        linked_passwords = session.execute(db.select(Password).where(Password.folder_id == folder.folder_id,
                                                                    Password.user_id == user[0].user_id)).scalars().all()
        for password in linked_passwords:
          password.folder_id = None

        session.delete(folder)
    invalidate_cache()
    return "successful"


folder_service = FolderService()
service_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=10)


@service_breaker
def save(user_id, folder_data):
  return folder_service.save(user_id, folder_data)


@service_breaker
def find_user_folders(user_id):
  return folder_service.find_user_folders(user_id)


@service_breaker
def update(user_id, folder_data):
  return folder_service.update(user_id, folder_data)


@service_breaker
def delete(user_id, folder_data):
  return folder_service.delete(user_id, folder_data)
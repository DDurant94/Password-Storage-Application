from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column, backref
from sqlalchemy import ForeignKeyConstraint
from typing import List
import datetime


class Folder(Base):
  __tablename__ = "Folders"
  folder_id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'))
  parent_folder_id: Mapped[int] = mapped_column(db.ForeignKey('Folders.folder_id'),nullable=True)
  folder_name: Mapped[str] = mapped_column(db.String(255),nullable=True)
  created_date: Mapped[datetime.datetime] = mapped_column(db.DateTime,nullable=True, default=datetime.timezone.utc)
  
  user: Mapped['User'] = db.relationship(back_populates='folders')
  passwords: Mapped[List['Password']] = db.relationship(back_populates='folder')
  children_folders: Mapped[List["Folder"]] = db.relationship(backref=backref('parent',  
                                                                             remote_side = [folder_id],
                                                                             lazy="subquery"),
                                                             cascade="all, delete-orphan",
                                                             single_parent=True)
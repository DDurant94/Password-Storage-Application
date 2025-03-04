from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column
import datetime
from typing import List

class Password(Base):
  __tablename__ = "Passwords"
  password_id: Mapped[int] = mapped_column(primary_key=True)
  folder_id: Mapped[int] = mapped_column(db.ForeignKey('Folders.folder_id'),nullable=True)
  user_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'))
  password_name: Mapped[str] = mapped_column(db.String(255),nullable=True)
  username: Mapped[str] = mapped_column(db.String(255),nullable=True)
  email: Mapped[str] = mapped_column(db.String(100),nullable=False)
  encripted_password: Mapped[str] = mapped_column(db.String(255),nullable=False)
  created_date: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False)
  last_updated_date: Mapped[datetime.datetime] = mapped_column(db.DateTime,nullable=False, default=datetime.datetime.now())
   
  user: Mapped['User'] = db.relationship(back_populates='passwords')
  folder: Mapped['Folder'] = db.relationship(back_populates='passwords')
  password_histories: Mapped[List['PasswordHistory']] = db.relationship(back_populates='passwords')
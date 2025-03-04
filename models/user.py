from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column
from typing import List
import datetime

class User(Base):
  __tablename__ = "Users"
  user_id: Mapped[int] = mapped_column(primary_key=True)
  username: Mapped[str] = mapped_column(db.String(12),unique=True, nullable=False)
  password: Mapped[str] = mapped_column(db.String(257),nullable=False)
  first_name: Mapped[str] = mapped_column(db.String(30),nullable=False)
  last_name: Mapped[str] = mapped_column(db.String(30),nullable=False)
  email: Mapped[str] = mapped_column(db.String(100),nullable=False)
  create_date: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False)
  updated_date: Mapped[datetime.datetime] = mapped_column(db.DateTime,nullable=False, default=datetime.datetime.now())
  role: Mapped[str] = mapped_column(db.String(80), nullable=False)
  key: Mapped[bytes] = mapped_column(nullable=False)
  
  roles: Mapped[List['Role']] = db.relationship(secondary='User_Management_Roles', lazy='joined') 
  folders: Mapped[List['Folder']] = db.relationship('Folder',back_populates='user')
  audit_logs: Mapped[List['AuditLog']] = db.relationship( back_populates='user') 
  security_questions: Mapped[List['SecurityQuestion']] = db.relationship('SecurityQuestion', back_populates='user') 
  password_histories: Mapped[List['PasswordHistory']] = db.relationship(back_populates='user') 
  passwords: Mapped[List['Password']] = db.relationship(back_populates='user')
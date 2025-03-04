from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column
import datetime

class PasswordHistory(Base):
  __tablename__ = "Password_Histories"
  history_id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'))
  password_id: Mapped[int] = mapped_column(db.ForeignKey('Passwords.password_id'))
  password_name: Mapped[str] = mapped_column(db.String(255),nullable=True)
  username: Mapped[str] = mapped_column(db.String(255),nullable=True)
  email: Mapped[str] = mapped_column(db.String(100),nullable=False)
  old_encripted_password: Mapped[str] = mapped_column(db.String(255), nullable=False)
  changed_date: Mapped[datetime.datetime] = mapped_column(db.DateTime,nullable=False, default=datetime.timezone.utc)
  
  user: Mapped['User'] = db.relationship(back_populates='password_histories')
  passwords: Mapped['Password'] = db.relationship(back_populates='password_histories')
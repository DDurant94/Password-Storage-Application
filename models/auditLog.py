from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column
import datetime

class AuditLog(Base):
  __tablename__ = "Audit_Logs"
  audit_id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'))
  action: Mapped[str] = mapped_column(db.String(255), nullable=False)
  time_stamp: Mapped[datetime.datetime] = mapped_column(db.DateTime,nullable=False, default=datetime.timezone.utc)
  details: Mapped[str] = mapped_column(db.String(255),nullable=True)
  ip_address: Mapped[str] = mapped_column(db.String(257), nullable=False)

  user: Mapped['User'] = db.relationship(back_populates='audit_logs')
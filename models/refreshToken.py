from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column
import datetime


class RefreshToken(Base):
  __tablename__ = "Refresh_Tokens"
  refresh_token_id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'), nullable=False, index=True)
  jti: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
  expires_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False)
  revoked: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
  created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False, default=datetime.datetime.now)

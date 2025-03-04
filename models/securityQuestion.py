from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column

class SecurityQuestion(Base):
  __tablename__ = "Security_Questions"
  question_id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'))
  question: Mapped[str] =  mapped_column(db.String(255), nullable=False)
  encripted_answer: Mapped[str] = mapped_column(db.String(255), nullable=False)
  
  user: Mapped['User'] = db.relationship(back_populates = 'security_questions')
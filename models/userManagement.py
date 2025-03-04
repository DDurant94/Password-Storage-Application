from database import db, Base
from sqlalchemy.orm import Mapped, mapped_column

class UserManagementRole(Base):
  __tablename__ = "User_Management_Roles"
  user_management_role_id: Mapped[int] = mapped_column(primary_key=True)
  user_management_id: Mapped[int] = mapped_column(db.ForeignKey('Users.user_id'))
  role_id: Mapped[int] = mapped_column(db.ForeignKey('Roles.role_id'))
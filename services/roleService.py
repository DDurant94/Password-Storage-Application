from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from models.role import Role
from models.user import User
from models.userManagement import UserManagementRole as UMR

# Adding a new role to API
def save(role_data):
  with Session(db.engine) as session:
    with session.begin():
      role = session.execute(db.select(Role).where(Role.role_name == role_data['role_name'])).unique().scalar_one_or_none()
      
      if role:
        raise ValueError("Role already In Database")
      
      new_role = Role(role_name = role_data['role_name'])
      
      session.add(new_role)
      session.commit()
    session.refresh(new_role)
  return new_role

# finding all roles 
def find(user_id):
  roles = db.session.query(Role).all()
  return roles

def update(user_id,role_data):
  with Session(db.engine) as session:
    with session.begin():
      role = session.execute(db.select(Role).where(Role.role_id == role_data['role_id'])).unique().scalar_one_or_none()
      users = session.query(User).where(User.role == role.role_name).all()
      if role is None:
        raise ValueError("Role Not Found!")
      
      for user in users:
        user.role = role_data['role_name']
      
      role.role_name = role_data['role_name']
      
      session.commit()
    session.refresh(role)
  return role

def delete(user_id,role_data):
  with Session(db.engine) as session:
    with session.begin():
      role = session.execute(db.select(Role).where(Role.role_id == role_data['role_id'])).unique().scalar_one_or_none()
      users = session.query(User).where(User.role == role.role_name).all() 
      user_role = session.query(Role).where(Role.role_name == 'user').one_or_none()
      
      if role is None:
        raise ValueError("Role Not Found!")
      
      if role.role_name in ['admin','user']:
        raise ValueError(f"Can not delete '{role.role_name}' role!")
      
      umr = session.execute(db.select(UMR).where(UMR.role_id == role.role_id)).scalars().all()
      
      for mng_role in umr:
        mng_role.role_id = user_role.role_id
      
      if users != []:
        for user in users:
          user.role = 'user'
        
      session.delete(role)
      session.commit()
  return 'successful'
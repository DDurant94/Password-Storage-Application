from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit

from services.passwordHistService import save as history_log, delete as hist_delete

from utils.util import decrypted,encrypted,find_user,make_key, time

from models.folder import Folder
from models.passwords import Password

##
###
#### HELPER FUNCS
###
##

# adding password data to history
def password_hist_func(password_data,time):
  log = history_log(password_data,time)
  return log

##
###
#### MAIN FUNCS
###
##

# think about getting that users password and validating it like the rest of the get user
# adding password
def save(user_id,password_data):
  with Session(db.engine) as session:
    with session.begin():
      user = find_user(user_id)
      if password_data['folder_id'] is not None:
        folder = session.execute(db.select(Folder).where(Folder.folder_id == password_data['folder_id'],
                                              Folder.user_id == user[0].user_id)).unique().scalar_one_or_none()
        
        if folder is None:
          raise ValueError('Folder not found!')
        
      encrypted_password = encrypted(user[1],password_data['encripted_password'])
      
      new_password = Password(
        folder_id = password_data['folder_id'],
        user_id = user[0].user_id,
        password_name = password_data['password_name'],
        username = password_data['username'],
        email = password_data['email'],
        encripted_password = encrypted_password,
        created_date = time(),
        last_updated_date = time()
      )
      
      session.add(new_password)
      session.flush()
      session.add(password_hist_func(new_password,time()))
      session.commit()
      
    session.refresh(new_password)
  return new_password

# get all passwords
def find_passwords(user_id):
  user = find_user(user_id)

  password_data = db.session.query(Password).filter(Password.user_id == user[0].user_id).all()
  
  for password in password_data:
      password.encripted_password = decrypted(user[1],password.encripted_password)
  
  return password_data

# get one password
def find_password(user_id, name):
  user = find_user(user_id)
  
  password_data = db.session.query(Password).filter(Password.user_id == user[0].user_id,
                                                    Password.password_name == name).one_or_none()
  
  if password_data is None:
    return None
  
  password_data.encripted_password = decrypted(user[1],password_data.encripted_password)
  
  return password_data

# update password
def update(user_id,password_data):
  try:
    with Session(db.engine) as session:
      with session.begin():        
        user = find_user(user_id)
        password = session.execute(db.select(Password).where(Password.password_id == password_data['password_id'], 
                                                             Password.user_id == user[0].user_id)).unique().scalar_one_or_none()
        
        if password is None:
          raise ValueError('Invalid Password!')
        
        if password_data['folder_id'] is not None:
          folder = session.query(Folder).filter(Folder.folder_id == password_data['folder_id'],
                                              Folder.user_id == user[0].user_id).one_or_none()
        
          if folder is None:
            raise ValueError('Folder not found!')       
        
        encrypted_password = encrypted(user[1],password_data['encripted_password'])
        
        password.folder_id = password_data['folder_id']
        password.password_name = password_data['password_name']
        password.username = password_data['username']
        password.email = password_data['email']
        password.encripted_password = encrypted_password
        password.last_updated_date = time()
        
        session.add(password_hist_func(password,time()))
    
        session.commit()
        
      session.refresh(password)
    return password
  except Exception as e:
    raise e 

# delete password
def delete(user_id,password_data):
  history = hist_delete(user_id,password_data)
  
  if int(user_id) != password_data['user_id']:
    raise ValueError("Invalid User")
  
  if history != 'successful':
    return None
  
  with Session(db.engine) as session:
    with session.begin():
      
      password = session.execute(db.select(Password).where(Password.password_id == password_data['password_id'],
                                                           Password.user_id == int(user_id))).unique().scalar_one_or_none()
      
      if not password:
        return None
      
      session.delete(password)
      session.commit()
  return 'successful'

def finder(key,user,rekeyed):
  with Session(db.engine) as session:
    with session.begin():
      passwords = session.execute(db.select(Password).where(Password.user_id == user.user_id,)).scalars().all()
      
      if passwords != []:
        for password in passwords:
          password.encripted_password = decrypted(key,password.encripted_password)
          password.encripted_password = encrypted(rekeyed,password.encripted_password)
          
      session.commit()
  return passwords
from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit

from services.passwordHistService import save as history_log, delete as hist_delete

from utils.utils import decrypted, encrypted, find_user, time

from models.folder import Folder
from models.passwords import Password

##
###
#### HELPER FUNCS
###
##

# Adding Password data to history
def hist_func(data):
  log = history_log(data)
  return log

##
###
#### MAIN FUNCS
###
##

# Adding password
def save(user_id,password_data):
  with Session(db.engine) as session:
    with session.begin():
      user = find_user(user_id)
      
      if password_data['folder_id'] is not None:
        folder = session.execute(db.select(Folder).where(Folder.folder_id == password_data['folder_id'],
                                              Folder.user_id == user[0].user_id)).unique().scalar_one_or_none()
        
        if folder is None:
          raise ValueError('Folder not found!')
        
      stamp = time()
      action = 'Create'
      details = f"'{user[0].username}' created a new saved password"
      encrypted_password = encrypted(user[1],password_data['encripted_password'])
      
      new_password = Password(
        folder_id = password_data['folder_id'],
        user_id = user[0].user_id,
        password_name = password_data['password_name'],
        username = password_data['username'],
        email = password_data['email'],
        encripted_password = encrypted_password,
        created_date = stamp,
        last_updated_date = stamp
      )
      
      session.add(new_password)
      session.flush()
      session.add(hist_func([new_password,stamp,details,action]))
      session.commit()
      
    session.refresh(new_password)
  return new_password

# Get all passwords 
def find_passwords(user_id):
  user = find_user(user_id)

  password_data = db.session.query(Password).filter(Password.user_id == user[0].user_id).all()
  
  for password in password_data:
      password.encripted_password = decrypted(user[1],password.encripted_password)
  
  return password_data

# Get one password
def find_password(user_id, name):
  user = find_user(user_id)
  
  password_data = db.session.query(Password).filter(Password.user_id == user[0].user_id,
                                                    Password.password_name == name).one_or_none()
  
  if password_data is None:
    return None
  
  password_data.encripted_password = decrypted(user[1],password_data.encripted_password)
  
  return password_data

# Update password
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
        
        stamp = time()
        check = decrypted(user[1],password.encripted_password)
        action = 'Update'
        details = f"'{user[0].username}' updated: password "
        
        if password.folder_id != password_data['folder_id']:
          password.folder_id = password_data['folder_id']
          details += 'folder, '
          
        if password.password_name != password_data['password_name']:
          password.password_name = password_data['password_name']
          details += 'password_name, '
          
        if password.username != password_data['username']:
          password.username = password_data['username']
          details += 'username, '
          
        if password.email != password_data['email']:
          password.email = password_data['email']
          details += 'email, '
      
        if check != password_data['encripted_password']:
          encrypted_password = encrypted(user[1],password_data['encripted_password'])
          password.encripted_password = encrypted_password
          details += 'ecripted_password'
          
        history = hist_func([password,stamp,details,action])
        session.add(history)

        password.last_updated_date = stamp
        
        session.commit()
        
      session.refresh(password)
    return password
  except Exception as e:
    raise e 

# Delete password
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

# Rekeying password func
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
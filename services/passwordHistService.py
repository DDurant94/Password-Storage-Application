from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from utils.utils import find_user, decript, decrypted, encrypted

from models.passwordHist import PasswordHistory
from models.user import User

##
###
#### MAIN FUNCS
###
##

#  Add password history as adding a password or updating it
def save(data):
  history_log = PasswordHistory(
  user_id = data[0].user_id,
  action = data[3],
  details = data[2],
  password_id = data[0].password_id,
  password_name = data[0].password_name,
  username = data[0].username,
  email = data[0].email,
  old_encripted_password = data[0].encripted_password,
  changed_date = data[1])
  
  return  history_log

# Find all password history by users I.D.
def find_passwords_history(user_id):
  user = find_user(user_id)
  query = db.session.query(PasswordHistory).filter(PasswordHistory.user_id == user[0].user_id).order_by(PasswordHistory.password_id,
                                                                                                     PasswordHistory.changed_date).all()
  all_history = decript(user[1],query)
  return all_history

# Find all history by search name and user I.D.
def find_password_history(user_id,search_name):
  user = find_user(user_id)
  query = db.session.query(PasswordHistory).filter(PasswordHistory.user_id == user[0].user_id,
                                                   PasswordHistory.password_name == search_name).order_by(PasswordHistory.password_id,
                                                                                                          PasswordHistory.changed_date).all()
  history = decript(user[1],query)
  return history

# Deleteing password history as deleteing password
def delete(user_id,password_data):
  with Session(db.engine) as session:
    with session.begin():
      user = find_user(user_id)
      password_history = session.execute(db.select(PasswordHistory).where(PasswordHistory.password_id == password_data['password_id'],
                                                                          PasswordHistory.user_id == user[0].user_id)).scalars().all()
      if password_history == []:
        raise ValueError('No Password History!')
      
      for password in password_history:
        session.delete(password)
        
      session.commit()
  return 'successful'

# Rekeying password history func
def finder(key,user,rekeyed):
  with Session(db.engine) as session:
    with session.begin():
      histories = session.execute(db.select(PasswordHistory).where(PasswordHistory.user_id == user.user_id,)).scalars().all()
      if histories != []:
        for history in histories:
          history.old_encripted_password = decrypted(key, history.old_encripted_password)
          history.old_encripted_password = encrypted(rekeyed, history.old_encripted_password)
      session.commit()
      
  return histories
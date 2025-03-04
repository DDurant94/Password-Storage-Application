from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from utils.util import find_user,make_key,decript

from models.passwordHist import PasswordHistory
from models.user import User

##
###
#### MAIN FUNCS
###
##

#  add password history as adding a password or updating it
def save(password_data,time):
  history_log = PasswordHistory(
  user_id = password_data.user_id,
  password_id = password_data.password_id,
  password_name = password_data.password_name,
  username = password_data.username,
  email = password_data.email,
  old_encripted_password = password_data.encripted_password,
  changed_date = time)
  
  return  history_log

# find all password history by users I.D.
def find_passwords_history(user_id):
  user = find_user(user_id)
  query = db.session.query(PasswordHistory).filter(PasswordHistory.user_id == user[0].user_id).order_by(PasswordHistory.password_id,
                                                                                                     PasswordHistory.changed_date).all()
  all_history = decript(user[1],query)
  return all_history

# find all history by search name and user I.D.
def find_password_history(user_id,search_name):
  user = find_user(user_id)
  query = db.session.query(PasswordHistory).filter(PasswordHistory.user_id == user[0].user_id,
                                                   PasswordHistory.password_name == search_name).order_by(PasswordHistory.password_id,
                                                                                                          PasswordHistory.changed_date).all()
  history = decript(user[1],query)
  return history

# deleteing password history as deleteing password
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
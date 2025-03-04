from database import db

from flask import request
from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit

from utils.util import time, find_user, encrypted, decrypted, make_key

from models.auditLog import AuditLog


##
###
#### MAIN FUNCS
###
##

# Adding a new audit log
def save(user_data,action,detail):
  key = make_key(user_data)
  
  encrypted_ip = encrypted(key,request.remote_addr)
  
  audit_log = AuditLog(
    user_id = user_data.user_id,
    action = action,
    time_stamp = time(),
    details = detail,
    ip_address = encrypted_ip
  )
  
  return audit_log

# getting a users audit log
def find(user_id):
  user = find_user(user_id)
  query = db.session.query(AuditLog).filter(AuditLog.user_id == user[0].user_id).all()
  
  for log in query:
    log.ip_address = decrypted(user[1], log.ip_address)
  
  return query
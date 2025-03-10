from database import db

from flask import request
from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit

from utils.utils import time, find_user, encrypted, decrypted, make_key

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

# Getting a users audit log
def find(user_id):
  user = find_user(user_id)
  query = db.session.query(AuditLog).filter(AuditLog.user_id == user[0].user_id).all()
  
  for log in query:
    log.ip_address = decrypted(user[1], log.ip_address)
  
  return query

# Rekeying audit log func
def finder(key,user,rekeyed):
  with Session(db.engine) as session:
    with session.begin():
      audits = session.execute(db.select(AuditLog).where(AuditLog.user_id == user.user_id,)).scalars().all()
      if audits != []:
        for log in audits:
          log.ip_address = decrypted(key, log.ip_address)
          log.ip_address = encrypted(rekeyed,log.ip_address)
      session.commit()
  return audits  
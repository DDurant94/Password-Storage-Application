from database import db

from flask import request,jsonify
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta,timezone
import jwt
import uuid
import base64
import os

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.fernet import Fernet
import hmac
import hashlib

from models.user import User

##
###
#### Make Tokens
###
##

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
SECOND_KEY = os.getenv('SECOND_KEY')

def time():
  return datetime.now()

def salt_maker():
  return os.urandom(16)

def encode_token(user_id, role_names):
  try:
    now = datetime.now(timezone.utc)
    payload = {
      'exp': (now + timedelta(hours=1)),
      'iat': now,
      "jti": str(uuid.uuid4()),
      'sub': str(user_id),
      'roles': role_names
      # 'aud': '127.0.0.1:5000' (adding this in once we are up and running)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token
  
  except Exception as e:
    print(f"Error encoding token: {e}")
    return e

def token_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = None
    if 'Authorization' in request.headers:
      try:
        token = request.headers['Authorization'].split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('sub')  # Extract the user ID from the token
        kwargs['user_id'] = user_id
      except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired', 'error': 'Unauthorized'}), 401     
      except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token', 'error': 'Unauthorized'}), 401
    if not token:
      return jsonify({'message': 'Token is missing', 'error': 'Unauthorized'}), 401
    return f(*args, **kwargs)
  
  return decorated

def role_required(role):
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      token = request.headers.get('Authorization', '').split(" ")[1]
      
      if not token:
        return jsonify({'message': 'Token is missing'}), 401
      
      try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
      except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
      
      except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
      
      roles = payload.get('roles', [])
      if role not in roles:
        return jsonify({'message': 'User does not have the required role'}), 403
      
      return f(*args, **kwargs)
    
    return decorated_function
  
  return decorator
  

##
###
#### Helpers
###
##


##
### Encode Passwords
##

def derive_key(password,salt=None):
  if salt is None:
    salt = salt_maker()
  
  kdf = Argon2id(salt=salt,
               length=32,
               iterations=16,
               lanes=4,
               memory_cost=64 * 1024,
               ad=None,
               secret=None)
  key = kdf.derive(password.encode())
  return key, salt

def make_cipher(key):
  return Fernet(base64.urlsafe_b64encode(key))
  
def encrypted(key,data):
  cipher = make_cipher(key)
  encrypted_data = cipher.encrypt(data.encode())
  return encrypted_data

def decrypted(key,data):
  cipher = make_cipher(key)
  try:
    decrypted_data = cipher.decrypt(data).decode()
    return decrypted_data
  except Exception as e:
    raise ValueError(f'Decryption failed: {e}')
  
def make_key(user_data):
  salt = user_data.key
  data_hash = f"{SECRET_KEY}{user_data.password}{SECOND_KEY}".encode()
  secure_hash = hmac.new(SECRET_KEY.encode(),data_hash,hashlib.sha256).digest()
  key, _ = derive_key(secure_hash.hex(), salt)
  return key

def rekey(user_data,new):
  salt = user_data.key
  data_hash = f"{SECRET_KEY}{new}{SECOND_KEY}".encode()
  secure_hash = hmac.new(SECRET_KEY.encode(),data_hash,hashlib.sha256).digest()
  key, _ = derive_key(secure_hash.hex(), salt)
  return key

# decripting passwords
def decript(key,data):
  for password in data:
    password.old_encripted_password = decrypted(key,password.old_encripted_password)
  return data  

##
### General Helpers
##

# Get a user by I.D.
def find_user(user_id):
  user = db.session.query(User).where(User.user_id == int(user_id)).one_or_none()
  if user is None:
    raise ValueError('User not found!')

  key = make_key(user)
  return [user,key]
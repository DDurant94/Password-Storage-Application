from database import db

from flask import request, jsonify
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
import uuid
import base64
import os

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.fernet import Fernet
import hmac
import hashlib

from models.user import User

from utils.encryption_utils import make_key
from utils.error_handlers import ApiError

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
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

  except Exception as e:
    print(f"Error encoding token: {e}")
    raise ApiError("Unable to encode authentication token", status_code=500)


def _get_bearer_token():
  authorization_header = request.headers.get('Authorization', '')
  if not authorization_header.startswith('Bearer '):
    raise ApiError("Token is missing", status_code=401)

  return authorization_header.split(" ", 1)[1]


def _decode_token(token):
  try:
    return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  except jwt.ExpiredSignatureError as exc:
    raise ApiError("Token has expired", status_code=401) from exc
  except jwt.InvalidTokenError as exc:
    raise ApiError("Invalid token", status_code=401) from exc


def token_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = _get_bearer_token()
    payload = _decode_token(token)
    kwargs['user_id'] = payload.get('sub')
    return f(*args, **kwargs)

  return decorated


def role_required(role):
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      token = _get_bearer_token()
      payload = _decode_token(token)

      roles = payload.get('roles', [])
      if role not in roles:
        raise ApiError("User does not have the required role", status_code=403)

      return f(*args, **kwargs)

    return decorated_function

  return decorator
  

##
### General Helpers
##

# Get a user by I.D.
def find_user(user_id):
  user = db.session.query(User).where(User.user_id == int(user_id)).one_or_none()
  if user is None:
    raise ValueError('User not found!')

  key = make_key(user.key,user.password)
  return [user,key]
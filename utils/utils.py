from database import db

from flask import request, g
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
import uuid
import os

from models.user import User

from utils.encryption import make_key
from utils.errorHandlers import ApiError

##
###
#### Make Tokens
###
##

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key'
SECOND_KEY = os.getenv('SECOND_KEY') or 'dev-second-key'
INVALID_TOKEN_MESSAGE = "Invalid token"
ACCESS_TOKEN_TYPE = 'access'
REFRESH_TOKEN_TYPE = 'refresh'


def _require_secret_key():
  if not SECRET_KEY:
    raise ApiError("Server authentication is not configured", status_code=500)

def time():
  return datetime.now()

def salt_maker():
  return os.urandom(16)

def encode_token(user_id, role_names):
  _require_secret_key()
  try:
    now = datetime.now(timezone.utc)
    payload = {
      'exp': (now + timedelta(hours=1)),
      'iat': now,
      "jti": str(uuid.uuid4()),
      'sub': str(user_id),
      'type': ACCESS_TOKEN_TYPE,
      'roles': role_names
      # 'aud': '127.0.0.1:5000' (adding this in once we are up and running)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

  except Exception as _:
    raise ApiError("Unable to encode authentication token", status_code=500)


def encode_refresh_token(user_id):
  _require_secret_key()
  try:
    now = datetime.now(timezone.utc)
    payload = {
      'exp': (now + timedelta(days=7)),
      'iat': now,
      "jti": str(uuid.uuid4()),
      'sub': str(user_id),
      'type': REFRESH_TOKEN_TYPE
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

  except Exception as _:
    raise ApiError("Unable to encode refresh token", status_code=500)


def _get_bearer_token():
  authorization_header = request.headers.get('Authorization', '')
  if not authorization_header.startswith('Bearer '):
    raise ApiError("Token is missing", status_code=401)

  return authorization_header.split(" ", 1)[1]


def _decode_token(token):
  _require_secret_key()
  try:
    return jwt.decode(
      token,
      SECRET_KEY,
      algorithms=['HS256'],
      options={'require': ['exp', 'iat', 'sub']}
    )
  except jwt.ExpiredSignatureError as exc:
    raise ApiError("Token has expired", status_code=401) from exc
  except jwt.MissingRequiredClaimError as exc:
    raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401) from exc
  except jwt.InvalidTokenError as exc:
    raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401) from exc


def decode_refresh_token(token):
  payload = _decode_token(token)
  if payload.get('type') != REFRESH_TOKEN_TYPE:
    raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401)
  return payload


def _extract_user_id(payload):
  user_id = payload.get('sub')
  try:
    return int(user_id)
  except (TypeError, ValueError) as exc:
    raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401) from exc


def token_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = _get_bearer_token()
    payload = _decode_token(token)
    if payload.get('type') != ACCESS_TOKEN_TYPE:
      raise ApiError(INVALID_TOKEN_MESSAGE, status_code=401)
    authenticated_user_id = _extract_user_id(payload)
    g.auth_payload = payload
    kwargs['user_id'] = authenticated_user_id
    return f(*args, **kwargs)

  return decorated


def role_required(role):
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      payload = getattr(g, 'auth_payload', None)
      if payload is None:
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
from flask import request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter = Limiter(key_func=get_remote_address, storage_uri='memory://')


def build_limit_key():
  payload = request.get_json(silent=True) or {}
  username = payload.get('username')
  if username:
    return f"login:{username}"

  if getattr(g, 'auth_user_id', None) is not None:
    return f"user:{g.auth_user_id}"

  return f"ip:{get_remote_address()}"

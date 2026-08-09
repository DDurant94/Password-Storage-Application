from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash

from utils.utils import encode_token, time, salt_maker as salt, find_user, make_key

from services.auditLogService import save as audit_log, finder as fal
from services.passwordService import finder as fp
from services.passwordHistService import finder as fph
from services.securityQuestionService import finder as fsq

from models.user import User
from models.role import Role
from models.userManagement import UserManagementRole as UMR 


def _non_business_failure(exc_type, _):
  """Treat non-ValueError exceptions as circuit-breaker failures."""
  return not issubclass(exc_type, ValueError)

##
###
#### Helper Functions
###
##

# Fallback function incase of an error
def fallback_function(*user):
  return None


def update_getter(user, new_password):
  key = make_key(user.key, user.password)
  rekeyed = make_key(user.key, new_password)
  audits = fal(key, user, rekeyed)
  passwords = fp(key, user, rekeyed)
  history = fph(key, user, rekeyed)
  questions = fsq(key, user, rekeyed)
  return [audits, passwords, history, questions]


def _execute_query(session, statement):
  if session is not None and hasattr(session, 'execute'):
    return session.execute(statement)

  return db.session.execute(statement)


def _get_user_by_username(session, username):
  return _execute_query(session, db.select(User).where(User.username == username)).unique().scalar_one_or_none()


def _get_user_by_id(session, user_id):
  return _execute_query(session, db.select(User).where(User.user_id == int(user_id))).unique().scalar_one_or_none()


def _get_role_by_name(session, role_name):
  return _execute_query(session, db.select(Role).where(Role.role_name == role_name)).scalar_one_or_none()

##
###
#### MAIN FUNCS
###
##

# Adding a new user
@circuit(
  failure_threshold=1,
  recovery_timeout=10,
  expected_exception=_non_business_failure,
  fallback_function=fallback_function
)
def save(user_data):
  if user_data['username'] == "Failure":
    raise Exception("Failure condition triggered")

  with Session(db.engine) as session:
    with session.begin():
      user = _get_user_by_username(session, user_data['username'])

      if user:
        raise ValueError("User Already Exists!")

      user_role = user_data.get('role', 'user')
      savepoint = session.begin_nested()

      new_user = User(username=user_data['username'],
                      password=generate_password_hash(user_data['password']),
                      first_name=user_data['first_name'],
                      last_name=user_data['last_name'],
                      email=user_data['email'],
                      create_date=time(),
                      updated_date=time(),
                      role=user_role,
                      key=salt())
      session.add(new_user)
      session.flush()

      role = _get_role_by_name(session, new_user.role)

      if role is not None:
        session.add(UMR(user_management_id=new_user.user_id, role_id=role.role_id))
        session.add(audit_log(new_user, "Creation", "Creating User Account"))
      else:
        savepoint.rollback()
        raise ValueError("Role Not Found! Add Role or Change Role")

      session.commit()
    session.refresh(new_user)
  return new_user

# Finding user
def find_by_id(user_id):
  user = find_user(user_id)
  return user[0]

# Updating user account
@circuit(
  failure_threshold=1,
  recovery_timeout=10,
  expected_exception=_non_business_failure,
  fallback_function=fallback_function
)
def update(user_data, user_id):
  with Session(db.engine) as session:
    with session.begin():
      user = _get_user_by_id(session, user_id)

      if user is None:
        raise ValueError("User not Found!")

      details = f"'{user.username}' updated "

      if user.first_name != user_data['first_name']:
        user.first_name = user_data['first_name']
        details += 'first name, '

      if user.last_name != user_data['last_name']:
        user.last_name = user_data['last_name']
        details += 'last name, '

      if user.email != user_data['email']:
        user.email = user_data['email']
        details += 'email, '

      if not check_password_hash(user.password, user_data['password']):
        new_password = generate_password_hash(user_data['password'])
        update_getter(user, new_password)
        user.password = new_password
        details += 'password '

      user.updated_date = time()

      audit = audit_log(user, 'Update', details)
      session.add(audit)

      session.commit()
    session.refresh(user)
  return user

# Log user into account
def login_user(username, password):
  with Session(db.engine) as session:
    with session.begin():
      login_outcome = [None, 'success']
      user = _get_user_by_username(session, username)
      if user:
        detail = f"'{user.username}' "
        if check_password_hash(user.password, password):
          role_names = [role.role_name for role in user.roles]
          auth_token = encode_token(user.user_id, role_names)
          resp = {
            "status": "success",
            "message": "Successfully logged in",
            "auth_token": auth_token
          }

          login_outcome[0] = resp
          detail += 'Successfully logged in'

        else:
          login_outcome[1] = 'Password'
          detail += 'Failed login Password'

        audit = audit_log(user, "Login", detail)

        session.add(audit)
        session.commit()

      else:
        login_outcome[1] = 'Username'
    session.refresh(user)
  return login_outcome

# Delete user 
def delete(user_id):
  with Session(db.engine) as session:
    with session.begin():
      user = _get_user_by_id(session, user_id)
      if not user:
        return None
      session.delete(user)
    session.commit()
  return "successful"
  
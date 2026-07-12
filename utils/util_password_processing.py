# This is going to be for encapsulation of code for password processing encrypting and decrypting

# To Do
# - Make a single entry point for password processes
# - Pass an observer to watch for the process
# - Give the information that we either want to add or update. Generating a new salt and blob for the password
# - Pass the only want is need to the function to see and nothing more. Allowing for other functions to handle only what the need.
# - Make sure that if the anything fails along the way that it doesn't insert the information causing the system to not normalize

import base64

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.fernet import Fernet
import hmac
import hashlib


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
  
def make_key(key,password):
  salt = key
  data_hash = f"{SECRET_KEY}{password}{SECOND_KEY}".encode()
  secure_hash = hmac.new(SECRET_KEY.encode(),data_hash,hashlib.sha256).digest()
  key, _ = derive_key(secure_hash.hex(), salt)
  return key
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
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key'
SECOND_KEY = os.getenv('SECOND_KEY') or 'dev-second-key'


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
  if not isinstance(key, (bytes, bytearray)):
    raise TypeError("Encryption key must be bytes")

  normalized_key = bytes(key)
  if len(normalized_key) != 32:
    raise ValueError("Encryption key must be 32 bytes")

  return Fernet(base64.urlsafe_b64encode(normalized_key))
  
def encrypted(key,data):
  if not isinstance(data, str):
    raise TypeError("Encryption payload must be a string")

  cipher = make_cipher(key)
  encrypted_data = cipher.encrypt(data.encode())
  return encrypted_data

def decrypted(key,data):
  if isinstance(data, str):
    return data

  if not isinstance(data, (bytes, bytearray)):
    raise TypeError("Encrypted payload must be bytes")

  cipher = make_cipher(key)
  try:
    decrypted_data = cipher.decrypt(data).decode()
    return decrypted_data
  except Exception as e:
    raise ValueError(f'Decryption failed: {e}')
  
def make_key(key,password):
  salt = key
  data_hash = f"{SECRET_KEY}{password}{SECOND_KEY}".encode()
  secure_hash = hmac.new(SECRET_KEY.encode(), data_hash, hashlib.sha256).digest()
  key, _ = derive_key(secure_hash.hex(), salt)
  return key

# decrypting passwords
def decrypt(key,data):
  for password in data:
    password.old_encripted_password = decrypted(key,password.old_encripted_password)
  return data


def rekey_value(ciphertext, key, rekeyed):
  decrypted_value = decrypted(key, ciphertext)
  return encrypted(rekeyed, decrypted_value)


def rekey_collection(records, key, rekeyed, attribute_name, limit=None):
  if not records:
    return records

  staged_updates = []
  processed = 0

  for record in records:
    if not hasattr(record, attribute_name):
      raise ValueError(f"Record is missing required attribute: {attribute_name}")

    current_value = getattr(record, attribute_name)
    staged_updates.append((record, rekey_value(current_value, key, rekeyed)))
    processed += 1

    if limit is not None and processed >= limit:
      break

  for record, rekeyed_value in staged_updates:
    setattr(record, attribute_name, rekeyed_value)

  return records
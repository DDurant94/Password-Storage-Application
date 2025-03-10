import secrets
import string

# Generate a password that is length of 16
def password_gen():
  alphabet = string.ascii_letters
  digits = string.digits
  special_chars = string.punctuation
  all_chars = alphabet + digits + special_chars
  
  base = [
      secrets.choice(string.ascii_lowercase),
      secrets.choice(string.ascii_uppercase),
      secrets.choice(digits),
      secrets.choice(special_chars)
  ]
  
  base += [secrets.choice(all_chars) for _ in range(16 - 4)]
  secrets.SystemRandom().shuffle(base)
  password = ''.join(base)
  return password

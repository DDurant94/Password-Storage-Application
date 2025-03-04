from flask_limiter import Limiter
from  flask_limiter.util import get_remote_address

# creating limiter object
limiter = Limiter(key_func=get_remote_address)
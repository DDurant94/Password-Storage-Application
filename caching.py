import time

DEFAULT_CACHE_TIMEOUT = 30
SHORT_CACHE_TIMEOUT = 15
LONG_CACHE_TIMEOUT = 60


class MemoryCache:
  def __init__(self):
    self._store = {}

  def init_app(self, app):
    self.app = app
    return self

  def get(self, key):
    entry = self._store.get(key)
    if entry is None:
      return None

    expires_at, value = entry
    if expires_at is not None and time.time() >= expires_at:
      self._store.pop(key, None)
      return None

    return value

  def set(self, key, value, timeout=None):
    expires_at = None if timeout is None else time.time() + timeout
    self._store[key] = (expires_at, value)
    return True

  def delete(self, key):
    self._store.pop(key, None)
    return True

  def clear(self):
    self._store.clear()
    return True


cache = MemoryCache()


def build_cache_key(namespace, action, *parts):
  key_parts = [namespace, action, *[str(part) for part in parts if part is not None]]
  return ':'.join(key_parts)


def benchmark_cache(factory, iterations=100):
  start = time.time()
  for _ in range(iterations):
    factory()
  return time.time() - start


def invalidate_cache():
  cache.clear()


def cached_result(cache_key, factory, timeout=LONG_CACHE_TIMEOUT):
  cached_value = cache.get(cache_key)
  if cached_value is not None:
    return cached_value

  value = factory()
  cache.set(cache_key, value, timeout=timeout)
  return value
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
  sys.path.insert(0, str(ROOT_DIR))

import caching as caching_module

DEFAULT_CACHE_TIMEOUT = caching_module.DEFAULT_CACHE_TIMEOUT
LONG_CACHE_TIMEOUT = caching_module.LONG_CACHE_TIMEOUT
SHORT_CACHE_TIMEOUT = caching_module.SHORT_CACHE_TIMEOUT
build_cache_key = caching_module.build_cache_key
cached_result = caching_module.cached_result
cache = caching_module.cache


"""Caching Tests"""

class TestCachingHelper(unittest.TestCase):

  def setUp(self):
    cache.clear()

  def test_cached_result_reuses_callback_value(self):
    calls = []

    def factory():
      calls.append('called')
      return {'value': 1}

    first = cached_result('demo:key', factory, timeout=30)
    second = cached_result('demo:key', factory, timeout=30)

    self.assertEqual(first, {'value': 1})
    self.assertEqual(second, {'value': 1})
    self.assertEqual(calls, ['called'])

  def test_cache_ttl_defaults_are_configured(self):
    self.assertEqual(DEFAULT_CACHE_TIMEOUT, 30)
    self.assertEqual(SHORT_CACHE_TIMEOUT, 15)
    self.assertEqual(LONG_CACHE_TIMEOUT, 60)

  def test_user_scoped_cache_keys_are_distinct(self):
    first = build_cache_key('password', 'list', 'user-1', 10, 0)
    second = build_cache_key('password', 'list', 'user-2', 10, 0)

    self.assertNotEqual(first, second)

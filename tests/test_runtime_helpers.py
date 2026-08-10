import importlib

import pytest
from flask import Flask, g


caching_module = importlib.import_module('caching')
limiter_module = importlib.import_module('limiter')

build_cache_key = caching_module.build_cache_key
build_limit_key = limiter_module.build_limit_key


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    return flask_app


def test_build_limit_key_prefers_login_username(app):
    with app.test_request_context('/user/login', method='POST', json={'username': 'alice'}):
        assert build_limit_key() == 'login:alice'


def test_build_limit_key_uses_authenticated_user_id(app):
    with app.app_context():
        with app.test_request_context('/user/42', method='GET'):
            g.auth_user_id = 42
            assert build_limit_key() == 'user:42'
            g.auth_user_id = None


def test_build_cache_key_uses_namespace_and_parts():
    assert build_cache_key('users', 'find_by_id', 7) == 'users:find_by_id:7'

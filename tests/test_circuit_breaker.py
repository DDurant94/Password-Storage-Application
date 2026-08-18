import time

import pytest

from utils.circuitbreaker import CircuitBreaker
from utils.errorHandlers import ApiError

"""Circuit Breaker Testing"""

def test_circuit_breaker_opens_after_threshold_and_uses_fallback():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, fallback=lambda: 'fallback')
    wrapped = breaker(flaky)

    try:
        wrapped()
    except RuntimeError:
        pass

    try:
        wrapped()
    except RuntimeError:
        pass

    assert wrapped() == 'fallback'


def test_circuit_breaker_recovers_after_timeout():
    calls = {'count': 0}

    def flaky():
        calls['count'] += 1
        if calls['count'] == 1:
            raise RuntimeError('boom')
        return 'ok'

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01, fallback=lambda: 'fallback')
    wrapped = breaker(flaky)

    try:
        wrapped()
    except RuntimeError:
        pass

    time.sleep(0.02)
    assert wrapped() == 'ok'


def test_circuit_breaker_does_not_open_on_business_errors():
    def flaky():
        raise ValueError('bad input')

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
    wrapped = breaker(flaky)

    with pytest.raises(ValueError):
        wrapped()

    with pytest.raises(ValueError):
        wrapped()


def test_circuit_breaker_raises_service_unavailable_when_open_without_fallback():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
    wrapped = breaker(flaky)

    try:
        wrapped()
    except RuntimeError:
        pass

    with pytest.raises(ApiError) as exc:
        wrapped()

    assert exc.value.status_code == 503
    assert 'temporarily unavailable' in str(exc.value).lower()

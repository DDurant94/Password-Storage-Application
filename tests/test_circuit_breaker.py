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

def test_circuit_breaker_configure_updates_threshold_and_fallback():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
    wrapped = breaker(flaky)

    # Reconfigure threshold to 3 and add fallback
    breaker.configure(failure_threshold=3, fallback=lambda: 'reconfigured fallback')

    # First failure should not trip because threshold is now 3
    with pytest.raises(RuntimeError):
        wrapped()

    # Second failure
    with pytest.raises(RuntimeError):
        wrapped()

    # Third failure trips the breaker and triggers fallback
    assert wrapped() == 'reconfigured fallback'

def test_circuit_breaker_set_fallback():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
    wrapped = breaker(flaky)

    try:
        wrapped()
    except RuntimeError:
        pass

    # Open state without fallback raises 503
    with pytest.raises(ApiError):
        wrapped()

    # Setting fallback updates behavior immediately
    breaker.set_fallback(lambda: 'updated fallback')
    assert wrapped() == 'updated fallback'


def test_circuit_breaker_direct_attribute_assignment():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    wrapped = breaker(flaky)

    breaker.failure_threshold = 1
    breaker.fallback = lambda: 'direct attribute fallback'

    # Single failure trips now that threshold is 1
    assert wrapped() == 'direct attribute fallback'

def test_circuit_breaker_protect_per_function_fallback_override():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1, fallback=lambda: 'default fallback')

    @breaker.protect(fallback=lambda: 'custom function fallback')
    def decorated():
        return flaky()

    # Triggers failure and custom fallback
    assert decorated() == 'custom function fallback'

def test_circuit_breaker_reset():
    def flaky():
        raise RuntimeError('boom')

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
    wrapped = breaker(flaky)

    try:
        wrapped()
    except RuntimeError:
        pass

    assert breaker.is_open() is True
    breaker.reset()
    assert breaker.is_open() is False
    assert breaker.failure_count == 0
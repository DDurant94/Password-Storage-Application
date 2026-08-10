import time
from functools import wraps

from utils.error_handlers import ApiError


class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30, fallback=None, expected_exception=None):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback = fallback
        self.expected_exception = expected_exception or (lambda exc_type, _: not issubclass(exc_type, ValueError))
        self._failure_count = 0
        self._opened_at = None
        self._state = 'closed'

    def _is_open(self):
        if self._state != 'open':
            return False

        if self._opened_at is None:
            return False

        if time.time() - self._opened_at >= self.recovery_timeout:
            self._state = 'half-open'
            return False

        return True

    def _record_success(self):
        self._failure_count = 0
        self._opened_at = None
        self._state = 'closed'

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = 'open'
            self._opened_at = time.time()

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if self._is_open():
                if self.fallback is not None:
                    return self.fallback(*args, **kwargs)
                raise ApiError('Service temporarily unavailable', status_code=503)

            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                exc_type = type(exc)
                if not self.expected_exception(exc_type, exc):
                    raise

                self._record_failure()
                if self._state == 'open' and self.fallback is not None:
                    return self.fallback(*args, **kwargs)
                raise
            else:
                self._record_success()
                return result

        return wrapper


def protected_call(fn, *args, **kwargs):
    breaker = getattr(fn, '__circuit_breaker__', None)
    if breaker is None:
        return fn(*args, **kwargs)

    return breaker(fn)(*args, **kwargs)

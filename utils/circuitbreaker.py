"""Circuit Breaker Pattern implementation for service fault tolerance.

Usage Examples:
---------------
1. Instantiating with custom threshold, recovery timeout, and fallback:
    service_breaker = CircuitBreaker(
        failure_threshold=3,     # Number of consecutive failures before opening (tripping)
        recovery_timeout=30,     # Seconds to wait before attempting recovery (half-open state)
        fallback=lambda *args, **kwargs: None  # Optional fallback callable when circuit is open
    )

2. Updating configuration at runtime:
    # Option A: Using configure() helper
    service_breaker.configure(failure_threshold=5, recovery_timeout=15, fallback=my_fallback)

    # Option B: Setting attributes directly
    service_breaker.failure_threshold = 5
    service_breaker.recovery_timeout = 15
    service_breaker.fallback = my_fallback

    # Option C: Using set_fallback() helper
    service_breaker.set_fallback(my_fallback)

3. Decorating service functions:
    @service_breaker
    def my_service_function(user_id, data):
        ...

    # Or override fallback per function:
    @service_breaker.protect(fallback=lambda user_id, data: [])
    def find_items(user_id, data):
        ...
"""

import time
from functools import wraps
from typing import Any, Callable, Optional

from utils.errorHandlers import ApiError

DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_RECOVERY_TIMEOUT = 30
_UNSET = object()


class CircuitBreaker:
    """Manages service failure states to prevent cascading system failures.

    Args:
        failure_threshold (int): Number of consecutive failures required to open the circuit.
        recovery_timeout (int|float): Time in seconds before allowing a trial request (half-open).
        fallback (callable, optional): Callable to execute when circuit is open or trips.
            Receives (*args, **kwargs) matching the decorated function.
        expected_exception (callable, optional): Predicate `(exc_type, exc) -> bool` determining
            which exceptions count as circuit failures. Defaults to non-ValueError exceptions.
    """

    def __init__(
        self,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        recovery_timeout: float = DEFAULT_RECOVERY_TIMEOUT,
        fallback: Optional[Callable[..., Any]] = None,
        expected_exception: Optional[Callable[[type, Exception], bool]] = None,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback = fallback
        self.expected_exception = expected_exception or (
            lambda exc_type, _: not issubclass(exc_type, ValueError)
        )
        self._failure_count = 0
        self._opened_at = None
        self._state = 'closed'

    @property
    def state(self) -> str:
        """Current state of circuit breaker ('closed', 'open', 'half-open')."""
        if self._state == 'open' and self._opened_at is not None:
            if time.time() - self._opened_at >= self.recovery_timeout:
                return 'half-open'
        return self._state

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        return self._failure_count

    def is_open(self) -> bool:
        """Check if the circuit is currently open."""
        return self._is_open()

    def configure(
        self,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[float] = None,
        fallback: Any = _UNSET,
        expected_exception: Optional[Callable[[type, Exception], bool]] = None,
    ):
        """Update circuit breaker configuration settings dynamically.

        Args:
            failure_threshold (int, optional): New failure threshold.
            recovery_timeout (float, optional): New recovery timeout in seconds.
            fallback (callable or None, optional): New fallback callable or None to remove.
            expected_exception (callable, optional): New exception filter predicate.

        Returns:
            self: The CircuitBreaker instance for chaining.
        """
        if failure_threshold is not None:
            self.failure_threshold = failure_threshold
        if recovery_timeout is not None:
            self.recovery_timeout = recovery_timeout
        if fallback is not _UNSET:
            self.fallback = fallback
        if expected_exception is not None:
            self.expected_exception = expected_exception
        return self

    def set_fallback(self, fallback: Optional[Callable[..., Any]]):
        """Set or update the fallback handler callable.

        Args:
            fallback (callable or None): Function called with (*args, **kwargs) when open.

        Returns:
            self: The CircuitBreaker instance for chaining.
        """
        self.fallback = fallback
        return self

    def reset(self):
        """Reset failure count and return circuit breaker to closed state."""
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

    def protect(self, fallback: Any = _UNSET):
        """Decorator that wraps a function with this circuit breaker.

        Args:
            fallback (callable, optional): Specific fallback for this decorated function.
                If omitted, uses the breaker's default `fallback`.
        """
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                active_fallback = self.fallback if fallback is _UNSET else fallback

                if self._is_open():
                    if active_fallback is not None:
                        return active_fallback(*args, **kwargs)
                    raise ApiError('Service temporarily unavailable', status_code=503)

                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:
                    exc_type = type(exc)
                    if not self.expected_exception(exc_type, exc):
                        raise

                    self._record_failure()
                    if self._state == 'open' and active_fallback is not None:
                        return active_fallback(*args, **kwargs)
                    raise
                else:
                    self._record_success()
                    return result

            return wrapper
        return decorator

    def __call__(self, fn=None, fallback=_UNSET):
        """Allows CircuitBreaker instance to be used directly as a decorator @breaker or @breaker(fallback=...)."""
        if fn is None or callable(fn) is False or (fn is not None and fallback is not _UNSET):
            # Used as @breaker() or @breaker(fallback=...)
            custom_fallback = fn if fallback is _UNSET and (fn is None or not callable(fn)) else fallback
            return self.protect(fallback=custom_fallback)
        return self.protect(fallback=_UNSET)(fn)


def circuit_breaker(
    failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
    recovery_timeout: float = DEFAULT_RECOVERY_TIMEOUT,
    fallback: Optional[Callable[..., Any]] = None,
    expected_exception: Optional[Callable[[type, Exception], bool]] = None,
) -> CircuitBreaker:
    """Factory function to create a new CircuitBreaker instance."""
    return CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        fallback=fallback,
        expected_exception=expected_exception,
    )


def protected_call(fn, *args, **kwargs):
    breaker = getattr(fn, '__circuit_breaker__', None)
    if breaker is None:
        return fn(*args, **kwargs)

    return breaker(fn)(*args, **kwargs)

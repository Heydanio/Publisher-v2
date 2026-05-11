"""Retry avec backoff exponentiel."""
import time
import functools
from typing import Callable, Type, Tuple, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator de retry avec backoff exponentiel."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retry in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
        return wrapper
    return decorator

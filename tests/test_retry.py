"""Tests retry decorator."""
import pytest
from src.utils.retry import retry


def test_retry_success_first():
    @retry(max_attempts=3, initial_delay=0.01)
    def func():
        return "ok"
    assert func() == "ok"


def test_retry_after_failures():
    count = 0
    @retry(max_attempts=3, initial_delay=0.01)
    def flaky():
        nonlocal count
        count += 1
        if count < 3:
            raise ValueError("fail")
        return "ok"
    assert flaky() == "ok"
    assert count == 3


def test_retry_max_attempts():
    @retry(max_attempts=2, initial_delay=0.01)
    def always_fails():
        raise ValueError("fail")
    with pytest.raises(ValueError):
        always_fails()

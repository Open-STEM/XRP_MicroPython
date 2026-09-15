"""
Unit tests for Timeout class.
"""
import time
import pytest
from XRPLib.timeout import Timeout


class TestTimeout:
    def test_not_done_immediately(self):
        t = Timeout(1.0)
        assert not t.is_done()

    def test_done_after_expiry(self):
        t = Timeout(0.05)
        time.sleep(0.1)
        assert t.is_done()

    def test_none_timeout_never_expires(self):
        t = Timeout(None)
        assert not t.is_done()
        time.sleep(0.05)
        assert not t.is_done()

    def test_zero_timeout_expires_immediately(self):
        t = Timeout(0)
        # A timeout of 0 seconds should expire almost immediately
        time.sleep(0.01)
        assert t.is_done()

    def test_stores_timeout_in_ms(self):
        t = Timeout(2.5)
        assert t.timeout == 2500

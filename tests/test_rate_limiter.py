import time
from src.security.rate_limiter import SmartRateLimiter

def test_rate_limiter_initial(tmp_path):
    state_file = str(tmp_path / ".test_last_sent")
    limiter = SmartRateLimiter(min_delay_seconds=60, max_delay_seconds=120, state_file=state_file)
    can_send, remaining = limiter.can_send_now()
    assert can_send is True
    assert remaining == 0

def test_rate_limiter_cooldown_active(tmp_path):
    state_file = str(tmp_path / ".test_last_sent")
    limiter = SmartRateLimiter(min_delay_seconds=60, max_delay_seconds=120, state_file=state_file)
    limiter.record_sent(fake_timestamp=time.time())

    can_send, remaining = limiter.can_send_now()
    assert can_send is False
    assert remaining > 0

def test_rate_limiter_cooldown_expired(tmp_path):
    state_file = str(tmp_path / ".test_last_sent")
    limiter = SmartRateLimiter(min_delay_seconds=10, max_delay_seconds=20, state_file=state_file)
    # Simulate sent 30 seconds ago
    limiter.record_sent(fake_timestamp=time.time() - 30)

    can_send, remaining = limiter.can_send_now()
    assert can_send is True
    assert remaining == 0

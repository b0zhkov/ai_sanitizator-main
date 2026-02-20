from datetime import datetime, timezone, timedelta
import json
import asyncio
import time
from collections import defaultdict
from fastapi import Request


CHAR_LIMIT = 2000
COOLDOWN_HOURS = 3

def check_rate_limit(user, db, cost: int, limit: int = CHAR_LIMIT):
    """
    Checks if the user has exceeded the usage limit.
    Returns a tuple (is_allowed, error_message_or_none).
    If usage exceeds limit, sets a cooldown on the user.
    """
    if not user:
        return True, None

    now = datetime.now(timezone.utc)

    # Check existing lockout
    if user.rewrite_lockout_until and user.rewrite_lockout_until > now:
        remaining = user.rewrite_lockout_until - now
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return False, f"Usage limit exceeded. Try again in {hours}h {minutes}m."

    current_usage = user.chars_used_current_session or 0
    
    # Check if this request would exceed limit
    if current_usage + cost > limit:
        user.rewrite_lockout_until = now + timedelta(hours=COOLDOWN_HOURS)
        user.chars_used_current_session = 0
        db.commit()
        return False, f"Usage limit ({limit} chars) exceeded. You are now on a {COOLDOWN_HOURS}-hour cooldown. You can still use Sanitization."

    return True, None

def update_usage(user, db, cost: int):
    """Updates the user's current session usage."""
    if user:
        user.chars_used_current_session = (user.chars_used_current_session or 0) + cost
        db.commit()

class IPRateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60, max_entries: int = 1000):
        self.max_requests = max_requests
        self.window = window_seconds
        self.max_entries = max_entries
        self._hits: dict[str, list[float]] = defaultdict(list)
    
    def check(self, request: Request) -> tuple[bool, str | None]:
        """
        Checks if the IP has exceeded the rate limit.
        Returns a tuple (is_allowed, error_message_or_none).
        """
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Periodic cleanup if dictionary grows too large to prevent memory leak
        if len(self._hits) > self.max_entries:
            self._prune_all(now)
            
        # Prune old entries for this specific IP
        self._hits[ip] = [t for t in self._hits[ip] if now - t < self.window]
        
        if len(self._hits[ip]) >= self.max_requests:
            return False, "Rate limit exceeded for anonymous usage. Try again later or log in."
        
        self._hits[ip].append(now)
        return True, None

    def _prune_all(self, now: float):
        """Cleans up expired IP entries across the entire dictionary."""
        for ip in list(self._hits.keys()):
            self._hits[ip] = [t for t in self._hits[ip] if now - t < self.window]
            if not self._hits[ip]:
                del self._hits[ip]

anonymous_rewrite_limiter = IPRateLimiter(max_requests=5, window_seconds=60)

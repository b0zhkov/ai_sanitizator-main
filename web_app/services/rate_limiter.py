from datetime import datetime, timezone, timedelta
import json
import asyncio

def check_rate_limit(user, db, cost: int, limit: int = 2000):
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
        user.rewrite_lockout_until = now + timedelta(hours=3)
        user.chars_used_current_session = 0
        db.commit()
        return False, "Usage limit (2000 chars) exceeded. You are now on a 3-hour cooldown. You can still use Sanitization."

    return True, None

def update_usage(user, db, cost: int):
    """Updates the user's current session usage."""
    if user:
        user.chars_used_current_session = (user.chars_used_current_session or 0) + cost
        db.commit()

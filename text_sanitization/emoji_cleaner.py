"""
Emoji Cleaner module.

This module provides functionality to remove emojis from text.
It uses a comprehensive regex pattern to match unicode emoji characters.
"""
import re

_EMOJI_REGEX = re.compile(
    r'[\U00010000-\U0010ffff]'
    r'|[\u2600-\u27BF]'
    r'|[\u2300-\u23FF]'
    r'|[\u2B50-\u2B55]'
    r'|[\u203C-\u2049]'
    r'|[\u3030-\u303D]'
    r'|[\u3297-\u3299]'
    r'|[\u200D]'
    , flags=re.UNICODE
)

def remove_emojis(text: str) -> str:
    
    if not text:
        return ""
        
    return _EMOJI_REGEX.sub('', text)

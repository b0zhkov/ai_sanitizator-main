"""
Profanity Filter module.

This module provides functionality to censor profane words.
It uses a predefined list of words and replaces them with [CENSORED].
"""
import re

_PROFANITY_LIST = {
    "fuck", "shit", "bitch", "asshole", "cunt", "faggot", "nigger", "dick", "pussy", "cock", "bastard", "slut"
}

_PROFANITY_REGEX = re.compile(
    r'\b(' + '|'.join(re.escape(word) for word in _PROFANITY_LIST) + r')\b',
    flags=re.IGNORECASE
)

def redact_profanity(text: str) -> str:

    if not text:
        return ""
        
    def replace(match):
        word = match.group(0)
        return "*" * len(word)
        
    return _PROFANITY_REGEX.sub(replace, text)

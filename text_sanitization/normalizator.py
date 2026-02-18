"""
The normalizator ensures consistency in punctuation usage across the text.

It achieves this by:
1. Defining a map of replacement characters (e.g., curly quotes to straight quotes).
2. Using regular expressions to efficiently substitute these characters in the text.
3. Normalizing line endings to a standard newline format.

The end goal is to have text with uniform punctuation, reducing noise for subsequent processing steps.
"""
import re

REPLACEMENT_MAP = {
    '\u201c': '"',
    '\u201d': '"',
    '\u2018': "'",
    '\u2019': "'",
    '\u2013': '-',
    '\u2014': '-',
    '\u2026': '...',
    '\u2044': '/',
    '\u00A0': ' '
}

_KEYS = sorted(REPLACEMENT_MAP.keys(), key=len, reverse=True)
_PATTERN = re.compile('|'.join(re.escape(k) for k in _KEYS))

PATTERNS = [(re.escape(k), v) for k, v in REPLACEMENT_MAP.items()]

def normalize_punctuation(text: str) -> str:
    if not text:
        return ""
    
    text = _PATTERN.sub(lambda m: REPLACEMENT_MAP[m.group(0)], text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text
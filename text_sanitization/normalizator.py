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

def normalize_punctuation(text: str) -> str:
    if not text:
        return ""
        
    return _PATTERN.sub(lambda m: REPLACEMENT_MAP[m.group(0)], text)
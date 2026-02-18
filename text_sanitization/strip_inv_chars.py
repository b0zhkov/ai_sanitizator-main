"""
The strip invisible characters file's main purpose is to sanitize the text by:
1. removing hidden characters,
2. removing tracking artifacts,
3. removing formatting debris that do not contribute to the content.

It achieves this by:
1. defining regex patterns for invisible characters, tracking artifacts, and inline styles.
2. applying Unicode normalization (NFKC) to ensure character consistency.
3. attempting to fix common encoding issues using fallback encodings.

The end goal is to produce a clean text stream free of invisible noise and formatting artifacts.
"""
import re
import unicodedata

INVISIBLE_CHARS = re.compile(r'[\u200B-\u200D\uFEFF\u00A0]')
TRACKING_ARTIFACTS = re.compile(r'[\u202A-\u202E]')
INLINE_STYLES = re.compile(r'style=["\'][^"\']*["\']')
ASTERISKS = re.compile(r'\*')
TRAILING_WHITESPACE = re.compile(r'\s+$')
MARKDOWN_HEADINGS = re.compile(r'^\s*#+\s*')

PATTERNS = [
    (INVISIBLE_CHARS, ''),
    (TRACKING_ARTIFACTS, ''),
    (INLINE_STYLES, ''),
    (ASTERISKS, ''),
    (TRAILING_WHITESPACE, ''),
    (MARKDOWN_HEADINGS, '')
]

def validate_and_fix_encoding(text: str) -> str:
    if not text:
        return ""

    for encoding in ('cp1252', 'cp1251'):
        try:
            fixed = text.encode(encoding).decode('utf-8')
            if len(fixed) < len(text):
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
            
    return text

def sanitize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize('NFKC', text)
    text = validate_and_fix_encoding(text)
    text = INVISIBLE_CHARS.sub('', text)
    text = TRACKING_ARTIFACTS.sub('', text)
    text = INLINE_STYLES.sub('', text)
    text = ASTERISKS.sub('', text)
    text = TRAILING_WHITESPACE.sub('', text)
    text = MARKDOWN_HEADINGS.sub('', text)
    
    return text
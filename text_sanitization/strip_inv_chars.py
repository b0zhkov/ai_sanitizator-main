import re
import unicodedata

_INVISIBLE_CHARS = re.compile(r'[\u200B-\u200D\uFEFF\u00A0]')
_TRACKING_ARTIFACTS = re.compile(r'[\u202A-\u202E]')
_INLINE_STYLES = re.compile(r'style=["\'][^"\']*["\']')
_ASTERISKS = re.compile(r'\*')
_TRAILING_WHITESPACE = re.compile(r'\s+$')
_MARKDOWN_HEADINGS = re.compile(r'^\s*#+\s*')

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
    text = _INVISIBLE_CHARS.sub('', text)
    text = _TRACKING_ARTIFACTS.sub('', text)
    text = _INLINE_STYLES.sub('', text)
    text = _ASTERISKS.sub('', text)
    text = _TRAILING_WHITESPACE.sub('', text)
    text = _MARKDOWN_HEADINGS.sub('', text)
    
    return text
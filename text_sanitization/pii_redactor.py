"""
PII Redactor module.

Redacts Personally Identifiable Information (PII) — email addresses,
URLs, and IP addresses — using regex patterns.

This avoids loading the spacy NLP model for what is essentially
pattern matching, keeping the "clean" action spacy-free.
"""
import re
import socket

_EMAIL_RE = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
)

_URL_RE = re.compile(
    r'https?://\S+'        # http:// or https:// followed by non-whitespace
    r'|'
    r'www\.[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\S*'  # www.domain.tld...
)

_IPV4_RE = re.compile(
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
)


def _replace_ip(match: re.Match) -> str:
    """Replace only syntactically valid IPv4 addresses."""
    ip_str = match.group(0)
    try:
        socket.inet_aton(ip_str)
        return "[IP]"
    except socket.error:
        return ip_str


def redact_pii(text: str) -> str:
    """Redact emails, URLs, and IPs from *text*, returning the cleaned string."""
    if not text:
        return ""

    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _URL_RE.sub("[URL]", text)
    text = _IPV4_RE.sub(_replace_ip, text)

    return text
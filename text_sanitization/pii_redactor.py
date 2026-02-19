"""
PII Redactor module.

This module provides functionality to redact Personally Identifiable Information (PII)
such as email addresses, URLs, and IP addresses.
"""
import re
import socket

_EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)
_URL_REGEX = re.compile(
    r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+|www\.[-\w]+\.[-\w]+'
)

_IPV4_REGEX = re.compile(
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
)

def redact_pii(text: str) -> str:
    if not text:
        return ""
        
    text = _EMAIL_REGEX.sub("[EMAIL]", text)
    text = _URL_REGEX.sub("[URL]", text)
    
    def replace_ip(match):
        ip_str = match.group(0)
        try:
            socket.inet_aton(ip_str)
            return "[IP]"
        except socket.error:
            return ip_str

    text = _IPV4_REGEX.sub(replace_ip, text)
        
    return text

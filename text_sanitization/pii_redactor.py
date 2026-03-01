"""
PII Redactor module.

This module provides functionality to redact Personally Identifiable Information (PII)
such as email addresses, URLs, and IP addresses.
"""
import re
import socket
import shared_nlp

_IPV4_REGEX = re.compile(
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
)

def redact_pii(text: str) -> str:
    if not text:
        return ""
        
    # spacy's built-in token attributes handle emails and URLs out of the box
    nlp = shared_nlp.get_nlp_light()
    doc = nlp(text)
    
    result = []
    for token in doc:
        if token.like_email:
            result.append("[EMAIL]" + token.whitespace_)
        elif token.like_url:
            result.append("[URL]" + token.whitespace_)
        else:
            result.append(token.text_with_ws)
            
    text = "".join(result)
    
    def replace_ip(match):
        ip_str = match.group(0)
        try:
            # inet_aton validates it's actually an IP, not just four numbers with dots
            socket.inet_aton(ip_str)
            return "[IP]"
        except socket.error:
            return ip_str

    text = _IPV4_REGEX.sub(replace_ip, text)
        
    return text

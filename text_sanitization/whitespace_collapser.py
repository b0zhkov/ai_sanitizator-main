"""
Whitespace Collapser module.

This module provides functionality to normalize whitespace, ensuring consistent spacing.
It collapses multiple spaces into single spaces and limits consecutive newlines to two.
"""
import re

_MULTIPLE_SPACES = re.compile(r'[ \t\f\v]+')
_EXCESSIVE_NEWLINES = re.compile(r'(\r?\n){3,}')


def collapse_whitespace(text: str) -> str:
    if not text:
        return ""
    
    clean_lines = []
    for line in text.splitlines():
        clean_line = _MULTIPLE_SPACES.sub(' ', line).strip()
        clean_lines.append(clean_line)
    
    text = '\n'.join(clean_lines)
    
    text = _EXCESSIVE_NEWLINES.sub('\n\n', text)
    
    return text.strip()

"""
Whitespace Collapser module.

This module provides functionality to normalize whitespace, ensuring consistent spacing.
It collapses multiple spaces into single spaces and limits consecutive newlines to two.
"""
import re

# Regex for multiple spaces (except newlines)
_MULTIPLE_SPACES = re.compile(r'[ \t\f\v]+')
# Regex for more than 2 newlines
_EXCESSIVE_NEWLINES = re.compile(r'(\r?\n){3,}')


def collapse_whitespace(text: str) -> str:
    """
    Normalizes whitespace in the text.
    
    1. Replaces sequences of spaces/tabs with a single space.
    2. Uses max 2 consecutive newlines to preserve paragraphs but remove huge gaps.
    
    Args:
        text (str): Input text.
        
    Returns:
        str: Normalized text.
    """
    if not text:
        return ""
    
    # First, collapse inline whitespace (spaces, tabs)
    # We want to preserve newlines initially so we don't merge paragraphs into one line.
    # However, Python's split() splits by ANY whitespace including newlines.
    
    # Strategy: 
    # 1. Split lines.
    # 2. For each line, collapse internal whitespace.
    # 3. Join lines back, then normalize excessive vertical whitespace.
    
    clean_lines = []
    for line in text.splitlines():
        # Collapse internal spaces in the line and strip ends
        clean_line = _MULTIPLE_SPACES.sub(' ', line).strip()
        clean_lines.append(clean_line)
        
    # Rejoin with standard newline
    text = '\n'.join(clean_lines)
    
    # Now collapse excessive newlines (max 2)
    text = _EXCESSIVE_NEWLINES.sub('\n\n', text)
    
    return text.strip()

"""
Markdown Stripper module.

This module provides functionality to strip Markdown syntax from text.
It removes formatting like bold, italic, links, headers, and code blocks.
"""
import re

_MARKDOWN_ELEMENTS = [
    (re.compile(r'^#{1,6}\s*', re.MULTILINE), ''),
    (re.compile(r'\*{2}(.*?)\*{2}'), r'\1'),
    (re.compile(r'_{2}(.*?)_{2}'), r'\1'),
    (re.compile(r'\*(.*?)\*'), r'\1'),
    (re.compile(r'_(.*?)_'), r'\1'),
    (re.compile(r'!\[(.*?)\]\(.*?\)'), r'\1'),
    (re.compile(r'\[(.*?)\]\(.*?\)'), r'\1'),
    (re.compile(r'^>\s*', re.MULTILINE), ''),
    (re.compile(r'`(.*?)`'), r'\1'),
    (re.compile(r'```.*?\n?(.*?)```', re.DOTALL), r'\1'),
    (re.compile(r'^\s*[-*_]{3,}\s*$', re.MULTILINE), '')
]

def strip_markdown(text: str) -> str:

    if not text:
        return ""
    
    for pattern, replacement in _MARKDOWN_ELEMENTS:
        text = pattern.sub(replacement, text)
        
    return text

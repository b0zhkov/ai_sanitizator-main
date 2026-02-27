from collections import namedtuple
import re
import unicodedata
import strip_inv_chars
import normalizator
import html_cleaner
import whitespace_collapser
import pii_redactor
import markdown_stripper
import profanity_filter
import emoji_cleaner

Change = namedtuple('Change', ['description', 'text_before', 'text_after'])

def apply_regex_changes(text, regex_patterns):
    changes = []
    
    for pattern, replacement in regex_patterns:

        if hasattr(pattern, 'pattern'):
            pat_str = pattern.pattern
        else:
            pat_str = str(pattern)
            
        new_text, num_changes = re.subn(pattern, replacement, text)
        if num_changes > 0:
            changes.append(Change(
                description=f"Replaced '{pat_str}' with '{replacement}' ({num_changes} occurrences)",
                text_before=text,
                text_after=new_text
            ))
            text = new_text
            
    return changes, text

def build_changes_log(text):
    changes = []
    
    transformations = [
        ("Stripped HTML Tags", html_cleaner.clean_html),
        ("Stripped Markdown Syntax", markdown_stripper.strip_markdown),
        ("Applied NFKC Unicode Normalization", lambda str_: unicodedata.normalize('NFKC', str_)),
        ("Fixed Text Encoding", strip_inv_chars.validate_and_fix_encoding),
    ]

    for description, func in transformations:
        new_text = func(text)
        if new_text != text:
            changes.append(Change(
                description=description,
                text_before=text,
                text_after=new_text
            ))
            text = new_text

    regex_changes, text = apply_regex_changes(text, strip_inv_chars.PATTERNS)
    changes.extend(regex_changes)
    
    post_regex_transformations = [
        ("Redacted PII (Emails, URLs, IPs)", pii_redactor.redact_pii),
        ("Removed Emojis", emoji_cleaner.remove_emojis),
        ("Redacted Profanity", profanity_filter.redact_profanity),
        ("Collapsed Excessive Whitespace", whitespace_collapser.collapse_whitespace),
    ]

    for description, func in post_regex_transformations:
        new_text = func(text)
        if new_text != text:
            changes.append(Change(
                description=description,
                text_before=text,
                text_after=new_text
            ))
            text = new_text

    regex_changes, text = apply_regex_changes(text, normalizator.PATTERNS)
    changes.extend(regex_changes)
    
    return text, changes
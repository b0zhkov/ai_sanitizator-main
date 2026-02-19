from collections import namedtuple
import re
import unicodedata
import strip_inv_chars
import normalizator
import html_cleaner
import whitespace_collapser
import pii_redactor

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
    
    new_text = unicodedata.normalize('NFKC', text)
    if new_text != text:
        changes.append(Change(
            description="Applied NFKC Unicode Normalization",
            text_before=text,
            text_after=new_text
        ))
        text = new_text

    new_text = strip_inv_chars.validate_and_fix_encoding(text)
    if new_text != text:
        changes.append(Change(
            description="Fixed Text Encoding",
            text_before=text,
            text_after=new_text
        ))
        text = new_text

    regex_changes, text = apply_regex_changes(text, strip_inv_chars.PATTERNS)
    changes.extend(regex_changes)
    
    regex_changes, text = apply_regex_changes(text, normalizator.PATTERNS)
    changes.extend(regex_changes)
    
    return text, changes

def summarize_changes(changes):
    summaries = []
    for change in changes:
        summaries.append(change.description)
    return summaries
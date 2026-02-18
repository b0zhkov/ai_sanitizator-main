"""
This file is resposible for importing the cleaned version which was processed and cleaned by the 
files inside of the text_sanitization folder.
The goal is to follow the DRY priciple and to make it easier for the other files inside of the
analysis folder to import the cleaned text.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from text_sanitization.normalizator import normalize_punctuation
from text_sanitization.strip_inv_chars import sanitize_text
from text_sanitization.document_loading import load_file_content

def get_clean_text_from_file(file_path: str) -> str:

    try:
        text = load_file_content(file_path)
        return get_clean_text_from_string(text)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return ""

def get_clean_text_from_string(raw_text: str) -> str:
    
    text = sanitize_text(raw_text)
    text = normalize_punctuation(text)
    return text
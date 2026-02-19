"""
This file is responsible for importing the cleaned version which was processed and cleaned by the 
files inside of the text_sanitization folder.
The goal is to follow the DRY principle and to make it easier for the other files inside of the
analysis folder to import the cleaned text.
"""
import os
import sys
import _paths  # noqa: E402 — centralised path setup

from text_sanitization.changes_log import build_changes_log
from text_sanitization.document_loading import load_file_content

def get_clean_text_from_file(file_path: str) -> str:

    try:
        text = load_file_content(file_path)
        return get_clean_text_from_string(text)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return ""

def get_clean_text_from_string(raw_text: str) -> str:
    text, _ = build_changes_log(raw_text)
    return text
"""
HTML Cleaner module.

This module provides functionality to stArip HTML tags from text while preserving the content.
It uses BeautifulSoup for robust parsing and cleaning.
"""
from bs4 import BeautifulSoup

def clean_html(text: str) -> str:

    if not text:
        return ""

    try:
        soup = BeautifulSoup(text, "html.parser")

        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ")
        return text.strip()
    except Exception:

        return text

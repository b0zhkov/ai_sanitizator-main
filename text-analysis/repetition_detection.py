"""
The repetition detection module identifies recurring phrases and patterns.

The main purpose is to find n-gram repetitions that make the text feel robotic
or redundant.

It achieves this by:
1. Tokenizing the text into words.
2. generating n-grams of specified lengths (e.g., 2-5 words).
3. identifying and counting duplicates.

The end goal is to highlight repetitive phrasing that needs variation.
"""
from __future__ import annotations

import os
import sys
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

import _paths

if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    _NLTK_DIR = "/tmp/nltk_data"
    os.makedirs(_NLTK_DIR, exist_ok=True)
    if _NLTK_DIR not in nltk.data.path:
        nltk.data.path.append(_NLTK_DIR)
    
    try:
        nltk.data.find('tokenizers/punkt', paths=[_NLTK_DIR])
    except LookupError:
        try:
            nltk.download('punkt', download_dir=_NLTK_DIR)
        except Exception as e:
            print(f"Warning: Failed to download 'punkt' tokenizer to /tmp: {e}")
else:
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt')
        except Exception as e:
            print(f"Warning: Failed to download 'punkt' tokenizer: {e}")


def tokenize_text(text: str) -> list[str]:
    return word_tokenize(text)

def tokenize_text_into_sentences(text: str) -> list[str]:
    return sent_tokenize(text)

def get_repeating_keyphrases(text: str, min_phrase_length: int = 2, max_phrase_length: int = 5) -> list[str]:
    words = tokenize_text(text)
    keyphrases = _extract_ngrams(words, min_phrase_length, max_phrase_length)
    return _find_repetitions(keyphrases)

def _extract_ngrams(words: list[str], min_length: int, max_length: int) -> list[str]:
    return [
        ' '.join(gram)
        for n in range(min_length, max_length + 1)
        for gram in nltk.ngrams(words, n)
    ]

def _find_repetitions(items: list[str]) -> list[str]:
    seen = {}
    repeated = []
    repeated_normalized = set()
    for item in items:
        normalized = item.lower()
        if normalized in seen:
            if normalized not in repeated_normalized:
                repeated.append(seen[normalized])
                repeated_normalized.add(normalized)
        else:
            seen[normalized] = item
    return repeated
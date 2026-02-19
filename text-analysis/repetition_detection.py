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
import clean_text_getter

import _paths  # noqa: E402 — centralised path setup

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt')
    except Exception as e:
        print(f"Warning: Failed to download 'punkt' tokenizer: {e}")
        # Proceeding without punkt might cause issues later if not handled, 
        # but prevents immediate crash on import.



def tokenize_text(text: str) -> list[str]:
    return word_tokenize(clean_text_getter.get_clean_text_from_string(text))

def tokenize_text_into_sentences(text: str) -> list[str]:
    return sent_tokenize(clean_text_getter.get_clean_text_from_string(text))

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
    for item in items:
        normalized = item.lower()
        if normalized in seen:
            if normalized not in {r.lower() for r in repeated}:
                repeated.append(seen[normalized])
        else:
            seen[normalized] = item
    return repeated
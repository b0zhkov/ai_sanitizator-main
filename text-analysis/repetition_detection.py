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

from collections import Counter
import shared_nlp

import _paths


def tokenize_text(text: str) -> list[str]:
    nlp = shared_nlp.get_nlp_light()
    doc = nlp(text)
    return [token.text for token in doc if not token.is_punct and not token.is_space]

def tokenize_text_into_sentences(text: str) -> list[str]:
    nlp = shared_nlp.get_nlp_light()
    doc = nlp(text)
    return [sent.text for sent in doc.sents]

def get_repeating_keyphrases(text: str, min_phrase_length: int = 2, max_phrase_length: int = 5) -> list[str]:
    words = tokenize_text(text)
    keyphrases = _extract_ngrams(words, min_phrase_length, max_phrase_length)
    return _find_repetitions(keyphrases)

def _extract_ngrams(words: list[str], min_length: int, max_length: int) -> list[str]:
    ngrams = []
    for n in range(min_length, max_length + 1):
        for i in range(len(words) - n + 1):
            ngrams.append(' '.join(words[i:i+n]))
    return ngrams

def _find_repetitions(items: list[str]) -> list[str]:
    counts = Counter(item.lower() for item in items)
    # We want to return the original case-version of the first occurrence
    # Or just returning the lowercase version is fine. The original code returned the original case.
    # Let's preserve original case for the output.
    seen_originals = {}
    for item in items:
        lower_item = item.lower()
        if lower_item not in seen_originals:
            seen_originals[lower_item] = item
            
    return [seen_originals[normalized] for normalized, count in counts.items() if count > 1]
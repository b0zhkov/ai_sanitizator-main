"""
This file is responsible for injecting imperfections into the text.
That is important because the LLM always tries to make the text sound too perfect and textbook-like.
But this gets flagged by the detectors.

This script injects occasional typos from `typos.csv` as well as typographical quirks
like double spaces after periods or substituting 'and' with '&'.
"""
import os
import csv
import re
import random
from typing import List, Tuple

import _paths  # noqa: E402 — centralised path setup

_COMMON_TYPOS = {}
_CONTRACTION_TYPOS = {}
_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_typos_loaded = False

def _load_typos_csv():
    global _COMMON_TYPOS, _CONTRACTION_TYPOS, _typos_loaded
    if _typos_loaded:
        return
        
    filepath = os.path.join(_DATA_DIR, "typos.csv")
    if not os.path.exists(filepath):
        _typos_loaded = True
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row.get("Original", "").strip().lower()
            typo = row.get("Typo", "").strip()
            t_type = row.get("Type", "").strip().lower()
            
            if original and typo:
                if t_type == "word":
                    _COMMON_TYPOS[original] = typo
                elif t_type == "contraction":
                    _CONTRACTION_TYPOS[original] = typo
                    
    _typos_loaded = True

_TYPO_RATE = 0.05
_CONTRACTION_TYPO_RATE = 0.15
_AMPERSAND_RATE = 0.25
_DOUBLE_SPACE_RATE = 0.40

def _cleanup_spaces(text: str) -> str:
    return re.sub(r'[ \t]+', ' ', text)


def _fuzz_spelling(text: str) -> str:
    
    words = re.split(r'(\s+|[.,;!?])', text)
    result = []
    
    for w in words:
        if not w or w.isspace() or re.match(r'[.,;!?]', w):
            result.append(w)
            continue
            
        w_lower = w.lower()
        new_w = w
        
        if w_lower in _COMMON_TYPOS and random.random() < _TYPO_RATE:
            new_w = _COMMON_TYPOS[w_lower]
            if w[0].isupper():
                new_w = new_w.capitalize()
        elif w_lower in _CONTRACTION_TYPOS and random.random() < _CONTRACTION_TYPO_RATE:
            new_w = _CONTRACTION_TYPOS[w_lower]
            if w[0].isupper():
                new_w = new_w.capitalize()
                
        result.append(new_w)
        
    return "".join(result)


def _inject_typographical_quirks(text: str) -> str:
    # Ampersand swaps
    words = text.split(' ')
    result = []
    for w in words:
        if w.lower() == "and" and random.random() < _AMPERSAND_RATE:
            result.append("&")
        else:
            result.append(w)
    text = ' '.join(result)

    if random.random() < _DOUBLE_SPACE_RATE:
        text = re.sub(r'([.!?])\s+(?=[A-Z])', r'\1  ', text)
        
    return text


def inject_imperfections(text: str) -> str:
    if not text:
        return text
        
    _load_typos_csv()
    
    text = _fuzz_spelling(text)
    text = _inject_typographical_quirks(text)
    
    return text
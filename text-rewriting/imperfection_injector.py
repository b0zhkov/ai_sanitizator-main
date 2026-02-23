"""
This file is responsible for injecting imperfections into the text.
That is important because the LLM always tries to make the text sound too perfect and textbook-like.
But this gets flagged by the detectors.

The imperfections the file handles are the occasional removal (50%) of "that" when it is appropriate.
Appropriate meaning when "that" is used as a conjunction rather than a pronoun.

The other imperfection is regarding paragraphs since they also like the sentences have uniformal length,
which is not the case in human writing.
So the logic here is to find small sub 40 word paragraphs and merge them with the following paragraph to
decrease the uniformity of the text.
"""
import os
import csv
import re
import random
from typing import List, Tuple

import _paths  # noqa: E402 — centralised path setup
import shared_nlp

_THAT_DROP_RATE = 0.50       
_PARAGRAPH_MERGE_RATE = 0.20 
_MAX_MERGE_WORDS = 150       
_MIN_PARA_WORDS = 40         
_SAFE_HEAD_POS = {"VERB", "ADJ", "NOUN"}

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

def _get_nlp():
    return shared_nlp.get_nlp_light()


def _cleanup_spaces(text: str) -> str:
    return re.sub(r'[ \t]+', ' ', text)


def _remove_optional_that(text: str) -> str:
    nlp = _get_nlp()
    if nlp is None:
        return text

    doc = nlp(text)
    
    removals: List[Tuple[int, int]] = []
    
    for token in doc:
        if token.text.lower() == "that":
            
            if (token.dep_ == "mark" and
                token.head.dep_ == "ccomp" and
                token.head.head.pos_ in _SAFE_HEAD_POS):
                
                if random.random() < _THAT_DROP_RATE:
                    if token.whitespace_:
                         removals.append((token.idx, token.idx + len(token.text_with_ws)))
                    else:
                         removals.append((token.idx, token.idx + len(token.text)))

    if not removals:
        return text

    removals.sort(key=lambda x: x[0], reverse=True)
    
    for start, end in removals:
        text = text[:start] + text[end:]
        
    return _cleanup_spaces(text)


def _vary_paragraphs(text: str) -> str:
    paragraphs = text.split('\n\n')
    if len(paragraphs) <= 1:
        return text
        
    merged_paragraphs = []
    i = 0
    while i < len(paragraphs):
        current_para = paragraphs[i]
        
        if i < len(paragraphs) - 1:
            next_para = paragraphs[i+1]
            
            len_curr = len(current_para.split())
            len_next = len(next_para.split())
            
            if (len_curr < _MIN_PARA_WORDS and 
                len_next < _MIN_PARA_WORDS and 
                (len_curr + len_next) < _MAX_MERGE_WORDS and
                random.random() < _PARAGRAPH_MERGE_RATE):
                
                merged_paragraphs.append(current_para + " " + next_para)
                i += 2 
                continue
        
        merged_paragraphs.append(current_para)
        i += 1
        
    return '\n\n'.join(merged_paragraphs)


def _fuzz_spelling(text: str) -> str:
    words = text.split(' ')
    result = []
    for w in words:
        clean_w = w.strip(".,!?\"';:()")
        if not clean_w:
            result.append(w)
            continue
            
        w_lower = clean_w.lower()
        if w_lower in _COMMON_TYPOS and random.random() < _TYPO_RATE:
            new_w = _COMMON_TYPOS[w_lower]
            if clean_w[0].isupper():
                new_w = new_w.capitalize()
            w = w.replace(clean_w, new_w)
        elif w_lower in _CONTRACTION_TYPOS and random.random() < _CONTRACTION_TYPO_RATE:
            new_w = _CONTRACTION_TYPOS[w_lower]
            if clean_w[0].isupper():
                new_w = new_w.capitalize()
            w = w.replace(clean_w, new_w)
            
        result.append(w)
    return ' '.join(result)


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
    
    # Double space after periods (simulate human typing habits)
    if random.random() < _DOUBLE_SPACE_RATE:
        text = re.sub(r'([.!?])\s+(?=[A-Z])', r'\1  ', text)
        
    return text


def inject_imperfections(text: str) -> str:
    if not text:
        return text
        
    _load_typos_csv()
    
    text = _remove_optional_that(text)
    text = _vary_paragraphs(text)
    text = _fuzz_spelling(text)
    text = _inject_typographical_quirks(text)
    
    return text
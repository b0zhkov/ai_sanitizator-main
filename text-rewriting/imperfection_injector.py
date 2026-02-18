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
import re
import random
from typing import List, Tuple, Optional

try:
    import spacy
    import spacy.cli
except ImportError:
    spacy = None

_nlp = None

_THAT_DROP_RATE = 0.50       
_PARAGRAPH_MERGE_RATE = 0.20 
_MAX_MERGE_WORDS = 150       
_MIN_PARA_WORDS = 40         
_SAFE_HEAD_POS = {"VERB", "ADJ", "NOUN"}

def _get_nlp():
    global _nlp
    if spacy is None:
        return None
        
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "textcat", "entity_linker"])
        except OSError:
            print("Downloading spacy model en_core_web_sm...")
            spacy.cli.download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "textcat", "entity_linker"])
            
    return _nlp


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


def inject_imperfections(text: str) -> str:
    if not text:
        return text
        
    text = _remove_optional_that(text)
    
    text = _vary_paragraphs(text)
    
    return text
import re
import os
import csv
import random
from typing import List, Dict

_BURST_RATE = 0.15
_SPICE_RATE = 0.40
_IDIOM_RATE = 0.30

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))

_ADJECTIVE_SPICE: Dict[str, List[str]] = {}
_BURST_MODIFIERS: List[str] = []
_IDIOMS: Dict[str, List[str]] = {}
_data_loaded = False

def _load_csv_data() -> None:
    global _ADJECTIVE_SPICE, _BURST_MODIFIERS, _IDIOMS, _data_loaded

    if _data_loaded:
        return

    _ADJECTIVE_SPICE = _load_alternatives_csv("adjective_spice.csv", "Standard", "Alternatives")
    _IDIOMS = _load_alternatives_csv("idioms.csv", "Standard", "Idioms")
    _BURST_MODIFIERS = _load_list_csv("burst_modifiers.csv", "Modifier")
    _data_loaded = True


def _load_alternatives_csv(filename: str, key_col: str, val_col: str) -> Dict[str, List[str]]:
    filepath = os.path.join(_DATA_DIR, filename)
    result: Dict[str, List[str]] = {}

    if not os.path.exists(filepath):
        return result

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get(key_col, "").strip()
            values_raw = row.get(val_col, "").strip()
            if key and values_raw:
                result[key] = [v.strip() for v in values_raw.split("|")]
    
    return result


def _load_list_csv(filename: str, col_name: str) -> List[str]:
    filepath = os.path.join(_DATA_DIR, filename)
    result: List[str] = []

    if not os.path.exists(filepath):
        return result
        
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get(col_name, "").strip()
            if val:
                result.append(val)
                
    return result


def _preserve_case(original: str, replacement: str) -> str:
    if not original:
        return replacement
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _replace_match(match: re.Match, replacements: List[str]) -> str:
    if not replacements:
        return match.group(0)
    choice = random.choice(replacements)
    return _preserve_case(match.group(0), choice)



def _spice_adjectives(text: str) -> str:
    for adj, spices in _ADJECTIVE_SPICE.items():
        pattern = re.compile(r'\b' + re.escape(adj) + r'\b', re.IGNORECASE)
        
        def replacer(m, choices=spices):
            if random.random() > _SPICE_RATE:
                return m.group(0)
            return _replace_match(m, choices)
            
        text = pattern.sub(replacer, text)
    return text


def _inject_bursts(text: str) -> str:
    if not _BURST_MODIFIERS:
        return text

    starters = frozenset({"The", "It", "This", "That", "There", "He", "She", "We", "They"})
    
    sentences = text.split('. ')
    result = []
    
    for i, sent in enumerate(sentences):
        if not sent.strip():
            result.append(sent)
            continue
            
        words = sent.split()
        if not words:
            result.append(sent)
            continue
            
        first = words[0]
        clean_first = first.strip('"\'')
        
        injected = False
        
        if clean_first in starters and random.random() < _BURST_RATE:
            modifier = random.choice(_BURST_MODIFIERS)
            new_first = first[0].lower() + first[1:]
            new_sent = modifier + " " + new_first + sent[len(first):]
            result.append(new_sent)
            injected = True
            
        elif not injected and "," in sent and random.random() < _BURST_RATE:
             parts = sent.split(',', 1)
             modifier = random.choice(_BURST_MODIFIERS).rstrip(',')
             
             if len(parts) > 1 and parts[1].strip():
                 suffix = parts[1]
                 if not suffix.startswith(' '):
                     suffix = " " + suffix
                 
                 result.append(parts[0] + ", " + modifier + "," + suffix)
             else:
                 result.append(sent)
        else:
            result.append(sent)
            
    return '. '.join(result)


def _inject_idioms(text: str) -> str:
    for phrase, idioms in _IDIOMS.items():
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        
        def replacer(m, choices=idioms):
             if random.random() > _IDIOM_RATE:
                 return m.group(0)
             return _replace_match(m, choices)
         
        text = pattern.sub(replacer, text)
    return text

def enhance_perplexity(text: str) -> str:
    if not text:
        return text

    _load_csv_data()

    text = _inject_idioms(text)
    text = _spice_adjectives(text)
    text = _inject_bursts(text)
    
    return text
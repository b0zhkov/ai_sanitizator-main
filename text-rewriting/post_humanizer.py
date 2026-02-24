"""
This file is the last step before presenting the rewritten text to the user.

This file orchestrates the remaining "humanization" pipeline by applying a series of
transformations designed to degrade the "perfect" quality of AI text into something
more organic and flawed. 

It achieves this through a layered process:
1. Aggressively converts full two-word pairs (e.g., "do not", "they are") into their contracted forms ("don't", "they're") to sound less formal.
2. Calls the imperfection injector to randomly add humanizing typos and typographical quirks like double spaces.
"""
import re
import os
import csv
from typing import Dict
from imperfection_injector import inject_imperfections
import shared_utils

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_contraction_pairs: Dict[str, str] = {}
_data_loaded = False

_contraction_pattern = None
_contraction_lookup = None


def _load_csv_data() -> None:
    global _contraction_pairs, _data_loaded

    if _data_loaded:
        return

    _contraction_pairs = _load_two_column_csv("contraction_pairs.csv")
    _data_loaded = True


def _load_two_column_csv(filename: str) -> Dict[str, str]:
    filepath = os.path.join(_DATA_DIR, filename)
    result: Dict[str, str] = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values = list(row.values())
            key = str(values[0]).strip()
            value = str(values[1]).strip()
            if key and value:
                result[key] = value

    return result


def _enforce_contractions(text: str) -> str:
    global _contraction_pattern, _contraction_lookup
    if not _contraction_pairs:
        return text
        
    if _contraction_pattern is None:
        _contraction_lookup = {k.lower(): v for k, v in _contraction_pairs.items()}
        _contraction_pattern = shared_utils.build_optimized_regex(list(_contraction_pairs.keys()))
    
    def replacer(match):
        key = match.group(0).lower()
        if key not in _contraction_lookup:
            return match.group(0)
        return shared_utils.preserve_case(match.group(0), _contraction_lookup[key])
        
    return _contraction_pattern.sub(replacer, text)


def humanize(text: str, strength: str = "medium") -> str:

    if not text or not text.strip():
        return text

    _load_csv_data()

    text = _enforce_contractions(text)
    text = inject_imperfections(text)
    
    return text
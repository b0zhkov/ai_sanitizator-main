"""
This file is the last step before presenting the rewritten text to the user.

This file orchestrates the entire "humanization" pipeline by applying a series of
transformations designed to degrade the "perfect" quality of AI text into something
more organic and flawed. It serves as the main entry point that coordinates
specialized sub-modules (like structure breaking and perplexity enhancement) with
its own internal logic.

It achieves this through a layered process:
1. Systemically replaces complex, "university-level" words with simpler, conversational alternatives (e.g., "utilize" -> "use") using `vocab_swaps.csv`.
2. Aggressively converts full two-word pairs (e.g., "do not", "they are") into their contracted forms ("don't", "they're") to sound less formal.
3. Identifies formal transitions (e.g., "Furthermore," "In conclusion") and either deletes them or replaces them with casual alternatives (e.g., "Also," "So").
4. Calls external modules to break sentence structures, inject imperfections, and enhance perplexity.

Technical Realization:
The module loads several CSV databases upon first use (`_load_csv_data`) to build lookup dictionaries.
The `humanize()` function acts as the master controller, passing the text through each transformation 
function sequentially. It uses regex substitution with custom callback functions (`_make_vocabulary_replacer`)
to handle case-preservation during replacements. The order of operations is critical: vocabulary and 
contractions are fixed first to establish a "base" conversational tone, before the heavier structural 
changes are applied by the imported modules.
"""
import re
import os
import csv
import random
from typing import List, Dict, Callable
from structure_breaker import break_structure
from perplexity_enhancer import enhance_perplexity
from imperfection_injector import inject_imperfections
import shared_utils




STRENGTH_PRESETS = {
    "light":      {"vocab": 0.40, "transition_drop": 0.15, "transition_replace": 0.20, "conjunction": 0.05},
    "medium":     {"vocab": 0.85, "transition_drop": 0.30, "transition_replace": 0.40, "conjunction": 0.12},
    "aggressive": {"vocab": 1.00, "transition_drop": 0.50, "transition_replace": 0.60, "conjunction": 0.20},
}

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_CONJUNCTION_WORDS = frozenset({"and", "but", "or", "so", "yet", "nor", "for"})
_contraction_pairs: Dict[str, str] = {}
_transition_alternatives: Dict[str, List[str]] = {}
_vocabulary_swaps: Dict[str, str] = {}
_data_loaded = False


def _load_csv_data() -> None:
    global _contraction_pairs, _transition_alternatives, _vocabulary_swaps, _data_loaded

    if _data_loaded:
        return

    _contraction_pairs = _load_two_column_csv("contraction_pairs.csv")
    _transition_alternatives = _load_transition_csv("transition_alternatives.csv")
    _vocabulary_swaps = _load_two_column_csv("vocab_swaps.csv")
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


def _load_transition_csv(filename: str) -> Dict[str, List[str]]:
    filepath = os.path.join(_DATA_DIR, filename)
    result: Dict[str, List[str]] = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values = list(row.values())
            formal = str(values[0]).strip()
            alternatives_raw = str(values[1]).strip()
            if formal and alternatives_raw:
                result[formal] = [alt.strip() for alt in alternatives_raw.split("|")]

    return result





def _lowercase_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:] if len(text) > 1 else text[0].lower()


def _enforce_contractions(text: str) -> str:
    if not _contraction_pairs:
        return text
        
    lookup = {k.lower(): v for k, v in _contraction_pairs.items()}
    keys = list(_contraction_pairs.keys())
    pattern = _build_optimized_regex(keys)
    
    def replacer(match):
        key = match.group(0).lower()
        if key not in lookup:
            return match.group(0)
        return shared_utils.preserve_case(match.group(0), lookup[key])
        
    return pattern.sub(replacer, text)


def _fuzz_single_transition_optimized(sentence: str, pattern: re.Pattern, lookup: Dict[str, List[str]], drop_rate: float, replace_rate: float) -> str:
    # Only attempt replacements on transitions that start the sentence
    match = pattern.match(sentence)
    if not match:
        return sentence
            
    formal = match.group(0)
    key = formal.lower()
    
    if key not in lookup:
        return sentence

    remainder = sentence[len(formal):].lstrip()
    if not remainder:
        return sentence

    roll = random.random()

    if roll < drop_rate:
        return shared_utils.capitalize_first(remainder)

    if roll < drop_rate + replace_rate:
        alternatives = lookup[key]
        return random.choice(alternatives) + " " + remainder

    return sentence


def _fuzz_transitions(text: str, drop_rate: float, replace_rate: float) -> str:
    if not _transition_alternatives:
        return text

    # Build optimized pattern for transitions
    # Transitions are phrase starts.
    keys = list(_transition_alternatives.keys())
    sorted_keys = sorted(keys, key=len, reverse=True)
    pattern_str = '|'.join(re.escape(k) for k in sorted_keys)
    # Match at start of string
    pattern = re.compile(r'^(' + pattern_str + r')\b', re.IGNORECASE)
    
    lookup = {k.lower(): v for k, v in _transition_alternatives.items()}

    paragraphs = text.split('\n\n')
    result = []

    for paragraph in paragraphs:
        sentences = shared_utils.split_sentences(paragraph)
        fuzzed = [_fuzz_single_transition_optimized(s, pattern, lookup, drop_rate, replace_rate) for s in sentences]
        result.append(' '.join(fuzzed))

    return '\n\n'.join(result)


def _inject_into_sentences(sentences: List[str], conjunction_rate: float) -> List[str]:
    if len(sentences) < 3:
        return sentences
        
    result = [sentences[0]]

    for i in range(1, len(sentences)):
        sentence = sentences[i]
        words = sentence.split()
        if not words:
            result.append(sentence)
            continue

        first_word = words[0].lower().rstrip('.,;:')

        if first_word not in _CONJUNCTION_WORDS and random.random() < conjunction_rate:
            conjunction = random.choice(["And ", "But "])
            if first_word in shared_utils.LOWERABLE_STARTERS:
                sentence = conjunction + _lowercase_first(sentence)
            else:
                sentence = conjunction + sentence

        result.append(sentence)

    return result


def _inject_conjunctions(text: str, rate: float) -> str:
    paragraphs = text.split('\n\n')
    result = []

    for paragraph in paragraphs:
        sentences = shared_utils.split_sentences(paragraph)
        injected = _inject_into_sentences(sentences, rate)
        result.append(' '.join(injected))

    return '\n\n'.join(result)


def _downgrade_vocabulary(text: str, rate: float) -> str:
    if not _vocabulary_swaps:
        return text
        
    lookup = {k.lower(): v for k, v in _vocabulary_swaps.items()}
    keys = list(_vocabulary_swaps.keys())
    pattern = shared_utils.build_optimized_regex(keys)
    
    def replacer(match):
        if random.random() >= rate:
            return match.group(0)
            
        key = match.group(0).lower()
        if key not in lookup:
            return match.group(0)
        return shared_utils.preserve_case(match.group(0), lookup[key])

    return pattern.sub(replacer, text)


def humanize(text: str, strength: str = "medium") -> str:
    if not text or not text.strip():
        return text

    # Load config based on strength
    preset = STRENGTH_PRESETS.get(strength, STRENGTH_PRESETS["medium"])
    config = {
        "vocab_rate": preset["vocab"],
        "transition_drop": preset["transition_drop"],
        "transition_replace": preset["transition_replace"],
        "conjunction_rate": preset["conjunction"]
    }

    _load_csv_data()

    text = _downgrade_vocabulary(text, config["vocab_rate"])
    text = _enforce_contractions(text)
    text = _fuzz_transitions(text, config["transition_drop"], config["transition_replace"])
    text = _inject_conjunctions(text, config["conjunction_rate"])
    text = inject_imperfections(text)
    text = enhance_perplexity(text)
    text = break_structure(text)
    return text

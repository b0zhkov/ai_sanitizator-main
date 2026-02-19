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


TRANSITION_DROP_RATE = 0.30
TRANSITION_REPLACE_RATE = 0.40
CONJUNCTION_RATE = 0.12
VOCABULARY_SWAP_RATE = 0.85

STRENGTH_PRESETS = {
    "light":      {"vocab": 0.40, "transition_drop": 0.15, "transition_replace": 0.20, "conjunction": 0.05},
    "medium":     {"vocab": 0.85, "transition_drop": 0.30, "transition_replace": 0.40, "conjunction": 0.12},
    "aggressive": {"vocab": 1.00, "transition_drop": 0.50, "transition_replace": 0.60, "conjunction": 0.20},
}

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+')
_CONJUNCTION_WORDS = frozenset({"and", "but", "or", "so", "yet", "nor", "for"})
_LOWERABLE_STARTERS = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "it", "its", "they", "their", "we", "our", "my",
    "he", "she", "his", "her", "there", "here",
    "some", "many", "most", "all", "each", "every",
    "one", "no", "not", "when", "while", "if", "as",
    "what", "which", "how", "where", "why",
})

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


def _substr(text: str, start: int, end: int = -1) -> str:
    if end == -1:
        end = len(text)
    chars = []
    for i in range(start, min(end, len(text))):
        chars.append(text[i])
    return ''.join(chars)


def _capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + _substr(text, 1) if len(text) > 1 else text[0].upper()


def _lowercase_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + _substr(text, 1) if len(text) > 1 else text[0].lower()


def _preserve_case(original: str, replacement: str) -> str:
    if not original or not replacement:
        return replacement
    if replacement[0] == "I" and len(replacement) > 1 and replacement[1] in ("'", " "):
        return replacement
    if original[0].isupper():
        return _capitalize_first(replacement)
    return replacement


def _make_contraction_replacer(contracted: str) -> Callable[[re.Match[str]], str]:
    def replacer(match: re.Match[str]) -> str:
        return _preserve_case(match.group(0), contracted)
    return replacer


def _make_vocabulary_replacer(common: str) -> Callable[[re.Match[str]], str]:
    def replacer(match: re.Match[str]) -> str:
        if random.random() < VOCABULARY_SWAP_RATE:
            return _preserve_case(match.group(0), common)
        return match.group(0)
    return replacer


def _split_sentences(text: str) -> List[str]:
    return [s for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]


def _build_optimized_regex(keys: List[str]) -> re.Pattern:
    # Sort by length descending to match longest first
    sorted_keys = sorted(keys, key=len, reverse=True)
    pattern_str = '|'.join(re.escape(k) for k in sorted_keys)
    return re.compile(r'\b(' + pattern_str + r')\b', re.IGNORECASE)

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
        return _preserve_case(match.group(0), lookup[key])
        
    return pattern.sub(replacer, text)


def _fuzz_single_transition_optimized(sentence: str, pattern: re.Pattern, lookup: Dict[str, List[str]]) -> str:
    # Check if sentence starts with any of the transitions
    # The pattern matches at \b, but transitions are usually at start.
    # We want to match ONLY at the beginning of the string.
    # So we use pattern.match (anchored at pos 0) if the pattern started with ^
    # But our shared pattern generator uses \b.
    # We need a specific pattern for transitions: ^(Formal1|Formal2|...)
    
    match = pattern.match(sentence)
    if not match:
        return sentence
            
    formal = match.group(0) # This picks the text that matched
    # But we need the case-insensitive key to lookup
    key = formal.lower()
    
    # In lookup, keys are lowercase? 
    # _load_transition_csv loads them as is. 
    # We need to ensure lookup map is lowercased.
    if key not in lookup:
        # Fallback to original flow if something weird happens with casing
        # or if the match wasn't in our lookup
        return sentence

    remainder = _substr(sentence, len(formal)).lstrip()
    if not remainder:
        return sentence

    roll = random.random()

    if roll < TRANSITION_DROP_RATE:
        return _capitalize_first(remainder)

    if roll < TRANSITION_DROP_RATE + TRANSITION_REPLACE_RATE:
        alternatives = lookup[key]
        return random.choice(alternatives) + " " + remainder

    return sentence


def _fuzz_transitions(text: str) -> str:
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
        sentences = _split_sentences(paragraph)
        fuzzed = [_fuzz_single_transition_optimized(s, pattern, lookup) for s in sentences]
        result.append(' '.join(fuzzed))

    return '\n\n'.join(result)


def _inject_into_sentences(sentences: List[str]) -> List[str]:
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

        if first_word not in _CONJUNCTION_WORDS and random.random() < CONJUNCTION_RATE:
            conjunction = random.choice(["And ", "But "])
            if first_word in _LOWERABLE_STARTERS:
                sentence = conjunction + _lowercase_first(sentence)
            else:
                sentence = conjunction + sentence

        result.append(sentence)

    return result


def _inject_conjunctions(text: str) -> str:
    paragraphs = text.split('\n\n')
    result = []

    for paragraph in paragraphs:
        sentences = _split_sentences(paragraph)
        injected = _inject_into_sentences(sentences)
        result.append(' '.join(injected))

    return '\n\n'.join(result)


def _downgrade_vocabulary(text: str) -> str:
    if not _vocabulary_swaps:
        return text
        
    lookup = {k.lower(): v for k, v in _vocabulary_swaps.items()}
    keys = list(_vocabulary_swaps.keys())
    pattern = _build_optimized_regex(keys)
    
    def replacer(match):
        if random.random() >= VOCABULARY_SWAP_RATE:
            return match.group(0)
            
        key = match.group(0).lower()
        if key not in lookup:
            return match.group(0)
        return _preserve_case(match.group(0), lookup[key])

    return pattern.sub(replacer, text)


def humanize(text: str, strength: str = "medium") -> str:
    if not text or not text.strip():
        return text

    global VOCABULARY_SWAP_RATE, TRANSITION_DROP_RATE, TRANSITION_REPLACE_RATE, CONJUNCTION_RATE

    preset = STRENGTH_PRESETS.get(strength, STRENGTH_PRESETS["medium"])
    VOCABULARY_SWAP_RATE = preset["vocab"]
    TRANSITION_DROP_RATE = preset["transition_drop"]
    TRANSITION_REPLACE_RATE = preset["transition_replace"]
    CONJUNCTION_RATE = preset["conjunction"]

    _load_csv_data()

    text = _downgrade_vocabulary(text)
    text = _enforce_contractions(text)
    text = _fuzz_transitions(text)
    text = _inject_conjunctions(text)
    text = inject_imperfections(text)
    text = enhance_perplexity(text)
    text = break_structure(text)
    return text

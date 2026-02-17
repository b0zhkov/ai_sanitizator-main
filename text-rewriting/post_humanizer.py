import re
import os
import csv
import random
from typing import List, Dict, Callable
from structure_breaker import break_structure
from perplexity_enhancer import enhance_perplexity


TRANSITION_DROP_RATE = 0.30
TRANSITION_REPLACE_RATE = 0.40
CONJUNCTION_RATE = 0.12
VOCABULARY_SWAP_RATE = 0.75

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


def _enforce_contractions(text: str) -> str:
    for expanded, contracted in _contraction_pairs.items():
        pattern = re.compile(r'\b' + re.escape(expanded) + r'\b', re.IGNORECASE)
        text = pattern.sub(_make_contraction_replacer(contracted), text)
    return text


def _fuzz_single_transition(sentence: str) -> str:
    for formal, alternatives in _transition_alternatives.items():
        if not sentence.startswith(formal):
            continue

        remainder = _substr(sentence, len(formal)).lstrip()
        if not remainder:
            return sentence

        roll = random.random()

        if roll < TRANSITION_DROP_RATE:
            return _capitalize_first(remainder)

        if roll < TRANSITION_DROP_RATE + TRANSITION_REPLACE_RATE:
            return random.choice(alternatives) + " " + remainder

        return sentence

    return sentence


def _fuzz_transitions(text: str) -> str:
    paragraphs = text.split('\n\n')
    result = []

    for paragraph in paragraphs:
        sentences = _split_sentences(paragraph)
        fuzzed = [_fuzz_single_transition(s) for s in sentences]
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
    sorted_swaps = sorted(
        _vocabulary_swaps.items(),
        key=lambda pair: len(pair[0]),
        reverse=True
    )

    for elevated, common in sorted_swaps:
        pattern = re.compile(r'\b' + re.escape(elevated) + r'\b', re.IGNORECASE)
        text = pattern.sub(_make_vocabulary_replacer(common), text)

    return text


def humanize(text: str) -> str:
    if not text or not text.strip():
        return text

    _load_csv_data()

    text = _downgrade_vocabulary(text)
    text = _enforce_contractions(text)
    text = _fuzz_transitions(text)
    text = _inject_conjunctions(text)
    text = enhance_perplexity(text)
    text = break_structure(text)
    return text

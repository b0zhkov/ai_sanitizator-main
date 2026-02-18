"""
The structure breaker module is responsible for the disruption of AI patterns.

The end goal is to increase the burstiness of the text and make it less predictable.


It achieves this through several randomized operations:
1. Breaks compound sentences at conjunctions (and, but, because) to create punchier, shorter statements.
2. Merges short sentences using dashes or conjunctions to create longer, more complex thoughts.
3. Moves subordinate clauses from the end of a sentence to the beginning (e.g., "I went home because it rained" -> "Because it rained, I went home").
4. Swaps predictable commas for more expressive punctuation like em-dashes (—) or semicolons (;).

Regex patterns are the core components used to identify sentence boundaries, conjunctions 
and subordinate clauses. It processes text paragraph by paragraph to maintain context, 
first splitting excessively long sentences based on a character threshold
then conditionally merging short ones. Finally, it applies clause reordering and 
punctuation swaps based on the probability constants defined in the module.

The end goal of this module is to assist with breaking the uniformity of AI text.
"""
import re
import random
from typing import List, Tuple


_SENTENCE_BOUNDARY = re.compile(r'(?<!\bDr)(?<!\bMr)(?<!\bMs)(?<!\bMrs)(?<!\bvs)(?<!\bSt)(?<=[.!?])\s+')

_SPLIT_CONJUNCTIONS = re.compile(
    r',\s*(and|but|or|yet|so|because|although|while|whereas|since|though)\s+',
    re.IGNORECASE,
)

_MOVABLE_CLAUSE = re.compile(
    r'^(.+?),\s*(because|since|although|while|though|when|whereas)\s+(.+)$',
    re.IGNORECASE,
)

_SENTENCE_SPLIT_RATE = 0.60
_SENTENCE_MERGE_RATE = 0.50
_CLAUSE_REORDER_RATE = 0.30
_COMMA_TO_DASH_RATE = 0.12
_COMMA_TO_SEMICOLON_RATE = 0.0

_MIN_SPLIT_CHARS = 60
_SHORT_SENTENCE_WORDS = 8
_MIN_WORDS_PER_SIDE = 3

_SAFE_TO_LOWERCASE = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "it", "its", "they", "their", "we", "our", "my",
    "he", "she", "his", "her", "there", "here",
    "some", "many", "most", "all", "each", "every",
    "one", "no", "not", "when", "while", "if", "as",
    "but", "and", "or", "so", "yet", "for", "nor",
})

def _split_into_sentences(text: str) -> List[str]:
    return [s for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]


def _capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:] if len(text) > 1 else text[0].upper()


def _lowercase_first_if_safe(text: str) -> str:
    if not text:
        return text
    first_word = text.split()[0].rstrip('.,;:!?')

    if first_word.lower() in _SAFE_TO_LOWERCASE:
        return text[0].lower() + text[1:]

    if len(first_word) <= 2 or first_word.isupper():
        return text
    if first_word[0].isupper() and first_word[1:].islower():
        return text[0].lower() + text[1:]

    return text


def _word_count(text: str) -> int:
    return len(text.split())


def _has_min_words(text: str, minimum: int = _MIN_WORDS_PER_SIDE) -> bool:
    return _word_count(text) >= minimum


def _strip_terminal_punct(text: str) -> Tuple[str, str]:
    stripped = text.rstrip()
    if stripped and stripped[-1] in '.!?':
        return stripped[:-1], stripped[-1]
    return stripped, ''

def _split_long_sentence(sentence: str) -> str:
    if len(sentence) < _MIN_SPLIT_CHARS:
        return sentence

    if random.random() > _SENTENCE_SPLIT_RATE:
        return sentence

    match = _SPLIT_CONJUNCTIONS.search(sentence)
    if not match:
        return sentence

    first_half = sentence[:match.start()].rstrip()
    rest = sentence[match.end():]
    conjunction = match.group(1)

    if not _has_min_words(first_half) or not _has_min_words(rest):
        return sentence

    capitalized_conn = _capitalize_first(conjunction)
    rest_clean = rest.lstrip()

    if conjunction.lower() in ("and", "but"):
        second_half = capitalized_conn + ", " + _lowercase_first_if_safe(rest_clean)
    else:
        second_half = capitalized_conn + " " + rest_clean

    if first_half[-1] not in '.!?':
        first_half += "."

    return first_half + " " + second_half


def _merge_short_sentences(sentences: List[str]) -> List[str]:
    if len(sentences) < 3:
        return sentences

    result: List[str] = []
    i = 0

    while i < len(sentences):
        current = sentences[i]
        can_merge = (
            i + 1 < len(sentences)
            and _word_count(current) <= _SHORT_SENTENCE_WORDS
            and _word_count(sentences[i + 1]) <= _SHORT_SENTENCE_WORDS
            and random.random() < _SENTENCE_MERGE_RATE
        )

        if can_merge:
            first, _ = _strip_terminal_punct(current)
            second = sentences[i + 1]

            connector = random.choices(
                [" — ", ", and "],
                weights=[1, 5],
                k=1,
            )[0]

            merged = first + connector + _lowercase_first_if_safe(second)
            result.append(merged)
            i += 2
        else:
            result.append(current)
            i += 1

    return result


def _reorder_clause(sentence: str) -> str:
    if random.random() > _CLAUSE_REORDER_RATE:
        return sentence

    match = _MOVABLE_CLAUSE.match(sentence)
    if not match:
        return sentence

    main_clause = match.group(1).rstrip()
    subordinator = match.group(2)
    subordinate = match.group(3)

    if not _has_min_words(main_clause) or not _has_min_words(subordinate):
        return sentence

    sub_body, terminal = _strip_terminal_punct(subordinate)
    main_body, _ = _strip_terminal_punct(main_clause)

    reordered = (
        _capitalize_first(subordinator) + " " + sub_body.lstrip()
        + ", " + _lowercase_first_if_safe(main_body)
        + (terminal or ".")
    )

    return reordered


def _diversify_punctuation(sentence: str) -> str:
    if " — " in sentence or " – " in sentence or ";" in sentence:
        return sentence

    parts = sentence.split(", ")
    if len(parts) < 3:
        return sentence

    valid_indices = [
        idx for idx in range(1, len(parts) - 1)
        if _has_min_words(", ".join(parts[:idx]))
        and _has_min_words(", ".join(parts[idx:]))
    ]

    if not valid_indices:
        return sentence

    idx = random.choice(valid_indices)
    before = ", ".join(parts[:idx])
    after = ", ".join(parts[idx:])

    roll = random.random()

    if roll < _COMMA_TO_DASH_RATE:
        return before + " — " + after

    if roll < _COMMA_TO_DASH_RATE + _COMMA_TO_SEMICOLON_RATE:
        return before + "; " + after

    return sentence


def _fix_stray_dashes(text: str) -> str:

    text = re.sub(r'\s+[-–—]\s*([.!?])', r'\1', text)
    text = re.sub(r'\s+[-–—]\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'(\w)\s+-\s+(\w)', r'\1, \2', text)
    return text


def break_structure(text: str) -> str:

    if not text or not text.strip():
        return text

    text = _fix_stray_dashes(text)

    paragraphs = text.split('\n\n')
    result: List[str] = []

    for paragraph in paragraphs:
        sentences = _split_into_sentences(paragraph)

        split_sentences: List[str] = []
        for sentence in sentences:
            broken = _split_long_sentence(sentence)
            split_sentences.extend(_split_into_sentences(broken))
        merged_sentences = _merge_short_sentences(split_sentences)

        final_sentences = [
            _diversify_punctuation(_reorder_clause(s))
            for s in merged_sentences
        ]

        result.append(' '.join(final_sentences))

    return '\n\n'.join(result)

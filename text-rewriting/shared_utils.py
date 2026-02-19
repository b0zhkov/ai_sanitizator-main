import re
from typing import List

_SENTENCE_BOUNDARY = re.compile(r'(?<!\bDr)(?<!\bMr)(?<!\bMs)(?<!\bMrs)(?<!\bvs)(?<!\bSt)(?<=[.!?])\s+')

LOWERABLE_STARTERS = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "it", "its", "they", "their", "we", "our", "my",
    "he", "she", "his", "her", "there", "here",
    "some", "many", "most", "all", "each", "every",
    "one", "no", "not", "when", "while", "if", "as",
    "what", "which", "how", "where", "why",
    "but", "and", "or", "so", "yet", "for", "nor"
})

def split_sentences(text: str) -> List[str]:
    return [s for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]

def capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:] if len(text) > 1 else text[0].upper()

def preserve_case(original: str, replacement: str) -> str:
    if not original or not replacement:
        return replacement
    if replacement[0] == "I" and len(replacement) > 1 and replacement[1] in ("'", " "):
        return replacement
    if original[0].isupper():
        return capitalize_first(replacement)
    return replacement

def build_optimized_regex(keys: List[str]) -> re.Pattern:
    sorted_keys = sorted(keys, key=len, reverse=True)
    pattern_str = '|'.join(re.escape(k) for k in sorted_keys)
    return re.compile(r'\b(' + pattern_str + r')\b', re.IGNORECASE)

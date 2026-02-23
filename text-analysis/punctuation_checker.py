"""
The punctuation checker analyzes the text, then it gathers information as to what punctuation marks
have been used throughout.

The idea is to calculate a ratio of structured to conversational punctuation marks.

The structured ones being more typically used by AI due to them being more formal,
while the conversational ones are more typically used by humans.
"""
import re
from typing import Dict, Any

_STRUCTURED_PATTERN = re.compile(r'[;:•()]')
_CONVERSATIONAL_PATTERN = re.compile(r'[—?!]')

def analyze_punctuation_structure(text: str) -> Dict[str, Any]:
    if not text:
        return {
            "status": "empty_input",
            "structured_punct_count": 0,
            "conversational_punct_count": 0,
            "structure_ratio": 0.0
        }

    structured_matches = _STRUCTURED_PATTERN.findall(text)
    conversational_matches = _CONVERSATIONAL_PATTERN.findall(text)

    s_count = len(structured_matches)
    c_count = len(conversational_matches)

    total_punct = s_count + c_count
    ratio = (s_count / total_punct) if total_punct > 0 else 0.0

    return {
        "status": "success",
        "structured_punct_count": s_count,
        "conversational_punct_count": c_count,
        "structure_ratio": round(ratio, 2)
    }

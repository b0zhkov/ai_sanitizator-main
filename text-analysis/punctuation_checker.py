"""
The pucntuation checker analyzes the text, then it gathers information as to what punctuation marks
have been used throughout.

The idea is to calculate a ratio of structured to conversational punctuation marks.

The structured ones being more typically used by AI due to them being more formal,
while the conversational ones are more typically used by humans.
"""
import re
from typing import Dict

def analyze_punctuation_structure(text: str) -> Dict[str, any]:
    if not text:
        return {
            "status": "empty_input",
            "structured_punct_count": 0,
            "conversational_punct_count": 0,
            "structure_ratio": 0.0
        }

    structured_pattern = r'[;:•()]'
    structured_matches = re.findall(structured_pattern, text)
    
    conversational_pattern = r'[—?!]'
    conversational_matches = re.findall(conversational_pattern, text)

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

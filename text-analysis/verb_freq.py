"""
The verb frequency analyzer checks for the usage of specific "AI-favored" verbs
like "delve", "leverage", and "facilitate" which LLMs tend to overuse.

It achieves this by:
1. Using Spacy for Part-of-Speech tagging to identify verbs.
2. comparing lemmatized verbs against a known blocklist of AI favorites.
3. calculating the density of these verbs in the text.

The end goal is to encourage more natural and varied vocabulary.
"""
from typing import Dict, Any
import spacy

import shared_nlp

AI_FAVORED_VERBS = {
    "delve", "underscore", "illuminate", "facilitate", "bolster", 
    "revolutionize", "navigate", "foster", "optimize", "leverage",
    "transform", "embrace", "cultivate", "harness", "empower",
    "showcase", "streamline", "exemplify", "resonate", "spearhead"
}

def analyze_verb_frequency(text: str) -> Dict[str, Any]:

    if not text or not text.strip():
        return _build_empty_result()

    nlp = shared_nlp.get_nlp_full()
    doc = nlp(text)
    
    total_verbs = 0
    ai_verb_occurrences = 0
    detected_ai_verbs = set()

    for token in doc:
        if token.pos_ == "VERB":
            total_verbs += 1
            lemma = token.lemma_.lower()
            
            if lemma in AI_FAVORED_VERBS:
                detected_ai_verbs.add(lemma)
                ai_verb_occurrences += 1

    ai_verbs_count = ai_verb_occurrences
    density = (ai_verbs_count / total_verbs * 100) if total_verbs > 0 else 0.0

    return {
        "status": "success",
        "total_verbs": total_verbs,
        "ai_verbs_count": ai_verbs_count,
        "ai_verb_density_percentage": round(density, 2),
        "detected_ai_verbs": list(detected_ai_verbs)
    }

def _build_empty_result() -> Dict[str, Any]:
    return {
        "status": "empty_input",
        "total_verbs": 0,
        "ai_verbs_count": 0,
        "ai_verb_density_percentage": 0.0,
        "detected_ai_verbs": []
    }
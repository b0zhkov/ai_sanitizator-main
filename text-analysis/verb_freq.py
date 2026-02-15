from typing import Dict, List, Tuple
import spacy

AI_FAVORED_VERBS = {
    "delve", "underscore", "illuminate", "facilitate", "bolster", 
    "revolutionize", "navigate", "foster", "optimize", "leverage",
    "transform", "embrace", "cultivate", "harness", "empower",
    "showcase", "streamline", "exemplify", "resonate", "spearhead"
}

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

def analyze_verb_frequency(text: str) -> Dict[str, any]:

    if not text or not text.strip():
        return _build_empty_result()

    nlp = _get_nlp()
    doc = nlp(text)
    
    total_verbs = 0
    detected_ai_verbs = set()

    for token in doc:
        if token.pos_ == "VERB":
            total_verbs += 1
            lemma = token.lemma_.lower()
            
            if lemma in AI_FAVORED_VERBS:
                detected_ai_verbs.add(lemma)

    ai_verbs_count = len(detected_ai_verbs)
    density = (ai_verbs_count / total_verbs * 100) if total_verbs > 0 else 0.0

    return {
        "status": "success",
        "total_verbs": total_verbs,
        "ai_verbs_count": ai_verbs_count,
        "ai_verb_density_percentage": round(density, 2),
        "detected_ai_verbs": list(detected_ai_verbs)
    }

def _build_empty_result() -> Dict[str, any]:
    return {
        "status": "empty_input",
        "total_verbs": 0,
        "ai_verbs_count": 0,
        "ai_verb_density_percentage": 0.0,
        "detected_ai_verbs": []
    }
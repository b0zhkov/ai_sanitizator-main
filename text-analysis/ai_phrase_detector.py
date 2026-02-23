"""
The AI phrase detector identifies and flags common AI-generated phrases and mannerisms
that are highly indicative of LLM output.

It achieves this by:
1. Loading a list of known AI phrases from a CSV file.
2. Using regex to match these phrases in the text, respecting word boundaries.
3. Returning the count and list of found phrases.

The end goal is to catch specific "fingerprints" of AI writing that statistical methods might miss.
"""
import csv
import os

import shared_nlp
from spacy.matcher import PhraseMatcher

_nlp = None
_matcher = None

__all__ = ['analyze_ai_phrases']

def _initialize_matcher():
    global _nlp, _matcher
    if _matcher is not None:
        return

    _nlp = shared_nlp.get_nlp_light()
    _matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")

    csv_path = os.path.join(os.path.dirname(__file__), 'ai_phrases.csv')
    phrases = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                phrase = row.get('phrase', '').strip()
                if phrase:
                    phrases.append(phrase)
    
    patterns = [_nlp.make_doc(text) for text in phrases]
    _matcher.add("AI_PHRASE", patterns)


def analyze_ai_phrases(text):
    try:
        _initialize_matcher()
        doc = _nlp(text)
        matches = _matcher(doc)
        
        found_phrases = []
        for match_id, start, end in matches:
            found_phrases.append(doc[start:end].text.lower())
            
        return {
            "count": len(found_phrases),
            "phrases": found_phrases
        }
            
    except Exception as e:
        return {"error": f"Failed to check AI phrases: {str(e)}"}
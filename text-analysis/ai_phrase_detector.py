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
import re

_ai_phrases_cache = None

__all__ = ['analyze_ai_phrases']

def analyze_ai_phrases(text):
    global _ai_phrases_cache
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'ai_phrases.csv')
        
        found_phrases = []
        text_lower = text.lower()
        
        if _ai_phrases_cache is None:
            _ai_phrases_cache = []
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['phrase'].strip():
                            _ai_phrases_cache.append(row['phrase'].strip().lower())
            
            _ai_phrases_cache.sort(key=len, reverse=True)
        
        for phrase in _ai_phrases_cache:
            pattern = re.compile(r'\b' + re.escape(phrase) + r'\b')
            if pattern.search(text_lower):
                found_phrases.append(phrase)
                
        return {
            "count": len(found_phrases),
            "phrases": found_phrases
        }
            
    except Exception as e:
        return {"error": f"Failed to check AI phrases: {str(e)}"}
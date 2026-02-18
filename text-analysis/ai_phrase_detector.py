"""
The AI phrase detector identifies and flag common AI-generated phrases and mannerisms
that are highly indicative of LLM output.

It achieves this by:
1. Loading a list of known AI phrases from a CSV file.
2. using regex to match these phrases in the text, respecting word boundaries.
3. returning the count and list of found phrases.

The end goal is to catch specific "fingerprints" of AI writing that statistical methods might miss.
"""
import csv
import os
import re

def analyze_ai_phrases(text):
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'ai_phrases.csv')
        
        found_phrases = []
        text_lower = text.lower()
        
        ai_phrases = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['phrase'].strip():
                        ai_phrases.append(row['phrase'].strip().lower())
        
        ai_phrases.sort(key=len, reverse=True)
        
        for phrase in ai_phrases:
            pattern = re.compile(r'\b' + re.escape(phrase) + r'\b')
            if pattern.search(text_lower):
                found_phrases.append(phrase)
                
        return {
            "count": len(found_phrases),
            "phrases": found_phrases
        }
            
    except Exception as e:
        return {"error": f"Failed to check AI phrases: {str(e)}"}
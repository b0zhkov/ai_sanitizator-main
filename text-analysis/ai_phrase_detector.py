import csv
import os
import re

def analyze_ai_phrases(text):
    """
    Analyzes text for common AI-generated phrases and mannerisms.
    Returns a dictionary containing the count and a list of found phrases.
    """
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'ai_phrases.csv')
        
        found_phrases = []
        text_lower = text.lower()
        
        # Load phrases from CSV
        ai_phrases = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['phrase'].strip():
                        ai_phrases.append(row['phrase'].strip().lower())
        
        # Check for phrases
        # We process by length (descending) to match longer phrases first if they overlap
        ai_phrases.sort(key=len, reverse=True)
        
        for phrase in ai_phrases:
            # We use a simple containment check. 
            # For phrases, word boundaries are less critical than for single words, 
            # but we should still be careful.
            # strict regex for phrases is safer: \bphrase\b
            
            pattern = re.compile(r'\b' + re.escape(phrase) + r'\b')
            if pattern.search(text_lower):
                found_phrases.append(phrase)
                
        return {
            "count": len(found_phrases),
            "phrases": found_phrases
        }
            
    except Exception as e:
        return {"error": f"Failed to check AI phrases: {str(e)}"}

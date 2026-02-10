import os
import sys
import spacy
import pandas as pd
from spacy.matcher import PhraseMatcher


import clean_text_getter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

nlp = spacy.load("en_core_web_sm")
df = pd.read_csv("excess_words.csv")

style_words = df[df['type'] == 'style']['word'].tolist()
content_words = df[df['type'] == 'content']['word'].tolist()

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

style_patterns = [nlp.make_doc(text) for text in style_words]
matcher.add("AI_FILLER", style_patterns)

def load_and_clean_text(file_path: str) -> str:
    return clean_text_getter.get_clean_text_from_file(file_path)

def analyze_and_filter_out(text: str):
    doc = nlp(text)
    matches = matcher(doc)
    
    to_remove = set()
    found_words = []

    for match_id, start, end in matches:
        found_words.append(doc[start:end].text)
        for i in range(start, end):
            to_remove.add(i)

    cleaned_tokens = [token.text_with_ws for token in doc if token.i not in to_remove]
    cleaned_text = "".join(cleaned_tokens).strip()

    stats = {
        "original_word_count": len(doc),
        "filler_count": len(matches),
        "filler_density": (len(matches) / len(doc)) * 100 if len(doc) > 0 else 0,
        "detected_fillers": list(set(found_words))
    }

    return cleaned_text, stats
"""
The hedging and filler detector is designed to identify and remove "fluff" words.

The main purpose is to target language that dilutes the content's impact, such as excessive
hedging, unnecessary qualifiers, and verbal padding often found in AI-generated text.
Unlike simple keyword matching, this module provides both detection metrics and an experimental
"cleaned" version of the text.

It achieves this by:
1. Using a lazy-loading pattern for the Spacy NLP model to ensure the application starts fast.
2. Ingesting a categorized database of "style" words from `excess_words.csv`.
3. Utilizing Spacy's `PhraseMatcher` for efficient, high-speed pattern matching across the document.
4. Calculating a "filler density" score to quantify how much of the text is non-substantive.

The end goal is to highlight weak writing patterns and provide an immediate option to tighten
the prose by stripping out these redundancies.
"""
import os
import sys
import pandas as pd

import clean_text_getter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import shared_nlp

nlp = None
matcher = None
style_words = None
content_words = None

def _initialize_spacy():
    
    global nlp, matcher, style_words, content_words
    if nlp is not None:
        return

    from spacy.matcher import PhraseMatcher

    nlp = shared_nlp.get_nlp_full()
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "excess_words.csv"))

    style_words = df[df['type'] == 'style']['word'].tolist()
    content_words = df[df['type'] == 'content']['word'].tolist()

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    style_patterns = [nlp.make_doc(text) for text in style_words]
    matcher.add("AI_FILLER", style_patterns)

def load_and_clean_text(file_path: str) -> str:
    return clean_text_getter.get_clean_text_from_file(file_path)

def analyze_and_filter_out(text: str):
    _initialize_spacy()
    
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
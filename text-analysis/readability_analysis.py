"""
This file has the purpose of analyzing the overall readability of the text.
It does that by using the Flesch-Kincaid Grade Level and Flesch Reading Ease formulas.

It works by splitting the text into individual paragraphs and then calculate the results for the
above mentioned formulas for each paragraph.
Then it calculates its standard deviation and average values.

The end goal is to provide a widely known metric for readability which can help the llm judge the 
readability of the text better.
"""
import numpy as np
import textstat

import statistics
from repetition_detection import tokenize_text_into_sentences

def analyze_readability_variance(text: str) -> dict:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Fallback: if fewer than 2 paragraphs, try splitting into chunks of 3 sentences
    if len(paragraphs) <= 1:
        sentences = tokenize_text_into_sentences(text)
        if len(sentences) >= 6:  # Need at least 2 chunks of 3
            # Chunk sentences into groups of 3
            chunk_size = 3
            paragraphs = [
                " ".join(sentences[i:i + chunk_size])
                for i in range(0, len(sentences), chunk_size)
            ]

    if len(paragraphs) <= 1:
        flesch_score = textstat.flesch_reading_ease(text)
        grade_level = textstat.flesch_kincaid_grade(text)
        return {
            "status": "insufficient_data",
            "paragraph_count": len(paragraphs),
            "reading_ease_std": 0.0,
            "grade_level_std": 0.0,
            "avg_reading_ease": flesch_score,
            "avg_grade_level": grade_level,
            "scores": []
        }

    ease_scores = []
    grade_scores = []

    for p in paragraphs:
        ease = textstat.flesch_reading_ease(p)
        grade = textstat.flesch_kincaid_grade(p)
        
        ease_scores.append(ease)
        grade_scores.append(grade)

    ease_std = float(np.std(ease_scores))
    grade_std = float(np.std(grade_scores))
    
    avg_ease = float(np.mean(ease_scores))
    avg_grade = float(np.mean(grade_scores))

    result = {
        "status": "success",
        "paragraph_count": len(paragraphs),
        "reading_ease_std": round(ease_std, 2),
        "grade_level_std": round(grade_std, 2),
        "avg_reading_ease": round(avg_ease, 2),
        "avg_grade_level": round(avg_grade, 2),
        "uniformity_score": "High" if ease_std < 5.0 else "Low"
    }

    return result

import numpy as np
import textstat

def analyze_readability_variance(text: str) -> dict:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
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

"""
This file has the goal of counting the words in each sentence and then using the built-in statistics module
calculating the standard deviation of the word counts.

Then it measures the standard deviation on a scale to determine if the sentence length is too uniform or
is it too bursty.
"""
import statistics
from repetition_detection import tokenize_text_into_sentences

__all__ = ['uniform_sentence_check']

LOW_VARIANCE_THRESHOLD = 3.0
HIGH_VARIANCE_THRESHOLD = 6.5

RESULT_TEMPLATES = {
    'insufficient': ('Insufficient amount of sentences to run a test.', 'Neutral', 'white'),
    'uniform': ('Highly Uniform Sentences', 'Likely AI', 'red'),
    'moderate': ('Moderately Varied Sentences', 'Neutral', 'yellow'),
    'burstive': ('Highly Burstive Sentences', 'Likely human', 'green'),
}


def _build_result(score: float, template_key: str) -> dict:
    judgment, signal, color = RESULT_TEMPLATES[template_key]
    return {
        'score': score,
        'judgment': judgment,
        'signal': signal,
        'color': color
    }


def _classify_variance(std_dev: float) -> str:
    if std_dev < LOW_VARIANCE_THRESHOLD:
        return 'uniform'
    elif std_dev < HIGH_VARIANCE_THRESHOLD:
        return 'moderate'
    return 'burstive'


def uniform_sentence_check(text: str) -> dict:
    from repetition_detection import tokenize_text
    sentences = tokenize_text_into_sentences(text)
    words_per_sentence = [len(tokenize_text(sentence)) for sentence in sentences]

    if len(words_per_sentence) <= 1:
        return _build_result(0, 'insufficient')

    mean_length = statistics.mean(words_per_sentence)
    
    # Needs at least two points to calculate sample standard deviation
    if len(words_per_sentence) < 2:
        std_dev = 0.0
    else:
        std_dev = statistics.stdev(words_per_sentence)
    
    cv = (std_dev / mean_length) if mean_length > 0 else 0.0
    
    # Update thresholds based on CV: 
    # uniform < 0.2, moderate < 0.45, burstive > 0.45
    if cv < 0.20:
        category = 'uniform'
    elif cv < 0.45:
        category = 'moderate'
    else:
        category = 'burstive'

    return _build_result(round(cv, 2), category)
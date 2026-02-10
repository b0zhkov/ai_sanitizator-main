import numpy as np
from repetition_detection import tokenize_text_into_sentences

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
    sentences = tokenize_text_into_sentences(text)
    words_per_sentence = [len(sentence.split()) for sentence in sentences]

    if len(words_per_sentence) <= 1:
        return _build_result(0, 'insufficient')

    std_dev = round(np.std(words_per_sentence), 2)
    category = _classify_variance(std_dev)
    return _build_result(std_dev, category)
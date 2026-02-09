import sys
import nltk
import normalizator
import strip_inv_chars
from nltk.tokenize import word_tokenize, sent_tokenize

nltk.download('punkt')
nltk.download('punkt_tab')
sys.path.append('../text_sanitization')


def get_clean_text(raw_text: str) -> str:

    sanitized = strip_inv_chars.sanitize_text(raw_text)
    clean_text = normalizator.normalize_punctuation(sanitized)
    return clean_text


def tokenize_text_into_words(text: str) -> list[str]:
    """Tokenizes text into individual words."""
    return word_tokenize(text)


def tokenize_text_into_sentences(text: str) -> list[str]:
    """Tokenizes text into sentences."""
    return sent_tokenize(text)
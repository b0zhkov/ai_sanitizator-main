import sys
import os
import nltk
import clean_text_getter
from nltk.tokenize import word_tokenize, sent_tokenize

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

nltk.download('punkt')
nltk.download('punkt_tab')

def get_clean_text(raw_text: str) -> str:
    return clean_text_getter.get_clean_text_from_string(raw_text)


def tokenize_text_into_words(text: str) -> list[str]:
    return word_tokenize(text)


def tokenize_text_into_sentences(text: str) -> list[str]:
    return sent_tokenize(text)
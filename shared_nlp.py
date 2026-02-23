"""
Shared Spacy NLP model loader.

This module provides a single, lazily-loaded Spacy model instance that is shared
across all modules that need NLP processing (hedging_filler_detector, imperfection_injector).
This avoids loading the same ~50MB model multiple times into memory.
"""
import spacy
import spacy.cli

_nlp_full = None
_nlp_light = None
_nlp_tagger = None


def get_nlp_full():
    """Returns a full en_core_web_sm model (all components enabled)."""
    global _nlp_full
    if _nlp_full is None:
        try:
            _nlp_full = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            _nlp_full = spacy.load("en_core_web_sm")
    return _nlp_full

def get_nlp_tagger():
    """Returns a model with NER, textcat, entity_linker disabled, but keeps tagger and lemmatizer."""
    global _nlp_tagger
    if _nlp_tagger is None:
        try:
            _nlp_tagger = spacy.load("en_core_web_sm", disable=["ner", "textcat", "entity_linker"])
        except OSError:
            spacy.cli.download("en_core_web_sm")
            _nlp_tagger = spacy.load("en_core_web_sm", disable=["ner", "textcat", "entity_linker"])
    return _nlp_tagger


def get_nlp_light():
    """Returns a lightweight en_core_web_sm model (NER, lemmatizer, textcat disabled)."""
    global _nlp_light
    if _nlp_light is None:
        try:
            _nlp_light = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "textcat", "entity_linker"])
        except OSError:
            spacy.cli.download("en_core_web_sm")
            _nlp_light = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "textcat", "entity_linker"])
    return _nlp_light

"""
Shared Spacy NLP model loader.

This module provides a single, lazily-loaded Spacy model instance that is shared
across all modules that need NLP processing (hedging_filler_detector, imperfection_injector).
This avoids loading the same ~50MB model multiple times into memory.

There are 3 different functions which load different parts of the en_core_web_sm model.
The idea is to not load unnecessary heavy components for lightweight tasks.

NOTE: spacy is imported lazily inside each function (not at module level) so that
importing this module does not trigger the heavy spacy → thinc → blis chain.
This is critical for serverless platforms like Vercel where blis may not be
available at cold-start time.
"""

# singletons — each variant loads the model once and reuses it everywhere
_nlp_full = None
_nlp_light = None
_nlp_tagger = None


def _load_model(**kwargs):
    """Import spacy on first use and load the model, downloading if needed."""
    import spacy
    import spacy.cli

    try:
        return spacy.load("en_core_web_sm", **kwargs)
    except OSError:
        spacy.cli.download("en_core_web_sm")
        return spacy.load("en_core_web_sm", **kwargs)


def get_nlp_full():
    global _nlp_full
    if _nlp_full is None:
        _nlp_full = _load_model()
    return _nlp_full


def get_nlp_tagger():
    global _nlp_tagger
    if _nlp_tagger is None:
        _nlp_tagger = _load_model(disable=["ner", "textcat", "entity_linker"])
    return _nlp_tagger


def get_nlp_light():
    global _nlp_light
    if _nlp_light is None:
        _nlp_light = _load_model(disable=["ner", "lemmatizer", "textcat", "entity_linker"])
    return _nlp_light


def clear_nlp_models():
    global _nlp_full, _nlp_light, _nlp_tagger
    _nlp_full = None
    _nlp_light = None
    _nlp_tagger = None

import sys
import spacy
nlp_en = spacy.load("en_core_web_sm")
nlp_multi = spacy.load("xx_sent_ud_sm")
print("Both models loaded successfully!")
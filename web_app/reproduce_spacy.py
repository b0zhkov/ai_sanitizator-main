import sys
print("Importing spacy...")
try:
    import spacy
    print("SUCCESS: spacy")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"FAILED: spacy - {e}")
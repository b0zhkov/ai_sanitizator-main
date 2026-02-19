"""
The repeating headings detector finds duplicate or repetitive headers.

The main purpose is to catch structural repetition which might indicate
looping or poor document structure.

It achieves this by:
1. extracting lines that look like headings (short, capitalized, no period).
2. checking for duplicate occurrences of these heading strings.

The end goal is to ensure the document structure is unique and logical.
"""
import sys
import clean_text_getter
import repetition_detection



def get_sentences(text: str) -> list[str]:
    clean_text = clean_text_getter.get_clean_text_from_string(text)
    return repetition_detection.tokenize_text_into_sentences(clean_text)


def is_heading(line: str) -> bool:

    line = line.strip()
    
    if not line or len(line) >= 100 or not line[0].isupper() or line.endswith('.'):
        return False
    
    return True

def get_repeating_headings(text: str) -> list[str]:

    clean_text = clean_text_getter.get_clean_text_from_string(text)
    lines = clean_text.split('\n')
    
    seen_headings = {}
    repeated_headings = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if is_heading(line):
            normalized = line.lower()
            
            if normalized in seen_headings:
                if normalized not in [h.lower() for h in repeated_headings]:
                    repeated_headings.append(line)
            else:
                seen_headings[normalized] = line
    
    return repeated_headings
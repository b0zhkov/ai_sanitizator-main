"""
Verification script for sanitization pipeline.
"""
import sys
import os

# Setup path to mimic main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import _paths

from text_sanitization.changes_log import changes_log

def test_sanitization():
    print("Running Sanitization Verification...")
    
    # Test Case 1: HTML + PII + Whitespace
    input_text = """
    <div>
        <h1>  Hello   World!  </h1>
        <p>Contact me at test@example.com</p>
        <script>bad_code()</script>
        
        
        Check out https://google.com
    </div>
    """
    
    print(f"\n[Test 1 Input]:\n{input_text}")
    
    clean_text, changes = changes_log.build_changes_log(input_text)
    
    print(f"\n[Test 1 Output]:\n{clean_text}")
    print("\n[Changes Log]:")
    for change in changes:
        print(f"- {change.description}")
        
    # Assertions
    assert "<div>" not in clean_text, "HTML tags should be stripped"
    assert "bad_code" not in clean_text, "Script content should be stripped"
    assert "test@example.com" not in clean_text, "Email should be redacted"
    assert "[EMAIL]" in clean_text, "Email placeholder should be present"
    assert "https://google.com" not in clean_text, "URL should be redacted"
    assert "  Hello   World!" not in clean_text, "Whitespace should be collapsed"
    assert "\n\n\n" not in clean_text, "Excessive newlines should be collapsed"
    
    print("\n✅ Verification Passed!")

if __name__ == "__main__":
    test_sanitization()

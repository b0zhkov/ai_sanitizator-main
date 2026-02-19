import unittest
import sys
import os
from unittest.mock import MagicMock

# Add project root and text-analysis to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'text-analysis')))

# Mock broken dependencies before importing modules
# Ensure we DO NOT mock the modules we are testing
if 'llm_validator' in sys.modules: del sys.modules['llm_validator']
if 'post_humanizer' in sys.modules: del sys.modules['post_humanizer']
if 'rewriting_agent' in sys.modules: del sys.modules['rewriting_agent']

sys.modules['rewriting_agent'] = MagicMock()
sys.modules['document_loading'] = MagicMock()
sys.modules['spacy'] = MagicMock()
sys.modules['shared_nlp'] = MagicMock()
sys.modules['llm_info'] = MagicMock()
sys.modules['repetition_detection'] = MagicMock()
# sys.modules['repeating_headings'] = MagicMock() # needed for other test? No, other test imports it. 
# But wait, test_repeating_headings_rename imports it. If I mock it here, that test might fail or use mock.
# I should mock it inside the test_csv_caching or just mock it globally and unmock it for that specific test?
# Or just let it load since I verified it works?
# I'll let repeating_headings load for now as I tested it works. 
# But uniform_sentence_len etc might be broken.
sys.modules['uniform_sentence_len'] = MagicMock()
sys.modules['readability_analysis'] = MagicMock()
sys.modules['verb_freq'] = MagicMock()
sys.modules['punctuation_checker'] = MagicMock()

# Mock shared_nlp.get_nlp_full to return a mock object
mock_nlp = MagicMock()
sys.modules['shared_nlp'].get_nlp_full.return_value = mock_nlp

class TestMinorRefactor(unittest.TestCase):

    def test_repeating_headings_rename(self):
        print("\nTesting repeating_headings rename...")
        try:
            import repeating_headings
            print("Successfully imported repeating_headings")
            self.assertTrue(hasattr(repeating_headings, 'get_repeating_headings'))
        except ImportError:
            self.fail("Could not import repeating_headings. Rename failed or not in path.")

    def test_hedging_dead_code_removal(self):
        print("\nTesting hedging_filler_detector dead code removal...")
        try:
            import hedging_filler_detector
            if hasattr(hedging_filler_detector, 'load_and_clean_text'):
                self.fail("load_and_clean_text still exists in hedging_filler_detector")
            if hasattr(hedging_filler_detector, 'content_words'):
                self.fail("content_words global still exists in hedging_filler_detector")
            print("Dead code removed successfully.")
        except ImportError:
            self.fail("Could not import hedging_filler_detector")

    def test_csv_caching(self):
        print("\nTesting CSV caching mechanism...")
        try:
            # Import directly since text-analysis is in path
            import llm_validator
            import ai_phrase_detector
            
            # Reset mocks if needed or just check if variables exist
            # We can't easily check internal state without exposing it, 
            # but we can check if the variables are defined at module level
            # (which I did not do, I kept them internal/global).
            # Actually I defined them as globals in the module.
            
            print(f"llm_validator attributes: {dir(llm_validator)}")
            # Check llm_validator cache
            self.assertTrue(hasattr(llm_validator, '_excess_words_cache'), "llm_validator missing _excess_words_cache")
            
            # Check ai_phrase_detector cache
            self.assertTrue(hasattr(ai_phrase_detector, '_ai_phrases_cache'), "ai_phrase_detector missing _ai_phrases_cache")
            
            print("CSV cache variables present.")
        except ImportError as e:
            import traceback
            traceback.print_exc()
            self.fail(f"Import failed during cache test: {e}")

    def test_post_humanizer_config(self):
        print("\nTesting post_humanizer config refactor...")
        try:
            # post_humanizer is in text-rewriting, which we added to sys.path
            import post_humanizer
            print(f"post_humanizer attributes: {dir(post_humanizer)}")
            # Ensure globals are gone
            self.assertFalse(hasattr(post_humanizer, 'VOCABULARY_SWAP_RATE'), "VOCABULARY_SWAP_RATE global still exists")
            print("Global state removed from post_humanizer.")
        except ImportError:
             self.fail("Could not import post_humanizer")

if __name__ == '__main__':
    unittest.main()

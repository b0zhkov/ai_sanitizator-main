import sys
import os
import json
import traceback
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'text-analysis')))

import llm_info
from prompts import rewriting_prompt

class RewritingAgent:

    def __init__(self):
        self.llm = llm_info.llm
        self.chain = (rewriting_prompt | self.llm).with_retry(stop_after_attempt=3)

    def _unused_rewrite_sync(self, text: str, analysis: dict) -> str:
        try:
            analysis_str = json.dumps(analysis, indent=2)
            
            response = self.chain.invoke({
                "text": text,
                "analysis": analysis_str
            })
            
            if not response:
                return "Error: No response from LLM."
            
            raw_content = str(response.content) if response.content is not None else ""
            
            match = re.search(r'<final_text>(.*?)</final_text>', raw_content, re.DOTALL)
            if match:
                return match.group(1).strip()
            
            return raw_content
            
        except Exception as e:
            print(f"Rewriting Error: {str(e)}")
            traceback.print_exc()
            return f"Error during rewriting: {str(e)}"

    def stream_rewrite(self, text: str, analysis: dict):
        has_yielded_content = False
        
        buffer = ""
        found_start_tag = False
        start_tag = "<final_text>"
        end_tag = "</final_text>"
        
        try:
            analysis_str = json.dumps(analysis, indent=2)
            
            for chunk in self.chain.stream({
                "text": text,
                "analysis": analysis_str
            }):
                if chunk is not None and chunk.content is not None:
                    if isinstance(chunk.content, str) and chunk.content:
                        
                        buffer += chunk.content
                        
                        if not found_start_tag:
                            start_match = re.search(re.escape(start_tag), buffer)
                            if start_match:
                                found_start_tag = True
                                buffer = buffer[start_match.end():]
                            elif len(buffer) > 100:
                                found_start_tag = True
                                buffer = buffer.lstrip()
                        
                        if found_start_tag:
                            end_match = re.search(re.escape(end_tag), buffer)
                            if end_match:
                                final_chunk = buffer[:end_match.start()]
                                if final_chunk:
                                    has_yielded_content = True
                                    yield final_chunk
                                return
                            
                            safe_threshold = len(end_tag) + 5
                            if len(buffer) > safe_threshold:
                                to_yield = buffer[:-safe_threshold]
                                buffer = buffer[-safe_threshold:]
                                if to_yield:
                                    has_yielded_content = True
                                    yield to_yield

            if found_start_tag and buffer:
                end_match = re.search(re.escape(end_tag), buffer)
                if end_match:
                    yield buffer[:end_match.start()]
                else:
                    yield buffer
                    
        except Exception as e:
            print(f"Streaming Error: {str(e)}")
            traceback.print_exc()
            
            if not has_yielded_content:
                yield f"[Error: Failed to generate text. Check logs.]"
            else:
                print("Silently suppressed error after partial generation.")

rewriting_agent = RewritingAgent()
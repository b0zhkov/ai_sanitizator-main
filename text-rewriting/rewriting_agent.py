"""
This file is responsible for the actual rewriting of the text.
Firstly it initializes the LLM and creates a chain of events.
That chain being to first get the prompt and then give it to the LLM.
There is a safety measure against infinite loading which is to stop the rewriting process
after 3 failed attempts.

Then the rewriting process starts.
In the prompts.py file I have explicitly asked the llm to wrap its output inside <final_text> tags which keeps
the generic "Sure! Here is..." message out of what the user sees for a professional look.

The stream_rewrite function is the one responsible for yielding the output of the LLM in chunks.
It uses a buffer to store the output of the LLM and yields it as soon as it is safely confirmed
to be part of the final text (maintaining a small buffer to handle the closing tag).
This is used with the purpose to show the user, the text is being rewritten in real time,
rather than a lengthy loading screen.
"""

import json
import traceback
import re

import _paths  # noqa: E402 — centralised path setup

import llm_info
from prompts import rewriting_prompt

class RewritingAgent:

    def __init__(self):
        self.llm = llm_info.llm
        self.chain = (rewriting_prompt | self.llm).with_retry(stop_after_attempt=3)

    async def stream_rewrite(self, text: str, analysis: dict):
        has_yielded_content = False
        
        buffer = ""
        found_start_tag = False
        start_tag = "<final_text>"
        end_tag = "</final_text>"
        
        try:
            analysis_str = json.dumps(analysis, indent=2)
            
            async for chunk in self.chain.astream({
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
import sys
import os
import json
from langchain_core.output_parsers import StrOutputParser

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add text-analysis directory to path to allow importing llm_info
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'text-analysis')))

import llm_info
from prompts import rewriting_prompt

class RewritingAgent:

    def __init__(self):
        self.llm = llm_info.llm
        self.output_parser = StrOutputParser()
        self.chain = rewriting_prompt | self.llm | self.output_parser

    def rewrite(self, text: str, analysis: dict) -> str:
        try:
            analysis_str = json.dumps(analysis, indent=2)
            
            return self.chain.invoke({
                "text": text,
                "analysis": analysis_str
            })
        except Exception as e:
            return f"Error during rewriting: {str(e)}"

    def stream_rewrite(self, text: str, analysis: dict):
        try:
            analysis_str = json.dumps(analysis, indent=2)
            
            # Use chain.stream to get a generator of chunks
            for chunk in self.chain.stream({
                "text": text,
                "analysis": analysis_str
            }):
                yield chunk
        except Exception as e:
            yield f"Error during rewriting: {str(e)}"

rewriting_agent = RewritingAgent()

import os
import sys
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
import hedging_filler_detector as hedging
import repetition_detection as repetition
import uniform_sentence_len as uniform
import llm_info

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CritiqueSchema(BaseModel):
    validation_of_stats: dict = Field(description="Verification of the algorithmically detected hedging, repetition, and variance.")
    stylistic_issues: list[str] = Field(description="Specific AI-like stylistic issues found in the text.")
    recommended_actions: list[str] = Field(description="Steps to take during the rewriting phase.")
    overall_score: int = Field(description="Quality score from 1-10.")

def validate_text(text: str) -> dict:
    stats = {}
    
    stats['hedging'] = _analyze_hedging(text)
    stats['repetition'] = _analyze_repetition(text)
    stats['sentence_variance'] = _analyze_sentence_variance(text)

    llm_response = _get_llm_critique(text, stats)
    
    return {
        "statistical_metrics": stats,
        "llm_critique": llm_response
    }

def _analyze_hedging(text: str) -> dict:
    try:
        _, hedging_stats = hedging.analyze_and_filter_out(text)
        return hedging_stats
    except Exception as e:
        return {"error": str(e)}

def _analyze_repetition(text: str) -> dict:
    try:
        repeats = repetition.get_repeating_keyphrases(text)
        return {
            "count": len(repeats), 
            "samples": repeats[:5]
        }
    except Exception as e:
        return {"error": str(e)}

def _analyze_sentence_variance(text: str) -> dict:
    try:
        return uniform.uniform_sentence_check(text)
    except Exception as e:
        return {"error": str(e)}

def _get_llm_critique(text: str, stats: dict) -> dict:
    parser = JsonOutputParser(pydantic_object=CritiqueSchema)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional editor and text analyst. {format_instructions}"),
        ("human", "Critique the following text based on these algorithmic hints: {stats_json}\n\nText: {text_content}")
    ])
    
    chain = prompt | llm_info.llm | parser
    
    try:
        return chain.invoke({
            "stats_json": json.dumps(stats),
            "text_content": text[:4000],
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        return {
            "error": "Failed to get LLM critique",
            "details": str(e)
        }
"""
This file serves a validation layer for all other analysis algorithms.

It does that by feeding the mathematical data gathered from the other files in the folder 
(ex. hedging_filler_detector.py, repetition_detection.py, etc.) to the imported LLM.

Based on that data the LLM provides a critique, returns it as a json file and also calculates
a score from 1.0 to 10.0 (the lower the more human the text is).
"""
import os
import sys
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import csv

import _paths  # noqa: E402 — centralised path setup
import hedging_filler_detector as hedging
import repetition_detection as repetition
import uniform_sentence_len as uniform
import readability_analysis
import verb_freq
import punctuation_checker
import ai_phrase_detector
import llm_info


class CritiqueSchema(BaseModel):
    validation_of_stats: dict = Field(description="Verification of the algorithmically detected hedging, repetition, variance, readability, verb usage, and punctuation.")
    stylistic_issues: list[str] = Field(description="Specific AI-like stylistic issues found in the text.")
    recommended_actions: list[str] = Field(description="Steps to take during the rewriting phase.")
    ai_score: float = Field(description="Score from 1.0 (Human-written) to 10.0 (AI-generated). Use decimals for precision.")

def _collect_stats(text: str) -> dict:
    return {
        'hedging': _analyze_hedging(text),
        'repetition': _analyze_repetition(text),
        'sentence_variance': _analyze_sentence_variance(text),
        'readability': _analyze_readability(text),
        'verb_frequency': _analyze_verb_frequency(text),
        'punctuation_profile': _analyze_punctuation(text),
        'flagged_words': _check_excess_words(text),
        'ai_phrases': _analyze_ai_phrases(text),
    }


def collect_stats(text: str) -> dict:
    return _collect_stats(text)


def get_llm_critique(text: str, stats: dict) -> dict:
    return _get_llm_critique(text, stats)


def validate_text(text: str) -> dict:
    stats = _collect_stats(text)
    llm_response = _get_llm_critique(text, stats)

    return {
        "statistical_metrics": stats,
        "llm_critique": llm_response
    }


def verify_metrics_only(text: str) -> dict:
    stats = _collect_stats(text)

    return {
        "statistical_metrics": stats,
        "llm_critique": None
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

def _analyze_readability(text: str) -> dict:
    try:
        return readability_analysis.analyze_readability_variance(text)
    except Exception as e:
        return {"error": str(e)}

def _analyze_verb_frequency(text: str) -> dict:
    try:
        return verb_freq.analyze_verb_frequency(text)
    except Exception as e:
        return {"error": str(e)}

def _analyze_punctuation(text: str) -> dict:
    try:
        return punctuation_checker.analyze_punctuation_structure(text)
    except Exception as e:
        return {"error": str(e)}

def _check_excess_words(text: str) -> dict:
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'excess_words.csv')
        
        flagged = []
        text_lower = text.lower()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            excess_list = [word.strip().lower() for row in reader for word in row if word.strip()]
            
        for word in excess_list:
            if f" {word} " in text_lower: 
                flagged.append(word)
                
        return {"count": len(flagged), "words": flagged[:20]}
    except Exception as e:
        return {"error": f"Failed to check excess words: {str(e)}"}

def _analyze_ai_phrases(text: str) -> dict:
    try:
        return ai_phrase_detector.analyze_ai_phrases(text)
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
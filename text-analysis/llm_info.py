"""
This file is responsible for initializing the LLM and tinker with its core parameters.
It does that via the Langchain library.
There is also a dedicated .env file to hide sensitive information such as API keys.
"""
import os
from dotenv import load_dotenv
from langchain_cloudflare import ChatCloudflareWorkersAI

load_dotenv()

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatCloudflareWorkersAI(
            account_id=os.getenv("CF_ACCOUNT_ID"),
            api_token=os.getenv("CF_AI_API_KEY"),
            model="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            temperature=0.8,
            top_p=0.95,
            max_tokens=4096
        )
    return _llm

def __getattr__(name):
    if name == "llm":
        return get_llm()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
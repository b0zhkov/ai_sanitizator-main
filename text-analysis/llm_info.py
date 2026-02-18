"""
This file is responsible for initializing the LLM and tinker with its core parameters.
It does that via the Langchain library.
There is also a dedicated .env file to hide sensitive information such as API keys.
"""
import os
from dotenv import load_dotenv
from langchain_cloudflare import ChatCloudflareWorkersAI

load_dotenv()

llm = ChatCloudflareWorkersAI(
    account_id=os.getenv("CF_ACCOUNT_ID"),
    api_token=os.getenv("CF_AI_API_KEY"),
    model="@cf/meta/llama-3-8b-instruct",
    temperature=0.8,
    top_p=0.95,
    max_tokens=4096
)
"""LLM configuration module for Cloudflare Workers AI integration."""
import os
from dotenv import load_dotenv
from langchain_cloudflare import CloudflareWorkersAI

# Load environment variables from .env file
load_dotenv()

# Initialize the Cloudflare Workers AI LLM
llm = CloudflareWorkersAI(
    account_id=os.getenv("CF_ACCOUNT_ID"),
    api_token=os.getenv("CF_AI_API_KEY"),
    model="@cf/meta/llama-3.1-8b-instruct"
)
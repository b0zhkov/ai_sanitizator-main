import os
from dotenv import load_dotenv
from langchain_cloudflare import ChatCloudflareWorkersAI

load_dotenv()

llm = ChatCloudflareWorkersAI(
    account_id=os.getenv("CF_ACCOUNT_ID"),
    api_token=os.getenv("CF_AI_API_KEY"),
    model="@cf/meta/llama-3.1-8b-instruct",
    temperature=0.8,
    top_p=0.95,
    max_tokens=2048
)
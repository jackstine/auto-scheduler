"""Simple test of OpenRouter via LangChain's ChatOpenAI."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="openrouter/aurora-alpha",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
)

response = llm.invoke("Hello! Please respond with a short greeting. My name is Jake, who are you, what would you like to be called?")
print(response.content)

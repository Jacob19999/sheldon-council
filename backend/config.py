"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers (free models)
COUNCIL_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",  # Meta's Llama 3.1 8B - fast and capable
    "mistralai/mistral-7b-instruct",  # Mistral 7B - efficient and reliable
    "openchat/openchat-3.5-0106",  # OpenChat 3.5 - fine-tuned for conversations
    "google/gemma-2-9b-it",  # Google Gemma 2 9B - multilingual and versatile
    "qwen/qwen-2.5-7b-instruct",  # Qwen 2.5 7B - strong reasoning capabilities
]

# Chairman model - synthesizes final response (using a free model)
CHAIRMAN_MODEL = "meta-llama/llama-3.1-8b-instruct"  # Llama 3.1 8B for synthesis

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

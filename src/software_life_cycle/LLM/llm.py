from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

# Load environment variables from .env file
load_dotenv()

# Fetch API Key (Ensure it's not None)
api_key = os.getenv('GROQ_API_KEY')

if api_key is None:
    raise ValueError("Error: GROQ_API_KEY is missing! Please set it in the .env file.")

os.environ['GROQ_API_KEY'] = api_key

# llm = ChatGroq(model = 'llama-3.3-70b-versatile', api_key = api_key)
llm = ChatGroq(model = 'llama-3.2-90b-vision-preview', api_key = api_key)
llm_docs = ChatGroq(model = 'gemma2-9b-it', api_key=api_key)
# llm_coder = ChatGroq(model = 'llama3-8b-8192', api_key=api_key)
llm_coder = ChatGroq(model = 'qwen-2.5-coder-32b', api_key=api_key)

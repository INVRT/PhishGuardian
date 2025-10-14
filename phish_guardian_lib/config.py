import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini LLM
# This single instance will be imported and used by all agents.
# Updated to use the Gemini-2.0-Flash model.
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
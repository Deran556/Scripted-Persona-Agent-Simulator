from dotenv import load_dotenv
import os

load_dotenv()

# API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

# Generation Config
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 512))
TOP_P = float(os.getenv("TOP_P", 0.95))
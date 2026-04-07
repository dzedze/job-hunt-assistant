import os
from dotenv import load_dotenv

load_dotenv()

JOBS_API_KEY = os.getenv("JOBS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JOBS_API_HOST = os.getenv("JOBS_API_HOST")

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

JOBS_API_KEY = os.getenv("JOBS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JOBS_API_HOST = os.getenv("JOBS_API_HOST")

BASE_DIR = Path(".")  # current directory
PARENT_DIR = (
    BASE_DIR.parent.parent
)  # parent of the current directory, which is the root of the project

SAVED_JOBS_DIR = (
    PARENT_DIR / "data" / "jobs" / "saved"
)  # directory to save jobs
TEMP_JOBS_DIR = (
    PARENT_DIR / "data" / "jobs" / "temp"
)  # temporary directory for fetched jobs
COVER_LETTERS_DIR = (
    PARENT_DIR / "data" / "cover_letters"
)  # directory to save cover letters
JOBS_REPORTS_DIR = PARENT_DIR / "data" / "reports"
JOBS_REPORTS_PATH = (
    JOBS_REPORTS_DIR / "report.md"
)  # path to the jobs report
RESUME_PATH = (
    PARENT_DIR / "data" / "resume" / "resume.pdf"
)  # path to the resume
TEMP_FETCHED_JOBS_PATH = TEMP_JOBS_DIR / "temp_fetched_jobs.json"

# create directories if they do not exists
SAVED_JOBS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_JOBS_DIR.mkdir(parents=True, exist_ok=True)
COVER_LETTERS_DIR.mkdir(parents=True, exist_ok=True)
RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)

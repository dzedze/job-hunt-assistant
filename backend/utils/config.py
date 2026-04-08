import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

JOBS_API_KEY = os.getenv("JOBS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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
CUSTOMIZED_RESUMES_DIR = (
    PARENT_DIR / "data" / "customized_resumes"
)  # directory to save customized resumes
CUSTOMIZED_RESUMES_PATH = (
    CUSTOMIZED_RESUMES_DIR / "customized_resume.md"
)  # path to the customized resume
CUSTOMIZED_RESUME_PDF_PATH = (
    CUSTOMIZED_RESUMES_DIR / "customized_resume.pdf"
)
CUSTOMIZED_COVER_LETTER_PDF_PATH = (
    CUSTOMIZED_RESUMES_DIR / "cover_letter.pdf"
)
CUSTOMIZED_MESSAGES_DIR = (
    PARENT_DIR / "data" / "customized_messages"
)  # directory to save customized messages
CUSTOMIZED_MESSAGES_PATH = (
    CUSTOMIZED_MESSAGES_DIR / "customized_message.txt"
)  # path to the customized message
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
CUSTOMIZED_RESUMES_DIR.mkdir(parents=True, exist_ok=True)
CUSTOMIZED_MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)

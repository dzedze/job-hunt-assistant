from crewai import Crew, Process
from pypdf import PdfReader
from backend.agents.jd_analyst import (
    get_jd_analyst_agent,
    create_jd_analysis_task,
)
from backend.agents.resume_cl_agent import (
    get_resume_cl_agent,
    create_resume_cl_task,
)

from backend.utils import config as cfg
from backend.apis.jobs_api import fetch_jobs


def load_resume(path=cfg.RESUME_PATH):
    """Load text content from a PDF resume file."""
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except FileNotFoundError:
        print(f"Resume file not found at {path}")
        return ""
    except Exception as e:
        print(f"Error reading resume: {e}")
        return ""


def run_pipeline():
    # Fetch jobs posts
    job_posts = fetch_jobs("Data Scientist", "Toronto")
    if not job_posts:
        print("No job posts found. Exiting pipeline.")
        return

    # Extract job description from the first result
    job_data = job_posts[0]

    job_description = job_data.get("description", "")
    # print(job_description)
    if not job_description:
        print(
            "No job description found in the first job post. Exiting pipeline."
        )
        return

    # Load resume
    resume_text = load_resume()

    # Initialize agents
    jd_agent = get_jd_analyst_agent()
    resume_agent = get_resume_cl_agent()

    # Create tasks
    jd_task = create_jd_analysis_task(jd_agent, job_description)
    resume_task = create_resume_cl_task(
        resume_agent, job_description, resume_text
    )

    # Create and run the crew
    crew = Crew(
        agents=[jd_agent, resume_agent],
        tasks=[jd_task, resume_task],
        process=Process.sequential,
    )

    results = crew.kickoff()

    print("\n=== FINAL OUTPUT ===\n")
    print(results)


if __name__ == "__main__":
    run_pipeline()

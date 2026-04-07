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

from backend.agents.messaging_agent import (
    get_messaging_agent,
    create_messaging_task,
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

    agency_name = job_data.get("company", "the company")
    job_title = job_data.get("title", "the role")

    # Load resume & user bio
    resume_text = load_resume()
    user_bio = """
    Data science professional with 7+ years of software engineering experience building scalable, production-grade systems. Seeking Data Scientist or Machine Learning Engineer or AI Engineer roles to deliver scalable, data-driven business impact
    """
    # Initialize agents
    jd_agent = get_jd_analyst_agent()
    resume_agent = get_resume_cl_agent()
    message_agent = get_messaging_agent()

    # Create tasks
    jd_task = create_jd_analysis_task(jd_agent, job_description)
    resume_task = create_resume_cl_task(
        resume_agent, job_description, resume_text
    )

    message_task = create_messaging_task(
        message_agent,
        job_description,
        agency_name,
        job_title,
        user_bio,
    )

    # Create and run the crew
    crew = Crew(
        agents=[jd_agent, resume_agent, message_agent],
        tasks=[jd_task, resume_task, message_task],
        process=Process.sequential,
    )

    results = crew.kickoff()

    print("\n=== FINAL OUTPUT ===\n")
    print(results)


if __name__ == "__main__":
    run_pipeline()

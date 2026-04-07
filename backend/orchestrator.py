from crewai import Crew, Process
from backend.agents.jd_analyst import (
    get_jd_analyst_agent,
    create_jd_analysis_task,
)
from backend.apis.jobs_api import fetch_jobs


def run_pipeline():
    # Fetch jobs posts
    job_posts = fetch_jobs("Data Scientist", "Toronto")
    if not job_posts:
        print("No job posts found. Exiting pipeline.")
        return

    # Extract job description from the first result
    job_data = job_posts[0]

    job_description = job_data.get("description", "")
    print(job_description)
    if not job_description:
        print(
            "No job description found in the first job post. Exiting pipeline."
        )
        return

    # Initialize agent and task
    jd_agent = get_jd_analyst_agent()
    jd_task = create_jd_analysis_task(jd_agent, job_description)

    # Create and run the crew
    crew = Crew(
        agents=[jd_agent],
        tasks=[jd_task],
        process=Process.sequential,
    )

    results = crew.kickoff()

    print("\n=== FINAL OUTPUT ===\n")
    print(results)


if __name__ == "__main__":
    run_pipeline()

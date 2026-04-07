from crewai import Agent, Task
from langchain_google_genai import ChatGoogleGenerativeAI
import utils.config as cfg

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    api_key=cfg.GEMINI_API_KEY,
)


def get_jd_analyst_agent() -> Agent:
    return Agent(
        role="JD Analyst",
        goal="Understand and summarize job postings",
        backstory="You are an expert in job market analysis with a deep understanding of job descriptions and requirements. You have experience in analyzing job postings to extract key information and summarize it effectively.",
        llm=llm,
        verbose=True,
    )


def create_jd_analysis_task(agent, job_description) -> Task:
    return Task(
        description=f"""
        Analyze the following job posting and extract:
        - A summary of the role
        - Key skills required
        - Any specific qualifications or eligibility requirements or experience needed
        \n\nJob Description:\n{job_description}
        """,
        expected_output="A structured markdown summary containing sections for Qualifications, Required Skills, and Responsibilities.",
        agent=agent,
        output_file=cfg.JOBS_REPORTS_PATH,
    )

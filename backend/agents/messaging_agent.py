from crewai import Agent, Task
from crewai.llm import LLM
from backend.utils import config as cfg

llm = LLM(
    model="gpt-4o",
    temperature=0.2,
    api_key=cfg.OPENAI_API_KEY,
)

default_user_bio = """
    Data science professional with 7+ years of software engineering experience building scalable, production-grade systems. Seeking Data Scientist or Machine Learning Engineer or AI Engineer roles to deliver scalable, data-driven business impact
    """


def get_messaging_agent() -> Agent:
    return Agent(
        role="Outreach & Messaging Writer",
        goal="Draft personalized messages for job outreach.",
        backstory="You're a professional career coach skilled in writing effective cold emails and outreach messages for job seekers in tech.",
        llm=llm,
        verbose=True,
    )


def create_messaging_task(
    agent,
    job_summary,
    agency_name,
    job_title,
    user_bio=default_user_bio,
) -> Task:
    return Task(
        description=f"""
        Write a concise and compelling outreach message that the candidate could send to someone at {agency_name}, expressing interest in the job described below.
        
        --- Job Summary ---
        {job_summary}
        
        ___ Job Title: ___
        {job_title} 
        
        --- Candidate Bio ---
        {user_bio}
        
        The message should be friendly, professional, and under 150 words. Tailor it for a platform like LinkedIn or email.
        """,
        expected_output="""
        A short outreach message under 150 words, tailored for LinkedIn or email, that is professional and expresses interest in the job at the given agency. Save as a .txt file.
        """,
        agent=agent,
        output_file=str(cfg.CUSTOMIZED_MESSAGES_PATH),
    )

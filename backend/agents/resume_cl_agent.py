from crewai import Agent, Task
from crewai.llm import LLM
from ..utils import config as cfg

llm = LLM(
    model="gpt-4o",
    temperature=0.2,
    api_key=cfg.OPENAI_API_KEY,
)


def get_resume_cl_agent() -> Agent:
    return Agent(
        role="Resume & Cover Letter Writer",
        goal="Write a tailored resume and cover letter for a specific job posting.",
        backstory="You are an expert in resume and cover letter writing with a deep understanding of how to tailor application materials to specific job descriptions. You have experience in analyzing job postings to extract key information and using that to create compelling resumes and cover letters that highlight the applicant's relevant skills and experiences.",
        llm=llm,
        verbose=True,
    )


def create_resume_cl_task(agent, job_summary, resume_content) -> Task:
    return Task(
        description=f"""
        Using the following job summary and the applicant's existing resume content, write a tailored resume and cover letter that highlights the applicant's relevant skills and experiences for the job.
        
        Job Summary:
        {job_summary}
        
        Applicant's Existing Resume Content:
        {resume_content}

        Your output should include:
        1. A tailored resume that emphasizes the applicant's qualifications relevant to the job summary.
        2. A cover letter that explains why the applicant is a strong fit for the position
        """,
        expected_output="""
        A structured markdown document containing two sections:
        <<RESUME>>
        [The tailored resume content should be provided here, formatted as a standard resume with sections such as Summary, Skills, Experience, and Education. The content should be customized to align with the job summary provided.]
        
        <<COVER_LETTER>>
        [The cover letter should be a well-structured document that introduces the applicant, explains their interest in the position, and highlights how their skills and experiences make them a strong fit for the job. It should be tailored to the specific job summary provided.]
        """,
        agent=agent,
        output_file=str(cfg.CUSTOMIZED_RESUMES_PATH),
    )

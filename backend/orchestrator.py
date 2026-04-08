from crewai import Crew, Process
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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

# from backend.apis.jobs_api import fetch_jobs


def _extract_resume_and_cover_letter(
    content: str,
) -> tuple[str, str]:
    resume_marker = "<<RESUME>>"
    cover_marker = "<<COVER_LETTER>>"

    if resume_marker in content and cover_marker in content:
        resume_start = content.find(resume_marker) + len(
            resume_marker
        )
        cover_start = content.find(cover_marker)
        resume_text = content[resume_start:cover_start].strip()
        cover_text = content[
            cover_start + len(cover_marker) :
        ].strip()
        return resume_text, cover_text

    return content.strip(), ""


def _write_text_pdf(path: Path, text: str, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter

    y_position = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y_position, title)
    y_position -= 30

    pdf.setFont("Helvetica", 11)
    for raw_line in text.splitlines() or [""]:
        line = raw_line.strip()
        if not line:
            y_position -= 14
        else:
            words = line.split(" ")
            current_line = ""
            for word in words:
                candidate = f"{current_line} {word}".strip()
                if (
                    pdf.stringWidth(candidate, "Helvetica", 11)
                    < width - 100
                ):
                    current_line = candidate
                else:
                    pdf.drawString(50, y_position, current_line)
                    y_position -= 14
                    current_line = word
            if current_line:
                pdf.drawString(50, y_position, current_line)
                y_position -= 14

        if y_position < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y_position = height - 50

    pdf.save()


def _save_resume_and_cover_letter_pdfs(
    crew_output: str,
) -> tuple[str | None, str | None]:
    markdown_path = Path(cfg.CUSTOMIZED_RESUMES_PATH)
    content = ""

    if markdown_path.exists():
        content = markdown_path.read_text(encoding="utf-8")
    elif crew_output:
        content = str(crew_output)

    if not content.strip():
        return None, None

    resume_text, cover_letter_text = (
        _extract_resume_and_cover_letter(content)
    )

    resume_pdf_path = Path(cfg.CUSTOMIZED_RESUME_PDF_PATH)
    cover_pdf_path = Path(cfg.CUSTOMIZED_COVER_LETTER_PDF_PATH)

    _write_text_pdf(
        resume_pdf_path, resume_text, "Customized Resume"
    )
    _write_text_pdf(
        cover_pdf_path,
        cover_letter_text or "Cover letter content not generated.",
        "Cover Letter",
    )

    return str(resume_pdf_path), str(cover_pdf_path)


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


def run_pipeline(job_data=None, resume_text=None, user_bio=None):
    # # Fetch jobs posts
    # job_posts = fetch_jobs("Data Scientist", "Toronto")
    # if not job_posts:
    #     print("No job posts found. Exiting pipeline.")
    #     return

    # # Extract job description from the first result
    # job_data = job_posts[0]
    job_description = job_data.get("description", "")
    # print(job_description)
    if not job_description:
        print(
            "No job description found in the first job post. Exiting pipeline."
        )
        return

    agency_name = job_data.get("company", "the company")
    job_title = job_data.get("title", "the role")

    # # Load resume & user bio
    # resume_text = load_resume()
    # user_bio = """
    # Data science professional with 7+ years of software engineering experience building scalable, production-grade systems. Seeking Data Scientist or Machine Learning Engineer or AI Engineer roles to deliver scalable, data-driven business impact
    # """
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
    resume_pdf_path, cover_pdf_path = (
        _save_resume_and_cover_letter_pdfs(str(results))
    )

    return {
        "crew_output": results,
        "resume_pdf_path": resume_pdf_path,
        "cover_letter_pdf_path": cover_pdf_path,
    }


# if __name__ == "__main__":
# run_pipeline()

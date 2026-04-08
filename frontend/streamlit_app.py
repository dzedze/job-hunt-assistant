import streamlit as st
from pathlib import Path

from backend.orchestrator import run_pipeline, load_resume
from backend.apis.jobs_api import fetch_jobs
from backend.utils import config as cfg

MAX_RESUME_SIZE_MB = 5
MAX_RESUME_SIZE_BYTES = MAX_RESUME_SIZE_MB * 1024 * 1024

st.set_page_config(
    page_title="AI Job Hunt Assistant", layout="centered"
)

st.title("AI Job Hunt Assistant")
description = (
    "Use AI agent to analyze jobs, tailor your resume, "
    "and craft personalized messages to recruiters."
)
st.markdown(description)

if "application_results" not in st.session_state:
    st.session_state["application_results"] = []

# Input fields for job search
keywords = st.text_input("Job Keywords", "Data Scientist")
location = st.text_input("Location", "Toronto")
uploaded_resume = st.file_uploader(
    "Upload your CV (PDF, max 5MB)",
    type=["pdf"],
    help="Your file will be saved as data/resume/resume.pdf",
)

if uploaded_resume is not None:
    if uploaded_resume.size > MAX_RESUME_SIZE_BYTES:
        st.error(
            "Resume file is too large. Maximum allowed size is 5MB."
        )
    else:
        with open(cfg.RESUME_PATH, "wb") as resume_file:
            resume_file.write(uploaded_resume.getbuffer())
        st.success("Resume uploaded and saved successfully.")

user_bio = st.text_area(
    "Short bio about you (for personalized messaging)",
    "I'm a passionate data scientist with experience in machine learning and statistical analysis.",
    height=100,
)

# Search jobs
if st.button("Search Jobs"):
    with st.spinner(
        f"Searching jobs for '{keywords}' in {location}..."
    ):
        job_posts = fetch_jobs(keywords, location)

    if not job_posts:
        st.error(
            "No jobs found for this search. Try different keywords or location."
        )
    else:
        st.session_state["jobs"] = job_posts
        st.session_state["application_results"] = []
        st.success(
            "Jobs fetched! Select a job to analyze and tailor your resume."
        )

# Show checkbox for job selection
if "jobs" in st.session_state:
    selected_indexes = []
    st.markdown(
        "### Select jobs to analyze and tailor your resume:"
    )
    for idx, job in enumerate(st.session_state["jobs"]):
        title = job.get("title", "No title")
        company = job.get("company", "No company")
        checkbox = st.checkbox(
            f"{title} at {company}", key=f"job_{idx}"
        )
        if checkbox:
            selected_indexes.append(idx)
            job_description = job.get(
                "description", "No description available."
            )
            st.markdown("**Job Description**")
            st.markdown(job_description)

    # Run pipeline for selected jobs
    if st.button("Apply to Selected Jobs"):
        if not selected_indexes:
            st.warning("Please select at least one job.")
        elif uploaded_resume is not None and (
            uploaded_resume.size > MAX_RESUME_SIZE_BYTES
        ):
            st.warning("Please upload a PDF file smaller than 5MB.")
        elif (
            uploaded_resume is None and not cfg.RESUME_PATH.exists()
        ):
            st.warning(
                "Please upload your resume PDF before applying to jobs."
            )
        else:
            resume_text = load_resume()
            if not resume_text.strip():
                st.warning(
                    "Could not read text from the uploaded PDF. Try another file."
                )
                st.stop()

            st.session_state["application_results"] = []
            for idx in selected_indexes:
                job_data = st.session_state["jobs"][idx]
                with st.spinner(
                    f"Applying to {job_data.get('title')} at {job_data.get('company', 'the company')}..."
                ):
                    result = run_pipeline(
                        job_data, resume_text, user_bio
                    )

                    crew_output = result.get("crew_output", "")
                    resume_pdf_path = result.get("resume_pdf_path")
                    cover_pdf_path = result.get(
                        "cover_letter_pdf_path"
                    )

                    st.session_state["application_results"].append(
                        {
                            "job_index": idx,
                            "job_title": job_data.get(
                                "title", "Unknown role"
                            ),
                            "crew_output": crew_output,
                            "resume_pdf_path": resume_pdf_path,
                            "cover_pdf_path": cover_pdf_path,
                        }
                    )

if st.session_state.get("application_results"):
    col_results_title, col_clear = st.columns([3, 1])
    with col_results_title:
        st.markdown("## Generated Results")
    with col_clear:
        if st.button("Clear Results"):
            st.session_state["application_results"] = []
            st.rerun()

    for item in st.session_state["application_results"]:
        result_idx = item["job_index"]
        st.markdown("---")
        st.markdown(
            f"### The reach-out message for: {item['job_title']}"
        )
        st.markdown(item["crew_output"])

        resume_pdf_path = item.get("resume_pdf_path")
        if resume_pdf_path and Path(resume_pdf_path).exists():
            with open(resume_pdf_path, "rb") as file:
                st.download_button(
                    "📄 Download Customized Resume (PDF)",
                    data=file.read(),
                    file_name=Path(resume_pdf_path).name,
                    mime="application/pdf",
                    key=f"resume_pdf_{result_idx}",
                )

        cover_pdf_path = item.get("cover_pdf_path")
        if cover_pdf_path and Path(cover_pdf_path).exists():
            with open(cover_pdf_path, "rb") as file:
                st.download_button(
                    "📄 Download Cover Letter (PDF)",
                    data=file.read(),
                    file_name=Path(cover_pdf_path).name,
                    mime="application/pdf",
                    key=f"cover_pdf_{result_idx}",
                )

import streamlit as st
from backend.orchestrator import run_pipeline
from backend.apis.jobs_api import fetch_jobs

st.set_page_config(
    page_title="AI Job Hunt Assistant", layout="centered"
)

st.title("AI Job Hunt Assistant")
st.markdown(
    """
    Use AI agent to analyze jobs, tailor your resume, and craft personalized messages to recruiters.
    """
)

# Input fields for job search
keywords = st.text_input("Job Keywords", "Data Scientist")
location = st.text_input("Location", "Toronto")
resume_text = st.text_area(
    "Paste your resume text here", height=200
)
user_bio = st.text_area(
    "Short bio about you (for personalized messaging)",
    "I'm a passionate data scientist with experience in machine learning and statistical analysis.",
    height=100,
)

# Search jobs
if st.button("Search Jobs"):
    job_posts = fetch_jobs(keywords, location)
    if not job_posts:
        st.error(
            "No jobs found for this search. Try different keywords or location."
        )
    else:
        st.session_state["jobs"] = job_posts
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

    # Run pipeline for selected jobs
    if st.button("Apply to Selected Jobs"):
        if not selected_indexes:
            st.warning("Please select at least one job.")
        elif not resume_text.strip():
            st.warning(
                "Please paste your resume text to tailor it for the selected jobs."
            )
        else:
            for idx in selected_indexes:
                job_data = st.session_state["jobs"][idx]
                with st.spinner(
                    f"Applying to {job_data.get('title')} at {job_data.get('company', 'the company')}..."
                ):
                    result = run_pipeline(
                        job_data, resume_text, user_bio
                    )
                    st.markdown("---")
                    st.markdown(
                        f"### The reach-out message for: {job_data.get('PositionTitle')}"
                    )
                    st.markdown(result)

import sys
import types
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def fake_import_environment(tmp_path: Path, monkeypatch):
    """Fixture to mock crewai, pypdf, and agents for orchestrator testing."""
    # Set environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")
    monkeypatch.setenv("JOBS_API_KEY", "fake-jobs-key")
    monkeypatch.setenv("JOBS_API_HOST", "fake-host")

    # Clear backend modules from cache
    modules_to_clear = [
        "backend.utils",
        "backend.utils.config",
        "backend.apis.jobs_api",
        "backend.agents.jd_analyst",
        "backend.agents.resume_cl_agent",
        "backend.agents.messaging_agent",
        "backend.orchestrator",
    ]
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]

    # Mock pypdf.PdfReader
    pypdf_pkg = cast(Any, types.ModuleType("pypdf"))

    class MockPdfReader:
        def __init__(self, path):
            self.path = path
            # Check if path exists (or is a tmp_path object)
            if isinstance(path, str):
                if path == "/path/to/nonexistent/resume.pdf":
                    raise FileNotFoundError(f"No file at {path}")
            # Return mock pages for valid paths
            mock_page = Mock()
            mock_page.extract_text.return_value = (
                "Sample resume text"
            )
            self.pages = [mock_page]

    pypdf_pkg.PdfReader = MockPdfReader
    monkeypatch.setitem(sys.modules, "pypdf", pypdf_pkg)

    # Create fake crewai package
    crewai_pkg = cast(Any, types.ModuleType("crewai"))

    class Agent:
        def __init__(
            self, role, goal, backstory, llm, verbose=False
        ):
            self.role = role
            self.goal = goal
            self.backstory = backstory
            self.llm = llm
            self.verbose = verbose

    class Task:
        def __init__(
            self,
            description,
            expected_output,
            agent,
            output_file,
        ):
            self.description = description
            self.expected_output = expected_output
            self.agent = agent
            self.output_file = output_file

    class LLM:
        def __init__(self, model, temperature, api_key):
            self.model = model
            self.temperature = temperature
            self.api_key = api_key

    class Crew:
        def __init__(
            self, agents, tasks, process=None, verbose=False
        ):
            self.agents = agents
            self.tasks = tasks
            self.process = process
            self.verbose = verbose

        def kickoff(self):
            return "Crew execution results"

    class Process:
        sequential = "sequential"
        hierarchical = "hierarchical"

    crewai_pkg.Agent = Agent
    crewai_pkg.Task = Task
    crewai_pkg.Crew = Crew
    crewai_pkg.Process = Process

    crewai_llm = cast(Any, types.ModuleType("crewai.llm"))
    crewai_llm.LLM = LLM
    crewai_pkg.llm = crewai_llm

    monkeypatch.setitem(sys.modules, "crewai", crewai_pkg)
    monkeypatch.setitem(sys.modules, "crewai.llm", crewai_llm)

    # Mock jobs_api.fetch_jobs
    jobs_api_pkg = cast(
        Any, types.ModuleType("backend.apis.jobs_api")
    )

    def mock_fetch_jobs(*args, **kwargs):
        return [
            {
                "job_id": "123",
                "title": "Data Scientist",
                "company": "Tech Corp",
                "location": "Toronto",
                "description": "Analyze large datasets",
                "apply_link": "https://example.com/apply",
            }
        ]

    jobs_api_pkg.fetch_jobs = mock_fetch_jobs
    monkeypatch.setitem(
        sys.modules, "backend.apis.jobs_api", jobs_api_pkg
    )

    # Mock agent creation functions
    jd_analyst_pkg = cast(
        Any, types.ModuleType("backend.agents.jd_analyst")
    )

    def mock_get_jd_analyst_agent():
        return Agent(
            role="JD Analyst",
            goal="Analyze job descriptions",
            backstory="Expert analyst",
            llm=LLM(
                model="gpt-4o",
                temperature=0.2,
                api_key="fake-key",
            ),
            verbose=True,
        )

    def mock_create_jd_analysis_task(agent, description):
        return Task(
            description=f"Analyze: {description}",
            expected_output="Analysis results",
            agent=agent,
            output_file=str(tmp_path / "report.md"),
        )

    jd_analyst_pkg.get_jd_analyst_agent = mock_get_jd_analyst_agent
    jd_analyst_pkg.create_jd_analysis_task = (
        mock_create_jd_analysis_task
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.agents.jd_analyst",
        jd_analyst_pkg,
    )

    # Mock resume_cl_agent
    resume_pkg = cast(
        Any, types.ModuleType("backend.agents.resume_cl_agent")
    )

    def mock_get_resume_cl_agent():
        return Agent(
            role="Resume Writer",
            goal="Write resumes",
            backstory="Expert resume writer",
            llm=LLM(
                model="gpt-4o",
                temperature=0.2,
                api_key="fake-key",
            ),
            verbose=True,
        )

    def mock_create_resume_cl_task(agent, job_desc, resume):
        return Task(
            description=f"Create resume for: {job_desc}",
            expected_output="Resume and cover letter",
            agent=agent,
            output_file=str(tmp_path / "resume.md"),
        )

    resume_pkg.get_resume_cl_agent = mock_get_resume_cl_agent
    resume_pkg.create_resume_cl_task = mock_create_resume_cl_task
    monkeypatch.setitem(
        sys.modules, "backend.agents.resume_cl_agent", resume_pkg
    )

    # Mock messaging_agent
    messaging_pkg = cast(
        Any, types.ModuleType("backend.agents.messaging_agent")
    )

    def mock_get_messaging_agent():
        return Agent(
            role="Message Writer",
            goal="Write messages",
            backstory="Expert message writer",
            llm=LLM(
                model="gpt-4o",
                temperature=0.2,
                api_key="fake-key",
            ),
            verbose=True,
        )

    def mock_create_messaging_task(agent, job, company, title, bio):
        return Task(
            description=f"Write message for {title} at {company}",
            expected_output="Outreach message",
            agent=agent,
            output_file=str(tmp_path / "message.txt"),
        )

    messaging_pkg.get_messaging_agent = mock_get_messaging_agent
    messaging_pkg.create_messaging_task = mock_create_messaging_task
    monkeypatch.setitem(
        sys.modules, "backend.agents.messaging_agent", messaging_pkg
    )

    yield


def test_load_resume_from_pdf():
    """Test loading resume text from PDF file."""
    from backend.orchestrator import load_resume

    text = load_resume()
    assert isinstance(text, str)
    assert "Sample resume text" in text


def test_load_resume_file_not_found():
    """Test load_resume with non-existent file returns empty string."""
    from backend.orchestrator import load_resume

    text = load_resume("/path/to/nonexistent/resume.pdf")
    assert text == ""


def test_load_resume_with_custom_path(tmp_path, monkeypatch):
    """Test load_resume with custom path."""
    from backend.orchestrator import load_resume

    custom_path = tmp_path / "custom_resume.pdf"
    text = load_resume(custom_path)
    assert isinstance(text, str)


def test_run_pipeline_successful():
    """Test successful run_pipeline with mocked dependencies."""
    from backend.orchestrator import run_pipeline

    job_data = {
        "job_id": "123",
        "title": "Data Scientist",
        "company": "Tech Corp",
        "description": "Analyze large datasets",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    result = run_pipeline(job_data, resume_text, user_bio)

    assert result == "Crew execution results"


def test_run_pipeline_no_description():
    """Test run_pipeline when job has no description."""
    from backend.orchestrator import run_pipeline

    job_data = {
        "job_id": "123",
        "title": "Data Scientist",
        "company": "Tech Corp",
        "description": "",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    result = run_pipeline(job_data, resume_text, user_bio)

    assert result is None


def test_run_pipeline_creates_crew():
    """Test that run_pipeline creates a Crew with all agents and tasks."""
    from backend.orchestrator import run_pipeline

    crew_init_called = {"called": False}

    def mock_crew(*args, **kwargs):
        crew_init_called["called"] = True
        crew_init_called["agents"] = len(kwargs.get("agents", []))
        crew_init_called["tasks"] = len(kwargs.get("tasks", []))
        mock_crew_obj = Mock()
        mock_crew_obj.kickoff.return_value = "Results"
        return mock_crew_obj

    import backend.orchestrator as orch_module
    import sys

    if "backend.orchestrator" in sys.modules:
        del sys.modules["backend.orchestrator"]

    # from backend.orchestrator import Crew

    # original_crew = Crew
    orch_module.Crew = mock_crew

    job_data = {
        "job_id": "123",
        "title": "Data Scientist",
        "company": "Tech Corp",
        "description": "Analyze large datasets",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    run_pipeline(job_data, resume_text, user_bio)

    assert crew_init_called["called"] is True
    assert crew_init_called["agents"] == 3  # jd, resume, messaging
    assert crew_init_called["tasks"] == 3


def test_run_pipeline_extracts_job_details():
    """Test that run_pipeline correctly extracts job details."""
    from backend.orchestrator import run_pipeline

    job_data = {
        "job_id": "456",
        "title": "Senior Data Scientist",
        "company": "DataCorp",
        "description": "Advanced analytics role",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    messaging_task_called = {"company": None, "title": None}

    def mock_create_messaging_task(
        agent, desc, company, title, bio
    ):
        messaging_task_called["company"] = company
        messaging_task_called["title"] = title
        return Mock(
            description=desc,
            expected_output="",
            agent=agent,
            output_file="",
        )

    import backend.orchestrator as orch_module
    import sys

    if "backend.orchestrator" in sys.modules:
        del sys.modules["backend.orchestrator"]

    # from backend.orchestrator import create_messaging_task

    # original_messaging_task = create_messaging_task
    orch_module.create_messaging_task = mock_create_messaging_task

    run_pipeline(job_data, resume_text, user_bio)

    assert messaging_task_called["company"] == "DataCorp"
    assert messaging_task_called["title"] == "Senior Data Scientist"


def test_run_pipeline_uses_sequential_process():
    """Test that run_pipeline uses sequential process."""
    from backend.orchestrator import run_pipeline

    crew_process = {"value": None}

    def mock_crew(*args, **kwargs):
        crew_process["value"] = kwargs.get("process")
        mock_crew_obj = Mock()
        mock_crew_obj.kickoff.return_value = "Results"
        return mock_crew_obj

    import backend.orchestrator as orch_module
    import sys

    if "backend.orchestrator" in sys.modules:
        del sys.modules["backend.orchestrator"]

    # from backend.orchestrator import Crew

    # original_crew = Crew
    orch_module.Crew = mock_crew

    job_data = {
        "job_id": "123",
        "title": "Data Scientist",
        "company": "Tech Corp",
        "description": "Analyze large datasets",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    run_pipeline(job_data, resume_text, user_bio)

    assert crew_process["value"] == "sequential"


def test_run_pipeline_creates_all_task_types():
    """Test that run_pipeline creates all three task types."""
    from backend.orchestrator import run_pipeline

    task_creation = {
        "jd_task": False,
        "resume_task": False,
        "message_task": False,
    }

    def mock_create_jd_task(agent, desc):
        task_creation["jd_task"] = True
        return Mock(
            description=desc,
            expected_output="",
            agent=agent,
            output_file="",
        )

    def mock_create_resume_task(agent, desc, resume):
        task_creation["resume_task"] = True
        return Mock(
            description=desc,
            expected_output="",
            agent=agent,
            output_file="",
        )

    def mock_create_message_task(agent, desc, company, title, bio):
        task_creation["message_task"] = True
        return Mock(
            description=desc,
            expected_output="",
            agent=agent,
            output_file="",
        )

    import backend.orchestrator as orch_module
    import sys

    if "backend.orchestrator" in sys.modules:
        del sys.modules["backend.orchestrator"]

    # from backend.orchestrator import (
    #     create_jd_analysis_task,
    #     create_resume_cl_task,
    #     create_messaging_task,
    # )

    # original_jd_task = create_jd_analysis_task
    # original_resume_task = create_resume_cl_task
    # original_message_task = create_messaging_task

    orch_module.create_jd_analysis_task = mock_create_jd_task
    orch_module.create_resume_cl_task = mock_create_resume_task
    orch_module.create_messaging_task = mock_create_message_task

    job_data = {
        "job_id": "123",
        "title": "Data Scientist",
        "company": "Tech Corp",
        "description": "Analyze large datasets",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    run_pipeline(job_data, resume_text, user_bio)

    assert task_creation["jd_task"] is True
    assert task_creation["resume_task"] is True
    assert task_creation["message_task"] is True


def test_run_pipeline_with_none_job_data():
    """Test run_pipeline with None job_data."""
    from backend.orchestrator import run_pipeline

    with pytest.raises(AttributeError):
        run_pipeline(None, "resume", "bio")


def test_run_pipeline_with_empty_job_data():
    """Test run_pipeline with empty job_data dict."""
    from backend.orchestrator import run_pipeline

    result = run_pipeline({}, "resume", "bio")
    assert result is None


def test_run_pipeline_returns_crew_results():
    """Test that run_pipeline returns the crew kickoff results."""
    from backend.orchestrator import run_pipeline

    job_data = {
        "job_id": "123",
        "title": "Data Scientist",
        "company": "Tech Corp",
        "description": "Analyze large datasets",
    }
    resume_text = "Sample resume content"
    user_bio = "Data science professional"

    result = run_pipeline(job_data, resume_text, user_bio)

    assert result == "Crew execution results"

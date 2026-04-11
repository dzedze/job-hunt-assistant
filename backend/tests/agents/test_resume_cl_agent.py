import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest


@pytest.fixture(autouse=True)
def fake_import_environment(tmp_path: Path, monkeypatch):
    """Fixture to mock crewai and config modules for testing."""
    # Set environment variables before any imports
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")
    monkeypatch.setenv("JOBS_API_KEY", "fake-jobs-key")
    monkeypatch.setenv("JOBS_API_HOST", "fake-host")

    # Clear backend modules from cache to force reload with mocked env
    if "backend.utils" in sys.modules:
        del sys.modules["backend.utils"]
    if "backend.utils.config" in sys.modules:
        del sys.modules["backend.utils.config"]
    if "backend.agents.resume_cl_agent" in sys.modules:
        del sys.modules["backend.agents.resume_cl_agent"]

    # Create fake crewai package with Agent and Task classes
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

    crewai_pkg.Agent = Agent
    crewai_pkg.Task = Task

    # Create fake LLM class
    class LLM:
        def __init__(self, model, temperature, api_key):
            self.model = model
            self.temperature = temperature
            self.api_key = api_key

    crewai_pkg.llm = cast(Any, types.ModuleType("crewai.llm"))
    crewai_pkg.llm.LLM = LLM

    monkeypatch.setitem(sys.modules, "crewai", crewai_pkg)
    monkeypatch.setitem(sys.modules, "crewai.llm", crewai_pkg.llm)

    yield


def test_get_resume_cl_agent_returns_agent():
    """Test that get_resume_cl_agent returns a properly configured Agent."""
    from backend.agents import resume_cl_agent

    agent = resume_cl_agent.get_resume_cl_agent()

    assert agent.role == "Resume & Cover Letter Writer"
    assert "tailored resume and cover letter" in agent.goal
    assert "resume and cover letter writing" in (agent.backstory)
    assert "job postings" in agent.backstory
    assert agent.verbose is True
    assert agent.llm.model == "gpt-4o"
    assert agent.llm.temperature == 0.2
    assert agent.llm.api_key is not None


def test_create_resume_cl_task_returns_task():
    """Test that create_resume_cl_task returns a properly configured Task."""
    from backend.agents import resume_cl_agent

    fake_agent = object()
    job_summary = "Data Scientist role requiring Python and SQL"
    resume_content = "5+ years experience as data analyst"

    task = resume_cl_agent.create_resume_cl_task(
        fake_agent, job_summary, resume_content
    )

    assert task.agent is fake_agent
    assert job_summary in task.description
    assert resume_content in task.description
    assert "<<RESUME>>" in task.expected_output
    assert "<<COVER_LETTER>>" in task.expected_output
    assert task.output_file.endswith("customized_resume.md")


def test_create_resume_cl_task_description_structure():
    """Test that create_resume_cl_task description includes required elements."""
    from backend.agents import resume_cl_agent

    fake_agent = object()
    job_summary = "Senior Software Engineer role"
    resume_content = "Software engineer with 10 years experience"

    task = resume_cl_agent.create_resume_cl_task(
        fake_agent, job_summary, resume_content
    )

    description = task.description
    assert "tailored resume" in description.lower()
    assert "cover letter" in description.lower()
    assert "qualifications" in description.lower()
    assert "skills" in description.lower()


def test_create_resume_cl_task_output_includes_sections():
    """Test that create_resume_cl_task output specifies required sections."""
    from backend.agents import resume_cl_agent

    fake_agent = object()
    task = resume_cl_agent.create_resume_cl_task(
        fake_agent, "Job summary", "Resume content"
    )

    expected_output = task.expected_output
    assert "<<RESUME>>" in expected_output
    assert "<<COVER_LETTER>>" in expected_output
    assert "Summary" in expected_output
    assert "Skills" in expected_output
    assert "Experience" in expected_output
    assert "Education" in expected_output


def test_create_resume_cl_task_emphasizes_relevance():
    """Test that task instructions emphasize relevance to job."""
    from backend.agents import resume_cl_agent

    fake_agent = object()
    task = resume_cl_agent.create_resume_cl_task(
        fake_agent, "job summary", "resume content"
    )

    description = task.description.lower()
    assert "tailor" in description or "relevant" in description


def test_create_resume_cl_task_expected_output_format():
    """Test that expected output format is well-structured."""
    from backend.agents import resume_cl_agent

    fake_agent = object()
    task = resume_cl_agent.create_resume_cl_task(
        fake_agent, "Job", "Resume"
    )

    output = task.expected_output
    assert "structured markdown" in output.lower()
    assert "two sections" in output.lower()

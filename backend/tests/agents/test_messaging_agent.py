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
    if "backend.agents.messaging_agent" in sys.modules:
        del sys.modules["backend.agents.messaging_agent"]

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


def test_get_messaging_agent_returns_agent():
    """Test that get_messaging_agent returns a properly configured Agent."""
    from backend.agents import messaging_agent

    agent = messaging_agent.get_messaging_agent()

    assert agent.role == "Outreach & Messaging Writer"
    assert "personalized messages for job outreach" in agent.goal
    assert "career coach" in agent.backstory
    assert agent.verbose is True
    assert agent.llm.model == "gpt-4o"
    assert agent.llm.temperature == 0.2
    assert agent.llm.api_key is not None


def test_create_messaging_task_returns_task():
    """Test that create_messaging_task returns a properly configured Task."""
    from backend.agents import messaging_agent

    fake_agent = object()
    job_summary = "Data scientist role at Tech Company"
    agency_name = "Tech Company"
    job_title = "Senior Data Scientist"

    task = messaging_agent.create_messaging_task(
        fake_agent,
        job_summary,
        agency_name,
        job_title,
    )

    assert task.agent is fake_agent
    assert agency_name in task.description
    assert job_title in task.description
    assert job_summary in task.description
    assert "150 words" in task.expected_output
    assert task.output_file.endswith("customized_message.txt")


def test_create_messaging_task_with_custom_bio():
    """Test create_messaging_task with custom user bio."""
    from backend.agents import messaging_agent

    fake_agent = object()
    job_summary = "ML Engineer role"
    agency_name = "ML Corp"
    job_title = "ML Engineer"
    custom_bio = (
        "Expert machine learning engineer with 5+ years experience"
    )

    task = messaging_agent.create_messaging_task(
        fake_agent,
        job_summary,
        agency_name,
        job_title,
        user_bio=custom_bio,
    )

    assert custom_bio in task.description
    assert "professional" in task.expected_output.lower()


def test_default_user_bio_exists():
    """Test that default_user_bio is defined."""
    from backend.agents import messaging_agent

    assert hasattr(messaging_agent, "default_user_bio")
    assert isinstance(messaging_agent.default_user_bio, str)
    assert len(messaging_agent.default_user_bio) > 0
    assert "Data science professional" in (
        messaging_agent.default_user_bio
    )


def test_create_messaging_task_output_expectations():
    """Test that create_messaging_task specifies correct output expectations."""
    from backend.agents import messaging_agent

    fake_agent = object()
    task = messaging_agent.create_messaging_task(
        fake_agent,
        "Job summary",
        "Company Name",
        "Job Title",
    )

    assert "LinkedIn or email" in task.expected_output
    assert "professional" in task.expected_output.lower()
    assert "150 words" in task.expected_output

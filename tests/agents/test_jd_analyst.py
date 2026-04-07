import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest


@pytest.fixture(autouse=True)
def fake_import_environment(tmp_path: Path, monkeypatch):
    # Create a fake utils package with a config module used by jd_analyst.py
    utils_pkg = cast(Any, types.ModuleType("utils"))
    utils_config = cast(Any, types.ModuleType("utils.config"))
    utils_config.GEMINI_API_KEY = "fake-gemini-key"
    utils_config.JOBS_REPORTS_PATH = tmp_path / "jobs_report.md"
    utils_pkg.config = utils_config

    monkeypatch.setitem(sys.modules, "utils", utils_pkg)
    monkeypatch.setitem(sys.modules, "utils.config", utils_config)

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
            self, description, expected_output, agent, output_file
        ):
            self.description = description
            self.expected_output = expected_output
            self.agent = agent
            self.output_file = output_file

    crewai_pkg.Agent = Agent
    crewai_pkg.Task = Task
    monkeypatch.setitem(sys.modules, "crewai", crewai_pkg)

    # Create fake langchain_google_genai package used by jd_analyst.py
    langchain_pkg = cast(
        Any, types.ModuleType("langchain_google_genai")
    )

    class ChatGoogleGenerativeAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    langchain_pkg.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    monkeypatch.setitem(
        sys.modules, "langchain_google_genai", langchain_pkg
    )

    # Ensure reload uses our fake modules
    if "backend.agents.jd_analyst" in sys.modules:
        del sys.modules["backend.agents.jd_analyst"]

    yield


def test_get_jd_analyst_agent_returns_agent(monkeypatch):
    from backend.agents import jd_analyst

    agent = jd_analyst.get_jd_analyst_agent()

    assert agent.role == "JD Analyst"
    assert "Understand and summarize job postings" in agent.goal
    assert "job market analysis" in agent.backstory
    assert agent.verbose is True
    assert hasattr(agent.llm, "kwargs")
    assert agent.llm.kwargs["model"] == "gemini-2.0-flash"
    assert agent.llm.kwargs["temperature"] == 0
    assert agent.llm.kwargs["api_key"] == "fake-gemini-key"


def test_create_jd_analysis_task_returns_task(monkeypatch):
    from backend.agents import jd_analyst

    fake_agent = object()
    job_description = "This is a sample job description."
    task = jd_analyst.create_jd_analysis_task(
        fake_agent, job_description
    )

    assert task.agent is fake_agent
    assert "Analyze the following job posting" in task.description
    assert job_description in task.description
    assert "Qualifications" in task.expected_output
    assert task.output_file.name == "jobs_report.md"

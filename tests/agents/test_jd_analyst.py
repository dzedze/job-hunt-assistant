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
    utils_config.OPENAI_API_KEY = "fake-openai-key"
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

    class LLM:
        def __init__(self, model, temperature, api_key):
            self.model = model
            self.temperature = temperature
            self.api_key = api_key

    crewai_pkg.Agent = Agent
    crewai_pkg.Task = Task

    # Create fake crewai.llm submodule
    crewai_llm = cast(Any, types.ModuleType("crewai.llm"))
    crewai_llm.LLM = LLM
    crewai_pkg.llm = crewai_llm

    monkeypatch.setitem(sys.modules, "crewai", crewai_pkg)
    monkeypatch.setitem(sys.modules, "crewai.llm", crewai_llm)

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
    assert agent.llm.model == "gpt-4o"
    assert agent.llm.temperature == 0.2
    assert agent.llm.api_key is not None


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
    assert "report.md" in task.output_file

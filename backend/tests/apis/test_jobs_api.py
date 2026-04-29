import json
from pathlib import Path
from unittest.mock import Mock

from requests.exceptions import RequestException

from backend.apis.jobs_api import fetch_jobs, store_fetched_jobs


def test_store_fetched_jobs_writes_json(tmp_path: Path):
    jobs = [
        {
            "job_id": "1",
            "job_title": "Software Engineer",
            "employer_name": "Acme Corp",
        }
    ]
    file_path = tmp_path / "jobs.json"

    store_fetched_jobs(file_path, jobs)

    assert file_path.exists()
    with open(file_path, "r") as file:
        assert json.load(file) == jobs


def test_fetch_jobs_success(monkeypatch, tmp_path: Path):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "data": [
            {
                "job_id": "123",
                "job_title": "Data Scientist",
                "employer_name": "Tech Co",
                "job_city": "Toronto",
                "job_description": "Analyze data",
                "job_apply_link": "https://example.com/apply",
            }
        ]
    }

    monkeypatch.setattr(
        "backend.apis.jobs_api.requests.get",
        lambda *args, **kwargs: mock_response,
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_HOST",
        "jsearch.p.rapidapi.com",
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_KEY",
        "fake-key",
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.TEMP_FETCHED_JOBS_PATH",
        tmp_path / "temp_fetched_jobs.json",
    )

    results = fetch_jobs("Data Scientist", "Toronto", max_results=1)

    assert len(results) == 1
    assert results[0]["job_id"] == "123"
    assert results[0]["title"] == "Data Scientist"
    assert results[0]["company"] == "Tech Co"
    assert results[0]["location"] == "Toronto"
    assert results[0]["description"] == "Analyze data"
    assert results[0]["apply_link"] == "https://example.com/apply"

    assert (tmp_path / "temp_fetched_jobs.json").exists()


def test_fetch_jobs_returns_no_jobs(monkeypatch):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"data": []}

    monkeypatch.setattr(
        "backend.apis.jobs_api.requests.get",
        lambda *args, **kwargs: mock_response,
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_HOST",
        "jsearch.p.rapidapi.com",
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_KEY",
        "fake-key",
    )

    results = fetch_jobs("Data Scientist", "Toronto")

    assert results == []


def test_fetch_jobs_request_exception(monkeypatch):
    def raise_request(*args, **kwargs):
        raise RequestException("timeout")

    monkeypatch.setattr(
        "backend.apis.jobs_api.requests.get",
        raise_request,
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_HOST",
        "jsearch.p.rapidapi.com",
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_KEY",
        "fake-key",
    )

    results = fetch_jobs("Data Scientist", "Toronto")

    assert results == []


def test_fetch_jobs_invalid_json(monkeypatch):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("invalid json")

    monkeypatch.setattr(
        "backend.apis.jobs_api.requests.get",
        lambda *args, **kwargs: mock_response,
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_HOST",
        "jsearch.p.rapidapi.com",
    )
    monkeypatch.setattr(
        "backend.apis.jobs_api.cfg.JOBS_API_KEY",
        "fake-key",
    )

    results = fetch_jobs("Data Scientist", "Toronto")

    assert results == []

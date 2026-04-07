import requests
import json
from pathlib import Path
from requests.exceptions import RequestException
from backend.utils import config as cfg
from typing import List, Dict


def store_fetched_jobs(path: Path, jobs: List[Dict]):
    with open(path, "w") as file:
        json.dump(jobs, file, indent=4)


def fetch_jobs(
    role: str,
    area: str,
    country: str = "Canada",
    max_results: int = 5,
) -> List[Dict]:
    url = f"https://{cfg.JOBS_API_HOST}/search"

    query = f"{role} in {area}"

    querystring = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "country": country,
        "date_posted": "all",
    }

    headers = {
        "x-rapidapi-key": cfg.JOBS_API_KEY,
        "x-rapidapi-host": cfg.JOBS_API_HOST,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=querystring,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except RequestException as error:
        return [
            {
                "message": "Job fetch failed",
                "error": str(error),
            }
        ]
    except ValueError:
        return [
            {
                "message": "Job fetch failed",
                "error": "Invalid JSON response from jobs API.",
            }
        ]

    job_list = data.get("data", [])[:max_results]

    if not job_list:
        return [{"message": "No jobs found."}]

    store_fetched_jobs(cfg.TEMP_FETCHED_JOBS_PATH, job_list)

    results = []

    for job in job_list:
        results.append(
            {
                "job_id": job.get("job_id"),
                "title": job.get("job_title"),
                "company": job.get("employer_name"),
                "location": job.get("job_city"),
                "description": job.get("job_description"),
                "apply_link": job.get(
                    "job_apply_link", "Not provided"
                ),
            }
        )
    print(results)
    return results


if __name__ == "__main__":
    # Example usage - check if API key is configured
    if not cfg.JOBS_API_KEY:
        print(
            "JOBS_API_KEY not configured. Please set the JOBS_API_KEY environment variable."
        )
        print(
            "You can get a key from: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
        )
    else:
        jobs = fetch_jobs("Data Scientist", "Toronto")
        for job in jobs:
            print(job)

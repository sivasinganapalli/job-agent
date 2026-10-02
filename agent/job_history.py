import os
import re
import pandas as pd
from urllib.parse import urlparse, urlunparse


HISTORY_FILE = "data/job_history.csv"


HISTORY_COLUMNS = [
    "job_key",
    "job_url",
    "title",
    "company",
    "location",
    "date_posted",
    "first_seen",
    "last_seen",
    "matcher_score",
    "ai_analyzed",
]


def normalize_url(url):
    """
    Normalize a job URL so tracking parameters and
    minor URL differences don't create duplicates.
    """

    if not url or pd.isna(url):
        return ""

    url = str(url).strip()

    try:
        parsed = urlparse(url)

        # Remove query parameters and fragments.
        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                "",
                "",
            )
        )

        return normalized

    except Exception:
        return url.lower().rstrip("/")


def normalize_text(value):
    """Normalize text for duplicate detection."""

    if value is None or pd.isna(value):
        return ""

    value = str(value).lower().strip()

    # Replace multiple spaces
    value = re.sub(r"\s+", " ", value)

    return value



def create_job_key(job):
    """
    Create a stable identifier for a job.

    Rules:
    1. Use the full job URL when it contains a specific job identifier.
    2. Do NOT rely on generic Indeed / viewjob URLs.
    3. Fall back to company + title + location when the URL
       is generic or unavailable.
    """

    job_url = normalize_url(job.get("job_url", ""))

    company = normalize_text(job.get("company", ""))
    title = normalize_text(job.get("title", ""))
    location = normalize_text(job.get("location", ""))

    # -----------------------------------------------------
    # LinkedIn
    # -----------------------------------------------------
    # Example:
    # https://www.linkedin.com/jobs/view/4472883694
    #
    # The numeric job ID makes this a reliable identifier.

    if "linkedin.com/jobs/view/" in job_url:

        return f"url::{job_url}"

    # -----------------------------------------------------
    # Indeed
    # -----------------------------------------------------
    # Some Indeed results can have generic URLs such as:
    #
    # https://in.indeed.com/viewjob
    #
    # These are NOT reliable unique identifiers.
    #
    # Therefore use company + title + location.

    if "indeed.com/viewjob" in job_url:

        return (
            f"text::{company}|{title}|{location}"
        )

    # -----------------------------------------------------
    # Other sources with a usable URL
    # -----------------------------------------------------

    if job_url:

        return f"url::{job_url}"

    # -----------------------------------------------------
    # No usable URL
    # -----------------------------------------------------

    return (
        f"text::{company}|{title}|{location}"
    )

    """
    Create a stable identifier for a job.

    Primary identity:
        normalized job URL

    Fallback:
        company + title + location
    """

    job_url = normalize_url(job.get("job_url", ""))

    if job_url:
        return f"url::{job_url}"

    company = normalize_text(job.get("company", ""))
    title = normalize_text(job.get("title", ""))
    location = normalize_text(job.get("location", ""))

    return f"text::{company}|{title}|{location}"


def load_history():
    """Load existing job history."""

    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    history = pd.read_csv(HISTORY_FILE)

    # Make sure all expected columns exist.
    for column in HISTORY_COLUMNS:
        if column not in history.columns:
            history[column] = ""

    return history[HISTORY_COLUMNS]


def save_history(history):
    """Save job history."""

    os.makedirs("data", exist_ok=True)

    history.to_csv(
        HISTORY_FILE,
        index=False,
        encoding="utf-8",
    )


def mark_jobs_seen(jobs):
    """
    Add new jobs to history or update last_seen
    for jobs already known.
    """

    history = load_history()

    today = pd.Timestamp.now().strftime("%Y-%m-%d")

    for _, job in jobs.iterrows():

        job_dict = job.to_dict()

        job_key = create_job_key(job_dict)

        existing = history["job_key"] == job_key

        if existing.any():

            index = history.index[existing][0]

            history.at[index, "last_seen"] = today

        else:

            new_row = {
                "job_key": job_key,
                "job_url": normalize_url(
                    job_dict.get("job_url", "")
                ),
                "title": job_dict.get("title", ""),
                "company": job_dict.get("company", ""),
                "location": job_dict.get("location", ""),
                "date_posted": job_dict.get("date_posted", ""),
                "first_seen": today,
                "last_seen": today,
                "matcher_score": "",
                "ai_analyzed": False,
            }

            history = pd.concat(
                [
                    history,
                    pd.DataFrame([new_row]),
                ],
                ignore_index=True,
            )

    save_history(history)

    return history


def filter_new_jobs(jobs):
    """
    Return only jobs that have NOT been seen previously.

    Existing jobs are not returned.
    """

    history = load_history()

    if history.empty:
        jobs = jobs.copy()
        jobs["job_key"] = jobs.apply(
            create_job_key,
            axis=1,
        )
        return jobs

    existing_keys = set(
        history["job_key"].astype(str)
    )

    jobs = jobs.copy()

    jobs["job_key"] = jobs.apply(
        create_job_key,
        axis=1,
    )

    new_jobs = jobs[
        ~jobs["job_key"].isin(existing_keys)
    ].copy()

    return new_jobs


def get_history_stats():
    """Return basic history statistics."""

    history = load_history()

    if history.empty:
        return {
            "total_seen": 0,
            "ai_analyzed": 0,
        }

    analyzed = history["ai_analyzed"].astype(str).str.lower() == "true"

    return {
        "total_seen": len(history),
        "ai_analyzed": analyzed.sum(),
    }

import os
import pandas as pd
from datetime import datetime


HISTORY_FILE = "data/aruna_job_history.csv"

HISTORY_COLUMNS = [
    "job_key",
    "job_url",
    "title",
    "company",
    "location",
    "source",
    "date_posted",
    "first_seen",
]


def ensure_history_file():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(
            columns=HISTORY_COLUMNS
        ).to_csv(
            HISTORY_FILE,
            index=False,
        )


def load_history():
    ensure_history_file()

    history = pd.read_csv(HISTORY_FILE)

    if history.empty:
        return history

    history["job_key"] = (
        history["job_key"]
        .fillna("")
        .astype(str)
    )

    return history


def filter_new_jobs(jobs):
    """
    Return only jobs that have not been
    processed and emailed previously.
    """

    history = load_history()

    if jobs.empty:
        return jobs

    if history.empty:
        print(
            f"History empty. "
            f"All {len(jobs)} jobs are new."
        )

        return jobs.copy()

    processed_keys = set(
        history["job_key"].tolist()
    )

    new_jobs = jobs[
        ~jobs["job_key"].isin(processed_keys)
    ].copy()

    print(
        f"Previously processed: "
        f"{len(jobs) - len(new_jobs)}"
    )

    print(
        f"New jobs: {len(new_jobs)}"
    )

    return new_jobs.reset_index(drop=True)


def mark_jobs_processed(jobs):
    """
    Add successfully emailed jobs to history.

    We only call this AFTER the email succeeds.
    """

    if jobs.empty:
        return

    history = load_history()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    records = []

    for _, job in jobs.iterrows():

        records.append(
            {
                "job_key": job.get(
                    "job_key",
                    "",
                ),

                "job_url": job.get(
                    "job_url",
                    "",
                ),

                "title": job.get(
                    "title",
                    "",
                ),

                "company": job.get(
                    "company",
                    "",
                ),

                "location": job.get(
                    "location",
                    "",
                ),

                "source": job.get(
                    "search_site",
                    job.get(
                        "site",
                        "",
                    ),
                ),

                "date_posted": job.get(
                    "date_posted",
                    "",
                ),

                "first_seen": now,
            }
        )

    new_history = pd.DataFrame(
        records,
        columns=HISTORY_COLUMNS,
    )

    history = pd.concat(
        [
            history,
            new_history,
        ],
        ignore_index=True,
    )

    history = history.drop_duplicates(
        subset=["job_key"],
        keep="first",
    )

    history.to_csv(
        HISTORY_FILE,
        index=False,
    )

    print(
        f"History updated. "
        f"Total processed jobs: "
        f"{len(history)}"
    )
import os
import pandas as pd

from agent.job_search import search_jobs


DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "jobs.csv")


def save_jobs(jobs: pd.DataFrame):
    os.makedirs(DATA_DIR, exist_ok=True)

    if jobs.empty:
        print("No jobs found.")
        return

    jobs.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(jobs)} jobs to {OUTPUT_FILE}")


if __name__ == "__main__":
    jobs = search_jobs()
    save_jobs(jobs)
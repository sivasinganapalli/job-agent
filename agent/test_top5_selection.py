import pandas as pd

from job_history import filter_new_jobs
from matcher import match_jobs

JOBS_FILE = "data/jobs.csv"


def create_simulated_new_jobs():
    jobs = pd.read_csv(JOBS_FILE)

    # Take 10 existing jobs and modify their URLs so they behave
    # like newly discovered jobs.
    simulated = jobs.head(10).copy()

    simulated["job_url"] = (
        simulated["job_url"].astype(str)
        + "?simulation=new"
    )

    return simulated


def main():
    print("\n======================================")
    print("TOP 5 SELECTION TEST")
    print("======================================")

    simulated_jobs = create_simulated_new_jobs()

    print(f"\nSimulated jobs: {len(simulated_jobs)}")

    # Check against REAL history.
    new_jobs = filter_new_jobs(simulated_jobs)

    print(f"New simulated jobs: {len(new_jobs)}")

    if new_jobs.empty:
        print("\nERROR: Simulated jobs were not recognized as new.")
        return

    # Do NOT save these jobs to history.
    matcher_jobs = new_jobs.drop(
        columns=["job_key"],
        errors="ignore"
    ).copy()

    print("\nRunning matcher...")

    matched_jobs = match_jobs(matcher_jobs)

    matched_jobs["match_score"] = pd.to_numeric(
        matched_jobs["match_score"],
        errors="coerce"
    )

    matched_jobs = matched_jobs.sort_values(
        by="match_score",
        ascending=False
    )

    top_jobs = matched_jobs.head(5)

    print("\n======================================")
    print("TOP 5 SIMULATED NEW JOBS")
    print("======================================")

    for index, (_, job) in enumerate(
        top_jobs.iterrows(),
        start=1
    ):
        print(
            f"\n{index}. "
            f"{job['title']} | "
            f"{job['company']}"
        )
        print(f"   Score: {job['match_score']}%")
        print(f"   Location: {job['location']}")
        print(f"   URL: {job['job_url']}")

    print("\n======================================")
    print("TEST RESULT")
    print("======================================")
    print(f"Jobs entering matcher: {len(matched_jobs)}")
    print(f"Jobs selected for AI: {len(top_jobs)}")
    print("Real history was NOT modified.")


if __name__ == "__main__":
    main()
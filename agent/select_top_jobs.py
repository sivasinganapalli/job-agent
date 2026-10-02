import pandas as pd

from job_history import filter_new_jobs
from matcher import match_jobs


JOBS_FILE = "data/jobs.csv"
TOP_N = 5


def select_top_new_jobs():

    # -----------------------------------------------------
    # Load current jobs
    # -----------------------------------------------------

    jobs = pd.read_csv(JOBS_FILE)

    print(f"\nTotal jobs scraped: {len(jobs)}")

    # -----------------------------------------------------
    # Remove previously seen jobs
    # -----------------------------------------------------

    new_jobs = filter_new_jobs(jobs)

    print(f"New jobs: {len(new_jobs)}")
    print(
        f"Previously seen jobs: "
        f"{len(jobs) - len(new_jobs)}"
    )

    if new_jobs.empty:

        print("\nNo new jobs available.")

        return pd.DataFrame()

    # -----------------------------------------------------
    # Remove internal job_key before matcher
    #
    # matcher doesn't need this column.
    # -----------------------------------------------------

    matcher_jobs = new_jobs.drop(
        columns=["job_key"],
        errors="ignore"
    ).copy()

    # -----------------------------------------------------
    # Run matcher ONLY on new jobs
    # -----------------------------------------------------

    print("\nRunning matcher on NEW jobs only...")

    matched_jobs = match_jobs(matcher_jobs)

    if matched_jobs.empty:

        print("\nMatcher returned no jobs.")

        return pd.DataFrame()

    # -----------------------------------------------------
    # Sort by score
    # -----------------------------------------------------

    matched_jobs["match_score"] = pd.to_numeric(
        matched_jobs["match_score"],
        errors="coerce"
    )

    matched_jobs = matched_jobs.sort_values(
        by="match_score",
        ascending=False
    )

    # -----------------------------------------------------
    # TOP 5
    # -----------------------------------------------------

    top_jobs = matched_jobs.head(TOP_N).copy()

    print("\n======================================")
    print("TOP NEW JOBS")
    print("======================================")

    print(
        f"\nSelected {len(top_jobs)} jobs "
        f"for AI analysis."
    )

    for index, (_, job) in enumerate(
        top_jobs.iterrows(),
        start=1
    ):

        print(
            f"\n{index}. "
            f"{job['title']} | "
            f"{job['company']}"
        )

        print(
            f"   Score: "
            f"{job['match_score']}%"
        )

        print(
            f"   Location: "
            f"{job['location']}"
        )

        print(
            f"   URL: "
            f"{job['job_url']}"
        )

    return top_jobs


if __name__ == "__main__":

    select_top_new_jobs()
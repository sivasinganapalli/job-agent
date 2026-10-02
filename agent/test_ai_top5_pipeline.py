import pandas as pd

from job_history import filter_new_jobs
from matcher import match_jobs
from ai_analyzer import analyze_job


JOBS_FILE = "data/jobs.csv"
SIMULATED_JOB_COUNT = 10
TOP_N = 5


def create_simulated_new_jobs():
    jobs = pd.read_csv(JOBS_FILE)

    simulated = jobs.head(SIMULATED_JOB_COUNT).copy()

    # Use synthetic URLs so history treats them as genuinely new.
    simulated["job_url"] = [
        f"https://simulation.test/job/{i}"
        for i in range(len(simulated))
    ]

    return simulated

def main():
    print("\n======================================")
    print("AI TOP-5 PIPELINE TEST")
    print("======================================")

    jobs = create_simulated_new_jobs()

    print(f"\nSimulated jobs: {len(jobs)}")

    # Check against real history.
    new_jobs = filter_new_jobs(jobs)

    print(f"New simulated jobs: {len(new_jobs)}")

    if new_jobs.empty:
        print("\nERROR: No simulated new jobs found.")
        return

    # Matcher
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

    top_jobs = matched_jobs.head(TOP_N).copy()

    print(f"\nJobs sent to matcher: {len(matcher_jobs)}")
    print(f"Jobs returned by matcher: {len(matched_jobs)}")
    print(f"Jobs selected for AI: {len(top_jobs)}")

    print("\n======================================")
    print("SENDING TOP 5 TO OPENAI")
    print("======================================")

    # Map selected jobs back to the original rows so that
    # the AI receives the complete job description.
    selected_urls = set(top_jobs["job_url"])

    selected_original_jobs = new_jobs[
        new_jobs["job_url"].isin(selected_urls)
    ].copy()

    if len(selected_original_jobs) != len(top_jobs):
        print("\nERROR: Could not map all Top 5 jobs back to descriptions.")
        print(
            f"Top jobs: {len(top_jobs)} | "
            f"Mapped jobs: {len(selected_original_jobs)}"
        )
        return

    ai_results = []

    for index, (_, job) in enumerate(
        selected_original_jobs.iterrows(),
        start=1
    ):
        print(
            f"\n[{index}/{len(selected_original_jobs)}] "
            f"{job['title']} | {job['company']}"
        )

        try:
            result = analyze_job(job)

            ai_results.append({
                "title": job["title"],
                "company": job["company"],
                "job_url": job["job_url"],
                "result": result,
            })

            print(f"AI Fit: {result.get('fit')}")
            print(
                f"Experience Fit: "
                f"{result.get('experience_fit')}"
            )
            print(
                f"Role Alignment: "
                f"{result.get('role_alignment')}"
            )
            print(
                f"Priority: "
                f"{result.get('priority')}"
            )

        except Exception as error:
            print(f"AI ERROR: {error}")

    print("\n======================================")
    print("PIPELINE VALIDATION")
    print("======================================")

    print(f"Top jobs selected: {len(top_jobs)}")
    print(f"AI analyses completed: {len(ai_results)}")

    if len(ai_results) == TOP_N:
        print("\nSUCCESS: Exactly 5 jobs were analyzed by OpenAI.")
    else:
        print(
            f"\nWARNING: Expected {TOP_N} AI analyses, "
            f"but completed {len(ai_results)}."
        )

    print("\nIMPORTANT:")
    print("Real job_history.csv was NOT modified.")


if __name__ == "__main__":
    main()
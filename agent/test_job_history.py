import pandas as pd

from job_history import (
    create_job_key,
    filter_new_jobs,
    get_history_stats,
    load_history,
    mark_jobs_seen,
)


# ---------------------------------------------------------
# Load current jobs
# ---------------------------------------------------------

jobs = pd.read_csv("data/jobs.csv")

print("\n======================================")
print("JOB HISTORY / DEDUPLICATION TEST")
print("======================================")

print(f"\nJobs currently in jobs.csv: {len(jobs)}")


# ---------------------------------------------------------
# Check job keys
# ---------------------------------------------------------

print("\nGenerating job keys...")

jobs["job_key"] = jobs.apply(
    create_job_key,
    axis=1,
)

print("\nExample job keys:")

for _, job in jobs.head(5).iterrows():
    print(
        f"{job['company']} | "
        f"{job['title']} | "
        f"{job['job_key']}"
    )


# ---------------------------------------------------------
# Find jobs that are genuinely new
# ---------------------------------------------------------

new_jobs = filter_new_jobs(jobs)

print("\n======================================")
print("NEW JOBS")
print("======================================")

print(f"\nNew jobs: {len(new_jobs)}")
print(f"Previously seen: {len(jobs) - len(new_jobs)}")


# ---------------------------------------------------------
# Show new jobs
# ---------------------------------------------------------

if not new_jobs.empty:

    print("\nNew jobs found:")

    for _, job in new_jobs.iterrows():

        print(
            f"- {job['title']} | "
            f"{job['company']} | "
            f"{job['location']}"
        )

else:

    print("\nNo new jobs found.")


# ---------------------------------------------------------
# Mark current jobs as seen
# ---------------------------------------------------------

print("\nSaving current jobs to history...")

mark_jobs_seen(jobs)


# ---------------------------------------------------------
# Verify history
# ---------------------------------------------------------

history = load_history()
stats = get_history_stats()

print("\n======================================")
print("HISTORY")
print("======================================")

print(f"Total jobs in history: {stats['total_seen']}")
print(f"AI analyzed: {stats['ai_analyzed']}")

print("\nHistory file:")
print("data/job_history.csv")


# ---------------------------------------------------------
# Test again
# ---------------------------------------------------------

new_jobs_again = filter_new_jobs(jobs)

print("\n======================================")
print("SECOND DEDUPLICATION TEST")
print("======================================")

print(
    f"New jobs after saving history: "
    f"{len(new_jobs_again)}"
)

if len(new_jobs_again) == 0:
    print("\nSUCCESS: Duplicate filtering is working.")

else:
    print(
        "\nWARNING: Some jobs were still detected "
        "as new."
    )
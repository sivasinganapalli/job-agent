import pandas as pd

from matcher import match_jobs


JOBS_FILE = "data/jobs.csv"
TEST_JOB_COUNT = 10
TOP_N = 5


print("\n======================================")
print("TOP 5 SELECTION TEST")
print("======================================")


# ---------------------------------------------------------
# Load jobs
# ---------------------------------------------------------

jobs = pd.read_csv(JOBS_FILE)

print(f"\nJobs available: {len(jobs)}")


# ---------------------------------------------------------
# Simulate 10 NEW jobs
#
# We only use these jobs for testing.
# Nothing is written to job_history.csv.
# ---------------------------------------------------------

test_jobs = jobs.head(TEST_JOB_COUNT).copy()

print(
    f"Simulating {len(test_jobs)} new jobs..."
)


# ---------------------------------------------------------
# Run the existing matcher
# ---------------------------------------------------------

matched_jobs = match_jobs()

if matched_jobs.empty:
    print("\nMatcher returned no jobs.")
    raise SystemExit


# ---------------------------------------------------------
# Convert match score to number
# ---------------------------------------------------------

matched_jobs["match_score"] = pd.to_numeric(
    matched_jobs["match_score"],
    errors="coerce",
)


# ---------------------------------------------------------
# Match our simulated jobs against matcher results
# ---------------------------------------------------------

test_urls = set(
    test_jobs["job_url"]
    .fillna("")
    .astype(str)
)

matched_test_jobs = matched_jobs[
    matched_jobs["job_url"]
    .fillna("")
    .astype(str)
    .isin(test_urls)
].copy()


# ---------------------------------------------------------
# Sort by matcher score
# ---------------------------------------------------------

matched_test_jobs = matched_test_jobs.sort_values(
    by="match_score",
    ascending=False,
)


# ---------------------------------------------------------
# Select TOP 5
# ---------------------------------------------------------

top5 = matched_test_jobs.head(TOP_N)


# ---------------------------------------------------------
# Display
# ---------------------------------------------------------

print("\n======================================")
print("TOP 5 NEW JOBS")
print("======================================")

print(
    f"\nJobs sent to matcher: "
    f"{len(test_jobs)}"
)

print(
    f"Jobs returned by matcher: "
    f"{len(matched_test_jobs)}"
)

print(
    f"Jobs selected for AI: "
    f"{len(top5)}"
)


for index, (_, job) in enumerate(
    top5.iterrows(),
    start=1,
):

    print(
        f"\n{index}. "
        f"{job['title']} | "
        f"{job['company']}"
    )

    print(
        f"   Match Score: "
        f"{job['match_score']}%"
    )

    print(
        f"   Location: "
        f"{job['location']}"
    )


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("\n======================================")
print("VALIDATION")
print("======================================")

if len(top5) <= TOP_N:

    print(
        f"SUCCESS: No more than {TOP_N} jobs "
        f"were selected."
    )

else:

    print(
        "ERROR: More than 5 jobs were selected."
    )


print("\njob_history.csv was NOT modified.")
print("======================================")

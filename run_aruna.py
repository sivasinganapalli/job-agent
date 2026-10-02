import os

from agent.aruna_job_search import search_jobs
from agent.aruna_matcher import match_jobs
from agent.aruna_job_history import (
    filter_new_jobs,
    mark_jobs_processed,
)
from agent.aruna_email import (
    generate_digest,
    send_email,
)


JOBS_FILE = "data/aruna_jobs.csv"


def save_jobs(jobs):
    """
    Save the jobs collected and matched by the Aruna agent.
    """

    os.makedirs("data", exist_ok=True)

    if jobs.empty:
        print("No jobs to save.")
        return

    jobs.to_csv(
        JOBS_FILE,
        index=False,
    )

    print(
        f"Saved {len(jobs)} jobs to "
        f"{JOBS_FILE}"
    )


def main():

    print("=" * 50)
    print("ARUNA LINUX JOB AGENT")
    print("=" * 50)

    # ==================================================
    # 1. SEARCH JOB SITES
    # ==================================================

    print(
        "\n[1/6] Searching job sites..."
    )

    jobs = search_jobs()

    print(
        f"\nTotal unique jobs collected: "
        f"{len(jobs)}"
    )

    if jobs.empty:

        print(
            "\nNo jobs were found from any source."
        )

        return

    # ==================================================
    # 2. APPLY ARUNA PROFILE MATCHING
    # ==================================================

    print(
        "\n[2/6] Applying Aruna profile matching..."
    )

    jobs = match_jobs(jobs)

    print(
        f"Jobs matching Aruna profile: "
        f"{len(jobs)}"
    )

    if jobs.empty:

        print(
            "\nNo jobs matched the Aruna profile."
        )

        # Save empty/matched result
        save_jobs(jobs)

        return

    # ==================================================
    # 3. SAVE CURRENT JOB RESULTS
    # ==================================================

    print(
        "\n[3/6] Saving matched jobs..."
    )

    save_jobs(jobs)

    # ==================================================
    # 4. CHECK JOB HISTORY
    # ==================================================

    print(
        "\n[4/6] Checking previously processed jobs..."
    )

    new_jobs = filter_new_jobs(jobs)

    print(
        f"\nNew jobs ready for email: "
        f"{len(new_jobs)}"
    )

    if new_jobs.empty:

        print(
            "\nNo new jobs available."
        )

        return

    # ==================================================
    # 5. GENERATE AND SEND EMAIL
    # ==================================================

    print(
        "\n[5/6] Generating email digest..."
    )

    digest_file = generate_digest(
        new_jobs
    )

    print(
        "\nSending email..."
    )

    try:

        send_email(
            digest_file,
            len(new_jobs),
        )

    except Exception as exc:

        print(
            "\nEMAIL FAILED:"
        )

        print(exc)

        print(
            "\nJobs were NOT marked as processed."
        )

        print(
            "They will be available for retry "
            "on the next run."
        )

        return

    # ==================================================
    # 6. UPDATE HISTORY
    # ==================================================

    print(
        "\n[6/6] Updating job history..."
    )

    mark_jobs_processed(
        new_jobs
    )

    print("\n" + "=" * 50)
    print("ARUNA JOB AGENT COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    main()
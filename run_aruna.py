import os

import pandas as pd

from agent.ai_analyzer import analyze_job
from agent.aruna_ai_queue import (
    load_ai_queue,
    merge_queue_jobs,
    save_ai_queue,
    select_ai_batch,
)
from agent.aruna_email import (
    generate_digest,
    send_email,
)
from agent.aruna_job_history import (
    filter_new_jobs,
    mark_jobs_processed,
)
from agent.aruna_job_search import search_jobs
from agent.aruna_matcher import match_jobs


JOBS_FILE = "data/aruna_jobs.csv"
AI_BATCH_SIZE = 7


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


def is_ai_approved(analysis):
    """Keep only jobs that are plausibly worth emailing after AI review."""

    if not isinstance(analysis, dict):
        return False

    fit = str(analysis.get("fit", "")).strip().lower()
    role_alignment = str(analysis.get("role_alignment", "")).strip().lower()
    priority = str(analysis.get("priority", "")).strip().lower()

    if priority in {"high", "medium"} and fit in {"strong", "good", "moderate"}:
        return True

    if role_alignment in {"strong", "good", "moderate"} and fit in {"strong", "good"}:
        return True

    return False


def build_ai_result(job, analysis):
    return {
        "job_key": job.get("job_key", ""),
        "job_url": job.get("job_url", ""),
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "source": job.get("search_site", job.get("site", "")),
        "date_posted": job.get("date_posted", ""),
        "match_score": job.get("match_score", ""),
        "analysis": analysis,
    }


def build_ai_approved_row(job, analysis):
    row = job.copy()
    row["ai_fit"] = analysis.get("fit", "")
    row["ai_priority"] = analysis.get("priority", "")
    row["ai_role_alignment"] = analysis.get("role_alignment", "")
    row["ai_experience_fit"] = analysis.get("experience_fit", "")
    row["ai_summary"] = analysis.get("summary", "")
    row["ai_concerns"] = ", ".join(analysis.get("concerns", []))
    return row


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
    # 4. CHECK HISTORY + AI QUEUE
    # ==================================================

    print(
        "\n[4/6] Checking previously processed jobs and AI queue..."
    )

    new_jobs = filter_new_jobs(jobs)
    queue = load_ai_queue()
    queued_jobs = merge_queue_jobs(new_jobs, queue)

    print(
        f"\nJobs waiting for AI validation: "
        f"{len(queued_jobs)}"
    )

    if queued_jobs.empty:
        print("\nNo new jobs available.")
        return

    ai_batch, carry_forward = select_ai_batch(queued_jobs, batch_size=AI_BATCH_SIZE)

    print(
        f"AI batch selected: {len(ai_batch)}"
    )
    print(
        f"Jobs carried forward: {len(carry_forward)}"
    )

    if ai_batch.empty:
        print("\nNo jobs available for AI validation.")
        return

    # update the queue with carry-forward jobs first
    queue_to_save = carry_forward.copy()

    # ==================================================
    # 5. AI VALIDATION
    # ==================================================

    print(
        "\n[5/6] Running AI validation on top 7 jobs..."
    )

    ai_results = []
    approved_jobs = []
    rejected_jobs = []

    for index, (_, job) in enumerate(ai_batch.iterrows(), start=1):
        print(
            f"\nAI [{index}/{len(ai_batch)}] "
            f"{job.get('title', '')} | {job.get('company', '')}"
        )

        try:
            analysis = analyze_job(job)
            ai_results.append(build_ai_result(job, analysis))

            if is_ai_approved(analysis):
                approved_jobs.append(build_ai_approved_row(job, analysis))
                print(f"   AI decision: Approved ({analysis.get('priority', '')})")
            else:
                rejected_jobs.append(job)
                print(f"   AI decision: Rejected ({analysis.get('priority', '')})")

        except Exception as exc:
            print(f"   AI ERROR: {exc}")
            rejected_jobs.append(job)

    if approved_jobs:
        approved_df = pd.DataFrame(approved_jobs)
        print(f"\nApproved by AI: {len(approved_df)}")

        queue_to_save = merge_queue_jobs(rejected_jobs, queue_to_save)

        digest_file = generate_digest(approved_df)

        print("\nSending email...")

        try:
            send_email(
                digest_file,
                len(approved_df),
            )

            print("\n[6/6] Updating job history...")
            mark_jobs_processed(approved_df)

            # Only save queue after successful email; these jobs are now processed.
            queue_to_save = merge_queue_jobs(rejected_jobs, carry_forward)
            save_ai_queue(queue_to_save)

        except Exception as exc:
            print("\nEMAIL FAILED:")
            print(exc)
            print("\nAI-approved jobs will remain queued and be retried later.")
            queue_to_save = merge_queue_jobs(pd.concat([carry_forward, rejected_jobs, approved_df], ignore_index=True), queue)
            save_ai_queue(queue_to_save)

            return

    else:
        print("\nNo jobs were approved by AI.")
        queue_to_save = merge_queue_jobs(rejected_jobs, carry_forward)
        save_ai_queue(queue_to_save)
        print("\nJobs remain queued for the next AI validation run.")
        return

    print("\n" + "=" * 50)
    print("ARUNA JOB AGENT COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    main()
import os
import pandas as pd

from agent.email_digest import generate_digest
from agent.job_search import search_jobs
from agent.save_jobs import save_jobs

from agent.job_history import (
    load_history,
    save_history,
    filter_new_jobs,
    create_job_key,
    normalize_url,
)

from agent.matcher import match_jobs
from agent.ai_analyzer import analyze_job
from agent.email_sender import send_email


JOBS_FILE = "data/jobs.csv"
AI_RESULTS_FILE = "data/ai_results.csv"

TOP_N = 5


def update_history_after_processing(
    new_jobs,
    matched_jobs,
    ai_results,
):
    """
    Update job history after processing.

    Successfully AI-analyzed jobs are marked:
        ai_analyzed = True

    Jobs where AI failed are marked:
        ai_analyzed = False

    This allows failed jobs to be retried later.
    """

    history = load_history()

    today = pd.Timestamp.now().strftime(
        "%Y-%m-%d"
    )

    # -------------------------------------------------
    # Matcher scores by normalized URL
    # -------------------------------------------------

    matcher_scores = {}

    for _, job in matched_jobs.iterrows():

        url = normalize_url(
            job.get(
                "job_url",
                ""
            )
        )

        if url:

            matcher_scores[url] = job.get(
                "match_score",
                ""
            )

    # -------------------------------------------------
    # Successfully analyzed jobs
    # -------------------------------------------------

    analyzed_urls = set()

    for result in ai_results:

        url = normalize_url(
            result.get(
                "job_url",
                ""
            )
        )

        if url:

            analyzed_urls.add(url)

    # -------------------------------------------------
    # Update history
    # -------------------------------------------------

    for _, job in new_jobs.iterrows():

        job_dict = job.to_dict()

        job_key = create_job_key(
            job_dict
        )

        job_url = normalize_url(
            job_dict.get(
                "job_url",
                ""
            )
        )

        matcher_score = matcher_scores.get(
            job_url,
            ""
        )

        ai_analyzed = (
            job_url in analyzed_urls
        )

        existing = (
            history["job_key"]
            == job_key
        )

        if existing.any():

            index = history.index[
                existing
            ][0]

            history.at[
                index,
                "last_seen"
            ] = today

            if matcher_score != "":

                history.at[
                    index,
                    "matcher_score"
                ] = matcher_score

            history.at[
                index,
                "ai_analyzed"
            ] = ai_analyzed

        else:

            new_row = {
                "job_key": job_key,
                "job_url": job_url,
                "title": job_dict.get(
                    "title",
                    ""
                ),
                "company": job_dict.get(
                    "company",
                    ""
                ),
                "location": job_dict.get(
                    "location",
                    ""
                ),
                "date_posted": job_dict.get(
                    "date_posted",
                    ""
                ),
                "first_seen": today,
                "last_seen": today,
                "matcher_score": matcher_score,
                "ai_analyzed": ai_analyzed,
            }

            history = pd.concat(
                [
                    history,
                    pd.DataFrame(
                        [new_row]
                    ),
                ],
                ignore_index=True,
            )

    save_history(history)


def save_ai_results(ai_results):
    """
    Save successful AI analysis results to CSV.
    """

    if not ai_results:

        print(
            "No AI results to save."
        )

        return

    os.makedirs(
        "data",
        exist_ok=True
    )

    rows = []

    for result in ai_results:

        ai = result["analysis"]

        rows.append(
            {
                "analyzed_at":
                    pd.Timestamp.now().isoformat(),

                "title":
                    result["title"],

                "company":
                    result["company"],

                "location":
                    result["location"],

                "job_url":
                    result["job_url"],

                "match_score":
                    result["match_score"],

                "fit":
                    ai.get(
                        "fit",
                        ""
                    ),

                "experience_fit":
                    ai.get(
                        "experience_fit",
                        ""
                    ),

                "role_alignment":
                    ai.get(
                        "role_alignment",
                        ""
                    ),

                "matched_skills":
                    ", ".join(
                        ai.get(
                            "matched_skills",
                            []
                        )
                    ),

                "missing_core_skills":
                    ", ".join(
                        ai.get(
                            "missing_core_skills",
                            []
                        )
                    ),

                "missing_nice_to_have_skills":
                    ", ".join(
                        ai.get(
                            "missing_nice_to_have_skills",
                            []
                        )
                    ),

                "transferable_skills":
                    ", ".join(
                        ai.get(
                            "transferable_skills",
                            []
                        )
                    ),

                "key_requirements":
                    " | ".join(
                        ai.get(
                            "key_requirements",
                            []
                        )
                    ),

                "concerns":
                    " | ".join(
                        ai.get(
                            "concerns",
                            []
                        )
                    ),

                "summary":
                    ai.get(
                        "summary",
                        ""
                    ),

                "priority":
                    ai.get(
                        "priority",
                        ""
                    ),
            }
        )

    df = pd.DataFrame(rows)

    # Append instead of overwriting.
    if os.path.exists(
        AI_RESULTS_FILE
    ):

        existing = pd.read_csv(
            AI_RESULTS_FILE
        )

        df = pd.concat(
            [
                existing,
                df,
            ],
            ignore_index=True,
        )

    df.to_csv(
        AI_RESULTS_FILE,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Saved {len(ai_results)} AI results "
        f"to {AI_RESULTS_FILE}"
    )


def run_agent():

    print(
        "\n======================================"
    )

    print(
        "SIVA JOB AGENT"
    )

    print(
        "======================================"
    )

    # =================================================
    # 1. SEARCH
    # =================================================

    print(
        "\n[1/7] Searching jobs..."
    )

    jobs = search_jobs()

    if jobs is None or jobs.empty:

        print(
            "No jobs found."
        )

        return

    print(
        f"Jobs scraped: {len(jobs)}"
    )

    # =================================================
    # 2. SAVE RAW JOBS
    # =================================================

    print(
        "\n[2/7] Saving jobs..."
    )

    save_jobs(jobs)

    # =================================================
    # 3. FILTER HISTORY
    # =================================================

    print(
        "\n[3/7] Filtering previously "
        "processed jobs..."
    )

    new_jobs = filter_new_jobs(
        jobs
    )

    previously_processed = (
        len(jobs)
        - len(new_jobs)
    )

    print(
        f"New/unprocessed jobs: "
        f"{len(new_jobs)}"
    )

    print(
        f"Previously processed: "
        f"{previously_processed}"
    )

    if new_jobs.empty:

        print(
            "\nNo new jobs available."
        )

        return

    # =================================================
    # 4. MATCHER
    # =================================================

    print(
        "\n[4/7] Running matcher..."
    )

    matcher_jobs = new_jobs.drop(
        columns=[
            "job_key"
        ],
        errors="ignore",
    ).copy()

    matched_jobs = match_jobs(
        matcher_jobs
    )

    if matched_jobs.empty:

        print(
            "\nMatcher returned no jobs."
        )

        return

    matched_jobs["match_score"] = (
        pd.to_numeric(
            matched_jobs[
                "match_score"
            ],
            errors="coerce",
        )
    )

    matched_jobs = (
        matched_jobs
        .sort_values(
            by="match_score",
            ascending=False,
        )
    )

    print(
        f"Jobs matched: "
        f"{len(matched_jobs)}"
    )

    # =================================================
    # 5. TOP 5
    # =================================================

    print(
        "\n[5/7] Selecting Top 5..."
    )

    top_jobs = (
        matched_jobs
        .head(TOP_N)
        .copy()
    )

    print(
        f"Jobs selected for AI: "
        f"{len(top_jobs)}"
    )

    for index, (_, job) in enumerate(
        top_jobs.iterrows(),
        start=1,
    ):

        print(
            f"\n{index}. "
            f"{job['title']} | "
            f"{job['company']}"
        )

        print(
            f"   Match: "
            f"{job['match_score']}%"
        )

    # =================================================
    # Map Top 5 back to original jobs
    # =================================================

    selected_urls = set(
        top_jobs[
            "job_url"
        ].astype(str)
    )

    selected_original_jobs = (
        new_jobs[
            new_jobs[
                "job_url"
            ]
            .astype(str)
            .isin(
                selected_urls
            )
        ]
        .copy()
    )

    if (
        len(selected_original_jobs)
        != len(top_jobs)
    ):

        print(
            "\nERROR: Could not map Top jobs "
            "back to original job descriptions."
        )

        return

    # =================================================
    # 6. OPENAI
    # =================================================

    print(
        "\n[6/7] Running OpenAI analysis..."
    )

    ai_results = []

    for index, (_, job) in enumerate(
        selected_original_jobs.iterrows(),
        start=1,
    ):

        print(
            f"\nAI [{index}/"
            f"{len(selected_original_jobs)}] "
            f"{job['title']} | "
            f"{job['company']}"
        )

        try:

            analysis = analyze_job(
                job
            )

            # Find matcher score
            matched_row = top_jobs[
                top_jobs[
                    "job_url"
                ]
                == job[
                    "job_url"
                ]
            ]

            if not matched_row.empty:

                match_score = (
                    matched_row.iloc[0][
                        "match_score"
                    ]
                )

            else:

                match_score = ""

            ai_results.append(
                {
                    "title":
                        job["title"],

                    "company":
                        job["company"],

                    "location":
                        job["location"],

                    "job_url":
                        job["job_url"],

                    "match_score":
                        match_score,

                    "analysis":
                        analysis,
                }
            )

            print(
                f"   AI Fit: "
                f"{analysis.get('fit')}"
            )

            print(
                f"   Experience Fit: "
                f"{analysis.get('experience_fit')}"
            )

            print(
                f"   Role Alignment: "
                f"{analysis.get('role_alignment')}"
            )

            print(
                f"   Priority: "
                f"{analysis.get('priority')}"
            )

        except Exception as error:

            print(
                f"   AI ERROR: {error}"
            )

            print(
                "   Job will remain "
                "eligible for retry."
            )

    # =================================================
    # If all AI calls failed
    # =================================================

    if not ai_results:

        print(
            "\nNo successful AI analyses."
        )

        print(
            "Skipping digest and email."
        )

        print(
            "\nUpdating job history..."
        )

        update_history_after_processing(
            new_jobs,
            matched_jobs,
            ai_results,
        )

        print(
            "\n======================================"
        )

        print(
            "AGENT RUN COMPLETE"
        )

        print(
            "======================================"
        )

        print(
            f"Jobs scraped: {len(jobs)}"
        )

        print(
            f"New/unprocessed jobs: "
            f"{len(new_jobs)}"
        )

        print(
            f"Matched jobs: "
            f"{len(matched_jobs)}"
        )

        print(
            "AI analyzed: 0"
        )

        print(
            "Email: Not sent"
        )

        return

    # =================================================
    # SAVE AI RESULTS
    # =================================================

    print(
        "\nSaving AI results..."
    )

    save_ai_results(
        ai_results
    )

    # =================================================
    # GENERATE EMAIL DIGEST
    # =================================================

    print(
        "\nGenerating email digest..."
    )

    digest_file = generate_digest()

    # =================================================
    # SEND EMAIL
    # =================================================

    print(
        "\nSending email..."
    )

    if digest_file:

        try:

            send_email(
                digest_file,
                subject=(
                    "Siva Job Agent — "
                    f"{len(ai_results)} "
                    "New Job(s)"
                ),
            )

        except Exception as error:

            print(
                f"Email sending FAILED: "
                f"{error}"
            )

            print(
                "AI results were saved."
            )

    else:

        print(
            "No digest generated."
        )

        print(
            "Email not sent."
        )

    # =================================================
    # 7. UPDATE HISTORY
    # =================================================

    print(
        "\n[7/7] Updating job history..."
    )

    update_history_after_processing(
        new_jobs,
        matched_jobs,
        ai_results,
    )

    # =================================================
    # FINAL SUMMARY
    # =================================================

    print(
        "\n======================================"
    )

    print(
        "AGENT RUN COMPLETE"
    )

    print(
        "======================================"
    )

    print(
        f"Jobs scraped: {len(jobs)}"
    )

    print(
        f"New/unprocessed jobs: "
        f"{len(new_jobs)}"
    )

    print(
        f"Matched jobs: "
        f"{len(matched_jobs)}"
    )

    print(
        f"AI analyzed: "
        f"{len(ai_results)}"
    )

    print(
        "Email: Sent/Attempted"
    )


if __name__ == "__main__":

    run_agent()
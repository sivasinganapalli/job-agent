import pandas as pd

from agent.aruna_ai_queue import select_ai_batch, merge_queue_jobs
from run_aruna import build_ai_approved_row


def test_select_ai_batch_returns_top_seven_and_keeps_remainder():
    jobs = pd.DataFrame(
        [
            {"job_key": "k1", "title": "J1", "match_score": 98},
            {"job_key": "k2", "title": "J2", "match_score": 94},
            {"job_key": "k3", "title": "J3", "match_score": 90},
            {"job_key": "k4", "title": "J4", "match_score": 88},
            {"job_key": "k5", "title": "J5", "match_score": 87},
            {"job_key": "k6", "title": "J6", "match_score": 85},
            {"job_key": "k7", "title": "J7", "match_score": 83},
            {"job_key": "k8", "title": "J8", "match_score": 82},
            {"job_key": "k9", "title": "J9", "match_score": 81},
        ]
    )

    batch, remainder = select_ai_batch(jobs, batch_size=7)

    assert len(batch) == 7
    assert list(batch["job_key"]) == ["k1", "k2", "k3", "k4", "k5", "k6", "k7"]
    assert len(remainder) == 2
    assert list(remainder["job_key"]) == ["k8", "k9"]


def test_merge_queue_jobs_keeps_latest_match_score_and_dedupes():
    current = pd.DataFrame(
        [
            {"job_key": "a", "title": "A", "match_score": 90},
            {"job_key": "b", "title": "B", "match_score": 80},
        ]
    )

    previous = pd.DataFrame(
        [
            {"job_key": "b", "title": "B", "match_score": 70},
            {"job_key": "c", "title": "C", "match_score": 60},
        ]
    )

    merged = merge_queue_jobs(current, previous)

    assert len(merged) == 3
    assert set(merged["job_key"]) == {"a", "b", "c"}
    assert merged[merged["job_key"] == "b"].iloc[0]["match_score"] == 80


def test_build_ai_approved_row_includes_ai_decision_and_summary():
    job = {
        "job_key": "k1",
        "title": "Linux Administrator",
        "company": "Acme",
        "location": "Hyderabad",
        "match_score": 90,
    }

    analysis = {
        "fit": "Strong",
        "priority": "High",
        "role_alignment": "Strong",
        "experience_fit": "Good",
        "summary": "Excellent Linux admin fit.",
    }

    row = build_ai_approved_row(job, analysis)

    assert row["ai_fit"] == "Strong"
    assert row["ai_priority"] == "High"
    assert row["ai_role_alignment"] == "Strong"
    assert row["ai_experience_fit"] == "Good"
    assert row["ai_summary"] == "Excellent Linux admin fit."

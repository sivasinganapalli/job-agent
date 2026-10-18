import os
import pandas as pd


AI_QUEUE_FILE = "data/aruna_ai_queue.csv"
DEFAULT_BATCH_SIZE = 7


def ensure_ai_queue_file():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(AI_QUEUE_FILE):
        pd.DataFrame(columns=["job_key", "job_url", "title", "company", "location", "match_score"]).to_csv(
            AI_QUEUE_FILE,
            index=False,
        )


def load_ai_queue():
    ensure_ai_queue_file()
    queue = pd.read_csv(AI_QUEUE_FILE)
    if queue.empty:
        return queue
    queue["job_key"] = queue["job_key"].fillna("").astype(str)
    return queue


def save_ai_queue(queue):
    ensure_ai_queue_file()
    queue = queue.copy()
    queue.to_csv(AI_QUEUE_FILE, index=False)


def select_ai_batch(jobs, batch_size=DEFAULT_BATCH_SIZE):
    """
    Take the highest-scoring jobs for AI validation and return the remaining jobs as a carry-forward queue.
    """
    if jobs.empty:
        return pd.DataFrame(columns=jobs.columns), pd.DataFrame(columns=jobs.columns)

    ordered = jobs.copy()
    if "match_score" in ordered.columns:
        ordered["match_score"] = pd.to_numeric(ordered["match_score"], errors="coerce")
        ordered = ordered.sort_values(by="match_score", ascending=False, na_position="last")

    batch = ordered.head(batch_size).copy().reset_index(drop=True)
    remainder = ordered.iloc[batch_size:].copy().reset_index(drop=True)
    return batch, remainder


def merge_queue_jobs(current_jobs, queued_jobs):
    """
    Merge the carry-forward queue with the newly matched jobs, keeping the newest score on duplicates.
    """
    if isinstance(current_jobs, list):
        current_jobs = pd.DataFrame(current_jobs)
    if isinstance(queued_jobs, list):
        queued_jobs = pd.DataFrame(queued_jobs)

    if current_jobs is None or (hasattr(current_jobs, "empty") and current_jobs.empty):
        current_jobs = pd.DataFrame(columns=["job_key", "job_url", "title", "company", "location", "match_score"])
    if queued_jobs is None or (hasattr(queued_jobs, "empty") and queued_jobs.empty):
        queued_jobs = pd.DataFrame(columns=["job_key", "job_url", "title", "company", "location", "match_score"])

    combined = pd.concat([current_jobs, queued_jobs], ignore_index=True)

    if combined.empty:
        return combined

    if "match_score" in combined.columns:
        combined["match_score"] = pd.to_numeric(combined["match_score"], errors="coerce")

    combined = combined.drop_duplicates(subset=["job_key"], keep="first")
    combined = combined.sort_values(by="match_score", ascending=False, na_position="last")
    return combined.reset_index(drop=True)


def enqueue_remaining_jobs(jobs):
    """Persist jobs that were not sent for AI this cycle."""
    queue = load_ai_queue()
    merged = merge_queue_jobs(jobs, queue)
    save_ai_queue(merged)
    return merged


def pull_ai_queue():
    queue = load_ai_queue()
    if queue.empty:
        return pd.DataFrame(columns=["job_key", "job_url", "title", "company", "location", "match_score"])
    return queue.reset_index(drop=True)


def clear_ai_queue():
    save_ai_queue(pd.DataFrame(columns=["job_key", "job_url", "title", "company", "location", "match_score"]))

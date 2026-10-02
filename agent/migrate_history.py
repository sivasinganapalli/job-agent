import pandas as pd

from job_history import (
    HISTORY_FILE,
    HISTORY_COLUMNS,
    create_job_key,
    load_history,
    save_history,
)


print("\n======================================")
print("JOB HISTORY MIGRATION")
print("======================================")

# ---------------------------------------------------------
# Load existing history
# ---------------------------------------------------------

history = load_history()

print(f"\nHistory records before migration: {len(history)}")


if history.empty:
    print("No history found. Nothing to migrate.")
    raise SystemExit


# ---------------------------------------------------------
# Recalculate job keys
# ---------------------------------------------------------

print("\nRecalculating job keys...")

history["job_key"] = history.apply(
    create_job_key,
    axis=1,
)


# ---------------------------------------------------------
# Remove duplicate job keys
# ---------------------------------------------------------

before_dedup = len(history)

history = history.drop_duplicates(
    subset=["job_key"],
    keep="first",
).copy()

duplicates_removed = before_dedup - len(history)


# ---------------------------------------------------------
# Save migrated history
# ---------------------------------------------------------

history = history[HISTORY_COLUMNS]

save_history(history)


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print("\n======================================")
print("MIGRATION COMPLETE")
print("======================================")

print(f"\nRecords before migration: {before_dedup}")
print(f"Duplicate records removed: {duplicates_removed}")
print(f"Records after migration: {len(history)}")

print("\nHistory file:")
print(HISTORY_FILE)

print("\nExpected result for your current dataset:")
print("31 jobs in jobs.csv")
print("31 unique jobs in job_history.csv")

import pandas as pd

from ai_analyzer import analyze_job


# Load existing jobs
jobs = pd.read_csv("data/jobs.csv")

# Test only ONE job first.
job = jobs.iloc[0].to_dict()

print("\nAnalyzing:")
print("Title:", job.get("title"))
print("Company:", job.get("company"))

result = analyze_job(job)

print("\n===== AI JOB ANALYSIS =====")

for key, value in result.items():
    print(f"\n{key}:")
    print(value)
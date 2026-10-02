import os
from datetime import datetime

import pandas as pd


AI_RESULTS_FILE = "data/ai_results.csv"
OUTPUT_FILE = "data/daily_digest.html"


def load_ai_results():
    if not os.path.exists(AI_RESULTS_FILE):
        return pd.DataFrame()

    df = pd.read_csv(AI_RESULTS_FILE)

    if df.empty:
        return df

    return df


def safe(value):
    if pd.isna(value):
        return ""
    return str(value)


def make_list(value):
    if pd.isna(value) or not str(value).strip():
        return []

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def priority_class(priority):
    priority = safe(priority).lower()

    if priority == "high":
        return "high"

    if priority == "medium":
        return "medium"

    return "low"


def generate_digest():
    df = load_ai_results()

    if df.empty:
        print("No AI results available.")
        return None

    # Today's results only
    today = datetime.now().strftime("%Y-%m-%d")

    if "analyzed_at" in df.columns:
        df["analyzed_at"] = pd.to_datetime(
            df["analyzed_at"],
            errors="coerce"
        )

        today_results = df[
            df["analyzed_at"].dt.strftime("%Y-%m-%d") == today
        ].copy()

    else:
        today_results = df.copy()

    if today_results.empty:
        print("No AI results for today.")
        return None

    # Highest matcher score first
    today_results["match_score"] = pd.to_numeric(
        today_results["match_score"],
        errors="coerce"
    )

    today_results = today_results.sort_values(
        by="match_score",
        ascending=False
    )

    total_jobs = len(today_results)

    high_count = (
        today_results["priority"]
        .astype(str)
        .str.lower()
        .eq("high")
        .sum()
    )

    medium_count = (
        today_results["priority"]
        .astype(str)
        .str.lower()
        .eq("medium")
        .sum()
    )

    low_count = (
        today_results["priority"]
        .astype(str)
        .str.lower()
        .eq("low")
        .sum()
    )

    cards = []

    for index, job in enumerate(today_results.iterrows(), start=1):

        _, job = job

        title = safe(job.get("title"))
        company = safe(job.get("company"))
        location = safe(job.get("location"))
        job_url = safe(job.get("job_url"))

        match_score = safe(job.get("match_score"))
        fit = safe(job.get("fit"))
        experience_fit = safe(job.get("experience_fit"))
        role_alignment = safe(job.get("role_alignment"))
        priority = safe(job.get("priority"))

        matched_skills = make_list(job.get("matched_skills"))
        missing_core = make_list(job.get("missing_core_skills"))
        missing_nice = make_list(job.get("missing_nice_to_have_skills"))
        transferable = make_list(job.get("transferable_skills"))
        concerns = make_list(job.get("concerns"))

        summary = safe(job.get("summary"))

        matched_html = "".join(
            f"<span class='skill'>{skill}</span>"
            for skill in matched_skills
        )

        missing_html = "".join(
            f"<span class='missing'>{skill}</span>"
            for skill in missing_core
        )

        transferable_html = "".join(
            f"<span class='transfer'>{skill}</span>"
            for skill in transferable
        )

        concerns_html = "".join(
            f"<li>{concern}</li>"
            for concern in concerns
        )

        cards.append(
            f"""
            <div class="job-card">

                <div class="job-header">
                    <div>
                        <div class="job-number">#{index}</div>

                        <h2>{title}</h2>

                        <div class="company">
                            {company}
                        </div>

                        <div class="location">
                            📍 {location}
                        </div>
                    </div>

                    <div class="score">
                        <strong>{match_score}%</strong>
                        <span>Match</span>
                    </div>
                </div>

                <div class="badges">
                    <span class="badge {priority_class(priority)}">
                        {priority} Priority
                    </span>

                    <span class="badge">
                        AI Fit: {fit}
                    </span>

                    <span class="badge">
                        Experience: {experience_fit}
                    </span>

                    <span class="badge">
                        Role: {role_alignment}
                    </span>
                </div>

                <p class="summary">
                    {summary}
                </p>

                <h3>Matched Skills</h3>

                <div class="skills">
                    {matched_html or "<span>None identified</span>"}
                </div>

                <h3>Missing Core Skills</h3>

                <div class="skills">
                    {missing_html or "<span>None identified</span>"}
                </div>

                {
                    f'''
                    <h3>Transferable Skills</h3>

                    <div class="skills">
                        {transferable_html}
                    </div>
                    '''
                    if transferable_html
                    else ""
                }

                {
                    f'''
                    <h3>Concerns</h3>

                    <ul class="concerns">
                        {concerns_html}
                    </ul>
                    '''
                    if concerns_html
                    else ""
                }

                <a
                    class="apply-button"
                    href="{job_url}"
                    target="_blank"
                >
                    View Job →
                </a>

            </div>
            """
        )

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>Siva Job Agent</title>

<style>

body {{
    margin: 0;
    padding: 0;
    background: #f4f6f8;
    font-family: Arial, Helvetica, sans-serif;
    color: #222;
}}

.container {{
    max-width: 800px;
    margin: 0 auto;
    padding: 30px 20px;
}}

.header {{
    background: #17202a;
    color: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 20px;
}}

.header h1 {{
    margin: 0 0 8px 0;
}}

.header p {{
    margin: 0;
    opacity: 0.8;
}}

.stats {{
    display: flex;
    gap: 10px;
    margin-top: 20px;
    flex-wrap: wrap;
}}

.stat {{
    background: white;
    color: #222;
    padding: 12px 18px;
    border-radius: 8px;
}}

.stat strong {{
    display: block;
    font-size: 20px;
}}

.job-card {{
    background: white;
    padding: 25px;
    margin-bottom: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}

.job-header {{
    display: flex;
    justify-content: space-between;
    gap: 20px;
}}

.job-number {{
    font-size: 13px;
    color: #777;
}}

.job-card h2 {{
    margin: 4px 0;
}}

.company {{
    font-weight: bold;
    margin-top: 6px;
}}

.location {{
    color: #666;
    margin-top: 5px;
}}

.score {{
    text-align: center;
    min-width: 80px;
}}

.score strong {{
    display: block;
    font-size: 28px;
}}

.score span {{
    color: #777;
    font-size: 12px;
}}

.badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 18px 0;
}}

.badge {{
    background: #eef1f4;
    padding: 6px 10px;
    border-radius: 15px;
    font-size: 12px;
}}

.badge.high {{
    background: #dff5e5;
}}

.badge.medium {{
    background: #fff3cd;
}}

.badge.low {{
    background: #f0f0f0;
}}

.summary {{
    line-height: 1.6;
}}

.job-card h3 {{
    font-size: 14px;
    margin-top: 20px;
}}

.skills {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}}

.skill,
.missing,
.transfer {{
    padding: 5px 9px;
    border-radius: 12px;
    font-size: 12px;
}}

.skill {{
    background: #e8f4ff;
}}

.missing {{
    background: #fff0f0;
}}

.transfer {{
    background: #f1eaff;
}}

.concerns {{
    padding-left: 20px;
    line-height: 1.6;
}}

.apply-button {{
    display: inline-block;
    margin-top: 20px;
    padding: 10px 18px;
    background: #17202a;
    color: white;
    text-decoration: none;
    border-radius: 7px;
}}

.footer {{
    text-align: center;
    color: #888;
    font-size: 12px;
    margin-top: 30px;
}}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>🎯 Siva Job Agent</h1>

        <p>
            Daily AI-powered job matching report
        </p>

        <div class="stats">

            <div class="stat">
                <strong>{total_jobs}</strong>
                Jobs Analyzed
            </div>

            <div class="stat">
                <strong>{high_count}</strong>
                High Priority
            </div>

            <div class="stat">
                <strong>{medium_count}</strong>
                Medium Priority
            </div>

            <div class="stat">
                <strong>{low_count}</strong>
                Low Priority
            </div>

        </div>

    </div>

    {''.join(cards)}

    <div class="footer">

        Generated by Siva Job Agent<br>

        {datetime.now().strftime("%d %B %Y, %I:%M %p")}

    </div>

</div>

</body>

</html>
"""

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(html)

    print(f"Digest generated: {OUTPUT_FILE}")

    return OUTPUT_FILE


if __name__ == "__main__":
    generate_digest()
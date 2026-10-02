import pandas as pd
import yaml
import re


PROFILE_FILE = "config/profile.yaml"
JOBS_FILE = "data/jobs.csv"


def load_profile():
    with open(PROFILE_FILE, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def normalize_text(value):
    if pd.isna(value):
        return ""

    return str(value).lower()


def find_experience_requirement(text):
    patterns = [
        r"(\d+)\s*(?:to|-)\s*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\s*\+\s*(?:years?|yrs?)",
        r"minimum\s*(?:of\s*)?(\d+)\s*(?:years?|yrs?)",
        r"at least\s*(\d+)\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if not match:
            continue

        numbers = match.groups()

        if len(numbers) == 2:
            return int(numbers[0]), int(numbers[1])

        minimum = int(numbers[0])
        return minimum, minimum + 3

    return None, None


def location_match(location):

    location = location.lower()

    location_aliases = [
        "hyderabad",
        "greater hyderabad",
        "hyderabad area",
        "ts, in",
        "telangana",
        "remote india",
        "remote",
    ]

    return any(
        item in location
        for item in location_aliases
    )


def calculate_score(job, profile):

    title = normalize_text(job.get("title"))
    description = normalize_text(job.get("description"))
    location = normalize_text(job.get("location"))

    text = f"{title} {description}"

    score = 0

    reasons = []

    warnings = []

    matched_core = []
    matched_additional = []

    # =====================================================
    # 1. ROLE MATCH — 25
    # =====================================================

    target_role = False

    for role in profile["roles"]:

        role_text = role.lower()

        if role_text in title:
            target_role = True
            break

    if target_role:
        score += 25
        reasons.append("Target role")

    # Strong automation/testing titles
    elif any(
        keyword in title
        for keyword in [
            "automation",
            "software test",
            "quality engineer",
            "test engineer",
            "qa engineer",
        ]
    ):
        score += 18
        reasons.append("Relevant QA/automation role")

    # =====================================================
    # 2. LOCATION — 10
    # =====================================================

    if location_match(location):

        score += 10
        reasons.append("Preferred location")

    # =====================================================
    # 3. CORE SKILLS — 30
    # =====================================================

    for skill in profile["high_priority_skills"]:

        if skill.lower() in text:

            matched_core.append(skill)

    # Give extra importance to automation combinations

    core_score = min(
        len(matched_core) * 4,
        30
    )

    # Java + Selenium
    if (
        "java" in text
        and "selenium" in text
    ):
        core_score = min(core_score + 4, 30)

    # Python + pytest
    if (
        "python" in text
        and "pytest" in text
    ):
        core_score = min(core_score + 4, 30)

    # API automation
    if (
        "api" in text
        and (
            "rest assured" in text
            or "api testing" in text
            or "api automation" in text
        )
    ):
        core_score = min(core_score + 4, 30)

    score += core_score

    if matched_core:
        reasons.append(
            "Core skills: "
            + ", ".join(matched_core)
        )

    # =====================================================
    # 4. ADDITIONAL SKILLS — 5
    # =====================================================

    for skill in profile["additional_skills"]:

        if skill.lower() in text:

            matched_additional.append(skill)

    additional_score = min(
        len(matched_additional),
        5
    )

    score += additional_score

    # =====================================================
    # 5. EXPERIENCE — 25
    # =====================================================

    candidate_experience = profile["experience"]["years"]

    required_min, required_max = (
        find_experience_requirement(text)
    )

    if required_min:

        # Perfect / strong range
        if required_min <= candidate_experience <= required_max:

            score += 25

            reasons.append(
                f"Experience fit: "
                f"{required_min}-{required_max} years"
            )

        # Job asks one year more
        elif required_min == candidate_experience + 1:

            score += 18

            warnings.append(
                f"Minor experience gap: "
                f"{required_min}-{required_max} years"
            )

        # Candidate slightly below range
        elif required_min <= candidate_experience + 2:

            score += 10

            warnings.append(
                f"Experience gap: "
                f"{required_min}-{required_max} years"
            )

        # Significant gap
        else:

            score += 3

            warnings.append(
                f"Significant experience gap: "
                f"{required_min}-{required_max} years"
            )

    else:

        score += 12

        warnings.append(
            "Experience requirement unclear"
        )

    # =====================================================
    # 6. NEGATIVE SIGNALS
    # =====================================================

    # Don't search blindly for "intern".
    # Only use meaningful phrases.

    negative_patterns = [
        r"\binternship\b",
        r"\bintern\b",
        r"\btrainee\b",
        r"\bfresher\b",
        r"\bgraduate trainee\b",
    ]

    negative_found = False

    for pattern in negative_patterns:

        if re.search(pattern, title):

            negative_found = True

            warnings.append(
                "Entry-level role"
            )

            score -= 25

            break

    # =====================================================
    # 7. SENIORITY
    # =====================================================

    seniority_penalty = False

    if any(
        keyword in title
        for keyword in [
            "principal engineer",
            "staff engineer",
            "architect",
            "director",
            "head of",
        ]
    ):

        # Only penalize heavily if experience requirement
        # also indicates a senior role.

        if required_min and required_min >= 8:

            score -= 20

            warnings.append(
                "Senior role with high experience requirement"
            )

            seniority_penalty = True

    # =====================================================
    # 8. FINAL SCORE
    # =====================================================

    score = max(
        0,
        min(score, 100)
    )

    return {
        "score": score,
        "reasons": reasons,
        "warnings": warnings,
        "matched_core": matched_core,
        "matched_additional": matched_additional,
        "required_min": required_min,
        "required_max": required_max,
    }


    profile = load_profile()

    jobs = pd.read_csv(JOBS_FILE)

    results = []

    for _, job in jobs.iterrows():

        result = calculate_score(
            job,
            profile
        )

        results.append({

            "title": job.get("title", ""),

            "company": job.get("company", ""),

            "location": job.get("location", ""),

            "date_posted": job.get(
                "date_posted",
                ""
            ),

            "job_url": job.get(
                "job_url",
                ""
            ),

            "match_score": result["score"],

            "matched_skills": ", ".join(
                result["matched_core"]
            ),

            "required_experience":
                (
                    f"{result['required_min']}-"
                    f"{result['required_max']}"
                    if result["required_min"]
                    else "Unknown"
                ),

            "reasons": " | ".join(
                result["reasons"]
            ),

            "warnings": " | ".join(
                result["warnings"]
            ),
        })

    result_df = pd.DataFrame(results)

    return result_df.sort_values(
        by="match_score",
        ascending=False
    )


def match_jobs(jobs=None):

    profile = load_profile()

    # If no DataFrame is supplied, preserve the old behavior.
    # This keeps `python agent/matcher.py` working exactly as before.
    if jobs is None:
        jobs = pd.read_csv(JOBS_FILE)

    results = []

    for _, job in jobs.iterrows():

        result = calculate_score(
            job,
            profile
        )

        results.append({

            "title": job.get("title", ""),

            "company": job.get("company", ""),

            "location": job.get("location", ""),

            "date_posted": job.get(
                "date_posted",
                ""
            ),

            "job_url": job.get(
                "job_url",
                ""
            ),

            "match_score": result["score"],

            "matched_skills": ", ".join(
                result["matched_core"]
            ),

            "required_experience":
                (
                    f"{result['required_min']}-"
                    f"{result['required_max']}"
                    if result["required_min"]
                    else "Unknown"
                ),

            "reasons": " | ".join(
                result["reasons"]
            ),

            "warnings": " | ".join(
                result["warnings"]
            ),
        })

    result_df = pd.DataFrame(results)

    if result_df.empty:
        return result_df

    return result_df.sort_values(
        by="match_score",
        ascending=False
    )

if __name__ == "__main__":

    results = match_jobs()

    print("\nJOB MATCHING RESULTS V3")

    print("=" * 100)

    for _, job in results.iterrows():

        print(
            f"\n{job['match_score']}% | "
            f"{job['title']} | "
            f"{job['company']}"
        )

        print(
            f"Location: {job['location']}"
        )

        print(
            f"Required experience: "
            f"{job['required_experience']}"
        )

        print(
            f"Matched skills: "
            f"{job['matched_skills']}"
        )

        if job["reasons"]:

            print(
                f"Why: {job['reasons']}"
            )

        if job["warnings"]:

            print(
                f"Warnings: {job['warnings']}"
            )

        print(
            f"URL: {job['job_url']}"
        )
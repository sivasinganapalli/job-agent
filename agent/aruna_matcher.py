import re
import yaml
import pandas as pd


PROFILE_FILE = "config/profile_aruna.yaml"

# Jobs below this score will not be included
# in the final email.
MINIMUM_MATCH_SCORE = 45


# ============================================================
# TEXT UTILITIES
# ============================================================

def normalize(text):
    """
    Normalize text so matching is case-insensitive
    and formatting differences don't affect matching.
    """

    if text is None:
        return ""

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Normalize common separators
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text.replace("_", " ")

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def load_profile():
    """
    Load Aruna's profile from YAML.
    """

    with open(
        PROFILE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)


# ============================================================
# EXPERIENCE MATCHING
# ============================================================

def extract_experience(text):
    """
    Extract experience requirements from job description.

    Examples:

        4-7 years
        4 to 7 years
        5+ years
        5 years experience

    Returns:

        [(minimum, maximum), ...]
    """

    text = normalize(text)

    ranges = []

    # --------------------------------------------------------
    # 4-7 years
    # 4 to 7 years
    # --------------------------------------------------------

    range_pattern = (
        r"(\d+)\s*"
        r"(?:-|–|to)"
        r"\s*(\d+)\s*"
        r"(?:years?|yrs?)"
    )

    matches = re.findall(
        range_pattern,
        text
    )

    for match in matches:

        minimum = int(match[0])
        maximum = int(match[1])

        ranges.append(
            (
                minimum,
                maximum
            )
        )

    # --------------------------------------------------------
    # 5+ years
    # --------------------------------------------------------

    plus_pattern = (
        r"(\d+)\s*\+\s*"
        r"(?:years?|yrs?)"
    )

    matches = re.findall(
        plus_pattern,
        text
    )

    for match in matches:

        minimum = int(match)

        ranges.append(
            (
                minimum,
                15
            )
        )

    # --------------------------------------------------------
    # 5 years experience
    # --------------------------------------------------------

    exact_pattern = (
        r"(\d+)\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+of)?\s+"
        r"experience"
    )

    matches = re.findall(
        exact_pattern,
        text
    )

    for match in matches:

        years = int(match)

        ranges.append(
            (
                years,
                years
            )
        )

    return ranges


def experience_match(
    text,
    minimum,
    maximum
):
    """
    Compare job experience requirement
    against candidate experience range.

    Returns:

        1  = compatible
        0  = experience not mentioned
       -1  = outside candidate range
    """

    ranges = extract_experience(text)

    if not ranges:
        return 0

    for job_min, job_max in ranges:

        # Any overlap between the job requirement
        # and candidate range is considered compatible.
        if (
            job_max >= minimum
            and
            job_min <= maximum
        ):
            return 1

    return -1


# ============================================================
# LOCATION MATCHING
# ============================================================

def location_match(
    text,
    locations
):
    """
    Check whether a preferred location
    appears in the job information.
    """

    text = normalize(text)

    for location in locations:

        location_normalized = normalize(
            location
        )

        if location_normalized in text:
            return True

        # Bengaluru / Bangalore
        if (
            location_normalized == "bengaluru"
            and
            "bangalore" in text
        ):
            return True

        # Remote India
        if (
            location_normalized == "remote india"
            and
            "remote" in text
        ):
            return True

    return False


# ============================================================
# KEYWORD MATCHING
# ============================================================

def find_matches(
    text,
    keywords
):
    """
    Return all keywords found in text.
    """

    text = normalize(text)

    matches = []

    for keyword in keywords:

        keyword_normalized = normalize(
            keyword
        )

        if (
            keyword_normalized
            and
            keyword_normalized in text
        ):
            matches.append(keyword)

    return matches


# ============================================================
# EXCLUSION
# ============================================================

def is_excluded(
    text,
    exclude_keywords
):
    """
    Check whether job should be excluded.
    """

    text = normalize(text)

    for keyword in exclude_keywords:

        keyword_normalized = normalize(
            keyword
        )

        if (
            keyword_normalized
            and
            keyword_normalized in text
        ):
            return True

    return False


# ============================================================
# MATCH SCORE
# ============================================================

def calculate_match(
    job,
    profile
):
    """
    Calculate Aruna's job match percentage.

    Scoring:

    ------------------------------------------------------------
    Category                         Maximum
    ------------------------------------------------------------
    Job title / role                  35
    High-priority Linux skills        20
    Patching / Satellite              10
    Automation                         10
    Storage / filesystem                5
    Cloud / virtualization              5
    Location                           10
    Experience                          5
    ------------------------------------------------------------
    TOTAL                             100
    ------------------------------------------------------------
    """

    title = normalize(
        job.get("title", "")
    )

    company = normalize(
        job.get("company", "")
    )

    location = normalize(
        job.get("location", "")
    )

    description = normalize(
        job.get("description", "")
    )

    # Full text used for skill matching
    combined_text = " ".join(
        [
            title,
            company,
            location,
            description
        ]
    )

    # --------------------------------------------------------
    # EXCLUSION CHECK
    # --------------------------------------------------------

    if is_excluded(
        combined_text,
        profile.get(
            "exclude_keywords",
            []
        )
    ):

        return {
            "match_score": 0,
            "matched_roles": [],
            "matched_high_priority": [],
            "matched_additional": [],
            "experience_status": "Excluded",
            "location_match": False,
            "excluded": True
        }

    # --------------------------------------------------------
    # ROLE MATCH
    # --------------------------------------------------------

    role_matches = find_matches(
        title,
        profile.get(
            "roles",
            []
        )
    )

    # --------------------------------------------------------
    # HIGH PRIORITY SKILLS
    # --------------------------------------------------------

    high_priority_matches = find_matches(
        combined_text,
        profile.get(
            "high_priority_skills",
            []
        )
    )

    # --------------------------------------------------------
    # ADDITIONAL SKILLS
    # --------------------------------------------------------

    additional_matches = find_matches(
        combined_text,
        profile.get(
            "additional_skills",
            []
        )
    )

    # ========================================================
    # SCORE
    # ========================================================

    score = 0

    # --------------------------------------------------------
    # 1. ROLE / TITLE
    # Maximum = 35
    # --------------------------------------------------------

    role_score = 0

    if role_matches:

        # Exact / strong title match
        role_score = 35

    else:

        # If title contains Linux-related terminology,
        # give partial role credit.
        linux_title_keywords = [
            "linux",
            "rhel",
            "red hat",
            "unix",
            "system administrator",
            "systems administrator",
            "server administrator",
            "infrastructure engineer",
            "infrastructure support",
            "operations engineer"
        ]

        if any(
            keyword in title
            for keyword in linux_title_keywords
        ):
            role_score = 20

    score += role_score

    # --------------------------------------------------------
    # 2. HIGH PRIORITY SKILLS
    # Maximum = 20
    # --------------------------------------------------------

    high_priority_score = min(
        len(high_priority_matches) * 3,
        20
    )

    score += high_priority_score

    # --------------------------------------------------------
    # 3. PATCHING / SATELLITE
    # Maximum = 10
    # --------------------------------------------------------

    patching_keywords = [
        "patching",
        "server patching",
        "os patching",
        "linux patching",
        "kernel upgrade",
        "kernel patching",
        "red hat satellite",
        "satellite server",
        "rhsm",
        "red hat subscription manager",
        "subscription manager",
        "repository management"
    ]

    patching_matches = find_matches(
        combined_text,
        patching_keywords
    )

    patching_score = min(
        len(patching_matches) * 3,
        10
    )

    score += patching_score

    # --------------------------------------------------------
    # 4. AUTOMATION
    # Maximum = 10
    # --------------------------------------------------------

    automation_keywords = [
        "ansible",
        "bash",
        "shell scripting",
        "shell",
        "automation",
        "linux automation"
    ]

    automation_matches = find_matches(
        combined_text,
        automation_keywords
    )

    automation_score = min(
        len(automation_matches) * 3,
        10
    )

    score += automation_score

    # --------------------------------------------------------
    # 5. STORAGE / FILESYSTEM
    # Maximum = 5
    # --------------------------------------------------------

    storage_keywords = [
        "lvm",
        "logical volume manager",
        "filesystem",
        "file system",
        "nfs",
        "cifs",
        "storage",
        "disk management",
        "inode"
    ]

    storage_matches = find_matches(
        combined_text,
        storage_keywords
    )

    storage_score = min(
        len(storage_matches) * 2,
        5
    )

    score += storage_score

    # --------------------------------------------------------
    # 6. CLOUD / VIRTUALIZATION
    # Maximum = 5
    # --------------------------------------------------------

    cloud_keywords = [
        "aws",
        "oci",
        "oracle cloud",
        "gcp",
        "google cloud",
        "vmware",
        "vsphere"
    ]

    cloud_matches = find_matches(
        combined_text,
        cloud_keywords
    )

    cloud_score = min(
        len(cloud_matches) * 2,
        5
    )

    score += cloud_score

    # --------------------------------------------------------
    # 7. LOCATION
    # Maximum = 10
    # --------------------------------------------------------

    location_found = location_match(
        combined_text,
        profile.get(
            "locations",
            []
        )
    )

    if location_found:
        score += 10

    # --------------------------------------------------------
    # 8. EXPERIENCE
    # Maximum = 5
    # --------------------------------------------------------

    experience = profile.get(
        "experience",
        {}
    )

    minimum_years = experience.get(
        "minimum_years",
        4
    )

    maximum_years = experience.get(
        "maximum_years",
        7
    )

    experience_status = experience_match(
        combined_text,
        minimum_years,
        maximum_years
    )

    if experience_status == 1:

        score += 5

    elif experience_status == -1:

        # Penalize jobs clearly outside
        # the candidate's experience range.
        score -= 5

    # --------------------------------------------------------
    # Keep score between 0 and 100
    # --------------------------------------------------------

    score = max(
        0,
        min(
            score,
            100
        )
    )

    return {
        "match_score": score,

        "matched_roles": role_matches,

        "matched_high_priority":
            high_priority_matches,

        "matched_additional":
            additional_matches,

        "matched_patching":
            patching_matches,

        "matched_automation":
            automation_matches,

        "matched_storage":
            storage_matches,

        "matched_cloud":
            cloud_matches,

        "experience_status":
            experience_status,

        "location_match":
            location_found,

        "excluded": False
    }


# ============================================================
# MATCH ALL JOBS
# ============================================================

def match_jobs(jobs):
    """
    Calculate match percentage for every job.

    Jobs below MINIMUM_MATCH_SCORE
    are removed from the email list.

    Results are sorted from highest
    match percentage to lowest.
    """

    if jobs.empty:

        return jobs

    profile = load_profile()

    results = []

    for _, job in jobs.iterrows():

        result = calculate_match(
            job,
            profile
        )

        row = job.copy()

        row["match_score"] = result[
            "match_score"
        ]

        row["matched_roles"] = (
            ", ".join(
                result.get(
                    "matched_roles",
                    []
                )
            )
        )

        row["matched_high_priority"] = (
            ", ".join(
                result.get(
                    "matched_high_priority",
                    []
                )
            )
        )

        row["matched_additional"] = (
            ", ".join(
                result.get(
                    "matched_additional",
                    []
                )
            )
        )

        row["matched_patching"] = (
            ", ".join(
                result.get(
                    "matched_patching",
                    []
                )
            )
        )

        row["matched_automation"] = (
            ", ".join(
                result.get(
                    "matched_automation",
                    []
                )
            )
        )

        row["matched_storage"] = (
            ", ".join(
                result.get(
                    "matched_storage",
                    []
                )
            )
        )

        row["matched_cloud"] = (
            ", ".join(
                result.get(
                    "matched_cloud",
                    []
                )
            )
        )

        row["experience_status"] = (
            result[
                "experience_status"
            ]
        )

        row["location_match"] = (
            result[
                "location_match"
            ]
        )

        row["excluded"] = (
            result[
                "excluded"
            ]
        )

        results.append(row)

    matched = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Remove explicitly excluded jobs
    # --------------------------------------------------------

    matched = matched[
        matched["excluded"] == False
    ].copy()

    # --------------------------------------------------------
    # Remove jobs below minimum score
    # --------------------------------------------------------

    matched = matched[
        matched["match_score"]
        >= MINIMUM_MATCH_SCORE
    ].copy()

    # --------------------------------------------------------
    # Sort highest match first
    # --------------------------------------------------------

    matched = matched.sort_values(
        by="match_score",
        ascending=False
    )

    return matched.reset_index(
        drop=True
    )


# ============================================================
# TEST / DEBUG
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("ARUNA MATCHER TEST")
    print("=" * 60)

    profile = load_profile()

    print("\nProfile loaded successfully.")
    print(
        f"Candidate: "
        f"{profile.get('candidate', {}).get('name', 'Aruna')}"
    )

    print(
        f"Experience: "
        f"{profile.get('experience', {}).get('minimum_years')} "
        f"- "
        f"{profile.get('experience', {}).get('maximum_years')} years"
    )

    print(
        f"Minimum match score: "
        f"{MINIMUM_MATCH_SCORE}%"
    )

    print("\nMatcher is ready.")
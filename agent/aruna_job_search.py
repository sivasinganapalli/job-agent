import pandas as pd
from jobspy import scrape_jobs


SITES = [
    "linkedin",
    "naukri",
    "indeed",
    "glassdoor",
]

LOCATIONS = [
    "Hyderabad, Telangana, India",
    "Bengaluru, Karnataka, India",
    "Chennai, Tamil Nadu, India",
    "Pune, Maharashtra, India",
]

SEARCH_TERMS = [
    "Linux Administrator",
    "Linux System Administrator",
]

RESULTS_PER_SEARCH = 20
HOURS_OLD = 72


def search_one(site, search_term, location):
    print(
        f"\nSearching: {site} | {search_term} | {location}"
    )

    try:
        jobs = scrape_jobs(
            site_name=[site],
            search_term=search_term,
            location=location,
            results_wanted=RESULTS_PER_SEARCH,
            hours_old=HOURS_OLD,
            country_indeed="India",
            linkedin_fetch_description=False,
            description_format="markdown",
            verbose=1,
        )

        if jobs is None or jobs.empty:
            print(f"No jobs returned from {site}")
            return pd.DataFrame()

        jobs["search_site"] = site
        jobs["search_term"] = search_term
        jobs["search_location"] = location

        print(f"Found {len(jobs)} jobs from {site}")

        return jobs

    except Exception as exc:
        print(f"ERROR: {site} failed: {exc}")
        return pd.DataFrame()


def create_job_key(row):
    """
    Create a stable key for duplicate detection.
    Prefer job URL, otherwise use company/title/location.
    """

    url = str(row.get("job_url", "")).strip().lower()

    if url and url != "nan":
        return url

    company = str(row.get("company", "")).strip().lower()
    title = str(row.get("title", "")).strip().lower()
    location = str(row.get("location", "")).strip().lower()

    return f"{company}|{title}|{location}"


def clean_jobs(jobs):
    if jobs.empty:
        return jobs

    jobs = jobs.copy()

    jobs["job_key"] = jobs.apply(create_job_key, axis=1)

    # Remove duplicate jobs found from multiple sites/searches
    jobs = jobs.drop_duplicates(
        subset=["job_key"],
        keep="first",
    )

    # Remove obvious unwanted jobs
    exclude_patterns = [
        "intern",
        "internship",
        "trainee",
        "fresher",
    ]

    def is_excluded(row):
        text = " ".join(
            [
                str(row.get("title", "")),
                str(row.get("description", "")),
            ]
        ).lower()

        return any(pattern in text for pattern in exclude_patterns)

    jobs = jobs[~jobs.apply(is_excluded, axis=1)]

    return jobs.reset_index(drop=True)


def search_jobs():
    all_jobs = []

    total_searches = (
        len(SITES)
        * len(SEARCH_TERMS)
        * len(LOCATIONS)
    )

    current_search = 0

    for site in SITES:
        for search_term in SEARCH_TERMS:
            for location in LOCATIONS:

                current_search += 1

                print(
                    f"\n[{current_search}/{total_searches}] "
                    f"{site} | {search_term} | {location}"
                )

                jobs = search_one(
                    site,
                    search_term,
                    location,
                )

                if not jobs.empty:
                    all_jobs.append(jobs)

    if not all_jobs:
        print("\nNo jobs found from any source.")
        return pd.DataFrame()

    combined = pd.concat(
        all_jobs,
        ignore_index=True,
    )

    print(
        f"\nTotal jobs collected before cleanup: "
        f"{len(combined)}"
    )

    combined = clean_jobs(combined)

    print(
        f"Total unique jobs after cleanup: "
        f"{len(combined)}"
    )

    return combined
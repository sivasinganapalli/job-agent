from jobspy import scrape_jobs


def search_jobs():
    jobs = scrape_jobs(
        site_name=[
            "linkedin",
            "indeed",
            "google",
        ],
        search_term="SDET QA Automation Selenium",
        location="Hyderabad, Telangana, India",
        results_wanted=30,
        hours_old=72,
        country_indeed="India",

        # Get fuller LinkedIn job information
        linkedin_fetch_description=True,

        # Keep descriptions readable
        description_format="markdown",

        verbose=1,
    )

    return jobs


if __name__ == "__main__":
    jobs = search_jobs()

    print(f"\nFound {len(jobs)} jobs\n")
    print("=" * 100)

    for _, job in jobs.iterrows():

        print(f"Title    : {job.get('title', 'N/A')}")
        print(f"Company  : {job.get('company', 'N/A')}")
        print(f"Location : {job.get('location', 'N/A')}")
        print(f"Date     : {job.get('date_posted', 'N/A')}")
        print(f"Skills   : {job.get('skills', 'N/A')}")

        description = job.get("description", "")

        if description:
            print("Description:")
            print(str(description)[:500])
        else:
            print("Description: Not available")

        print(f"URL      : {job.get('job_url', 'N/A')}")
        print("-" * 100)
import json
import os

import yaml
from dotenv import load_dotenv
from openai import OpenAI


if not os.getenv("GITHUB_ACTIONS"):
    load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY was not found. Check GitHub Actions secret OPENAI_API_KEY or your local .env file."
    )

client = OpenAI(api_key=api_key)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def load_profile():
    """Load candidate profile from config/profile_aruna.yaml."""

    with open(
        "config/profile_aruna.yaml",
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


def analyze_job(job):
    """
    Analyze one job against the candidate profile and return a
    structured Python dictionary for final validation.
    """

    profile = load_profile()

    candidate = profile.get("candidate", {})
    experience = profile.get("experience", {})
    roles = profile.get("roles", [])
    locations = profile.get("locations", [])
    high_priority_skills = profile.get("high_priority_skills", [])
    additional_skills = profile.get("additional_skills", [])

    job_title = str(job.get("title", ""))
    company = str(job.get("company", ""))
    location = str(job.get("location", ""))
    description = str(job.get("description", ""))

    candidate_profile = {
        "name": candidate.get("name", ""),
        "experience_years": experience.get("years"),
        "minimum_target_experience_years": experience.get(
            "minimum_years"
        ),
        "maximum_target_experience_years": experience.get(
            "maximum_years"
        ),
        "target_roles": roles,
        "target_locations": locations,
        "high_priority_skills": high_priority_skills,
        "additional_skills": additional_skills,
    }

    prompt = f"""
You are an expert job-matching analyst for a Linux infrastructure candidate.

Your task is to compare ONE job against the candidate profile and decide whether it is worth sending in an email.

Use ONLY the information provided below.
Do not invent skills or experience.
Do not assume a role is a fit just because it is similar.
Compare the experience requirement to the candidate target range.
Focus on whether the job is worth applying to.
Return ONLY valid JSON, no markdown, no code fences.

---------------------------------------------------------
CANDIDATE PROFILE
---------------------------------------------------------
{json.dumps(candidate_profile, indent=2)}

---------------------------------------------------------
JOB
---------------------------------------------------------
Title:
{job_title}

Company:
{company}

Location:
{location}

Job Description:
{description}

---------------------------------------------------------
OUTPUT
---------------------------------------------------------
Return exactly this JSON structure:

{{
  "fit": "Strong|Good|Moderate|Weak",
  "experience_fit": "Good|Slight gap|Significant gap|Unknown",
  "role_alignment": "Strong|Good|Moderate|Weak",
  "matched_skills": [],
  "missing_core_skills": [],
  "missing_nice_to_have_skills": [],
  "transferable_skills": [],
  "key_requirements": [],
  "concerns": [],
  "summary": "",
  "priority": "High|Medium|Low"
}}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    raw_output = response.output_text.strip()

    try:
        result = json.loads(raw_output)
    except json.JSONDecodeError:
        print("\nAI returned invalid JSON:")
        print(raw_output)

        result = {
            "fit": "Unknown",
            "experience_fit": "Unknown",
            "role_alignment": "Unknown",
            "matched_skills": [],
            "missing_core_skills": [],
            "missing_nice_to_have_skills": [],
            "transferable_skills": [],
            "key_requirements": [],
            "concerns": ["AI response could not be parsed."],
            "summary": "AI analysis failed because the response was not valid JSON.",
            "priority": "Low",
        }

    return result

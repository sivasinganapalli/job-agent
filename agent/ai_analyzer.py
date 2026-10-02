import json
import os

import yaml
from dotenv import load_dotenv
from openai import OpenAI


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY was not found. Check your .env file."
    )

client = OpenAI(api_key=api_key)

MODEL = "gpt-6-luna"


# ---------------------------------------------------------
# Load candidate profile
# ---------------------------------------------------------

def load_profile():
    """Load candidate profile from config/profile.yaml."""

    with open("config/profile.yaml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# ---------------------------------------------------------
# Analyze one job
# ---------------------------------------------------------

def analyze_job(job):
    """
    Analyze one job against the candidate profile.

    Returns a structured Python dictionary.
    """

    profile = load_profile()

    candidate = profile.get("candidate", {})
    experience = profile.get("experience", {})
    roles = profile.get("roles", [])
    locations = profile.get("locations", [])
    high_priority_skills = profile.get("high_priority_skills", [])
    additional_skills = profile.get("additional_skills", [])
    exclude_keywords = profile.get("exclude_keywords", [])

    job_title = str(job.get("title", ""))
    company = str(job.get("company", ""))
    location = str(job.get("location", ""))
    description = str(job.get("description", ""))

    # -----------------------------------------------------
    # Candidate profile for AI
    # -----------------------------------------------------

    candidate_profile = {
        "name": candidate.get("name", ""),
        "experience_years": experience.get("years"),
        "maximum_target_experience_years": experience.get(
            "maximum_years"
        ),
        "target_roles": roles,
        "target_locations": locations,
        "high_priority_skills": high_priority_skills,
        "additional_skills": additional_skills,
        "exclude_keywords": exclude_keywords,
    }

    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    prompt = f"""
You are an expert job-matching analyst for an SDET / QA Automation candidate.

Your task is to compare ONE job description against the candidate profile.

IMPORTANT RULES:

1. Use ONLY the candidate information provided below.
2. Do not invent candidate skills or experience.
3. Do not assume that a tool is known just because it is similar
   to another tool.
4. Distinguish between:
   - Core/critical requirements
   - Nice-to-have requirements
5. A missing nice-to-have skill should NOT heavily reduce the overall fit.
6. A missing core requirement should have a stronger impact.
7. Transferable skills may be considered, but clearly identify them.
8. Compare the job's stated experience requirement with the candidate's
   configured experience.
9. If the job does not state an experience requirement, use "Unknown".
10. Consider the candidate's target roles and locations.
11. Excluded keywords should be treated as negative signals.
12. Focus on whether this job is worth the candidate's application time.
13. Do NOT predict whether the candidate will get an interview or offer.
14. Return ONLY valid JSON.
15. Do not return Markdown.
16. Do not use ```json fences.

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

---------------------------------------------------------
PRIORITY GUIDANCE
---------------------------------------------------------

High:
- Strong alignment with the target role
- Experience is within the candidate's target range
- Core automation skills are well matched
- No major blocker is present

Medium:
- Reasonable match
- Some meaningful skill gaps exist
- Candidate can still reasonably consider applying

Low:
- Major experience mismatch
- Role is primarily outside the candidate's target area
- Significant core skill gaps
- Excluded role characteristics are present
"""


    # -----------------------------------------------------
    # OpenAI request
    # -----------------------------------------------------

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    raw_output = response.output_text.strip()

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

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
            "concerns": [
                "AI response could not be parsed."
            ],
            "summary": "AI analysis failed because the response was not valid JSON.",
            "priority": "Low",
        }

    return result

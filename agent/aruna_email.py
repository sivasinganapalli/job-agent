import os
import html
import smtplib

import pandas as pd

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()


EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "smtp.gmail.com",
)

EMAIL_PORT = int(
    os.getenv("EMAIL_PORT", "465")
)

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

EMAIL_RECIPIENTS = [
    email.strip()
    for email in EMAIL_TO.split(",")
    if email.strip()
] if EMAIL_TO else []

DIGEST_FILE = "data/aruna_daily_digest.html"


def safe(value):
    """Convert NaN/None values to safe strings."""

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return html.escape(str(value))


def format_match_score(value):
    """Return a human-friendly match percentage string, or empty string."""

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    s = str(value).strip()

    if not s:
        return ""

    # If value already contains a percent sign, return as-is
    if s.endswith('%'):
        return html.escape(s)

    try:
        num = float(s)

        # Render integers without decimal
        if num.is_integer():
            display = f"{int(num)}%"
        else:
            display = f"{round(num, 1)}%"

        return html.escape(display)

    except Exception:
        # Fallback: append percent sign
        return html.escape(f"{s}%")


def generate_digest(jobs):
    """
    Generate the HTML email containing all new Aruna jobs.
    """

    os.makedirs("data", exist_ok=True)

    if jobs.empty:

        html_content = """
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">

            <h2>Aruna Linux Job Agent</h2>

            <p>
                No new Linux Administrator jobs were found today.
            </p>

        </body>
        </html>
        """

    else:

        job_cards = []

        for _, job in jobs.iterrows():

            title = safe(
                job.get("title", "")
            )

            company = safe(
                job.get("company", "")
            )

            location = safe(
                job.get("location", "")
            )

            source = safe(
                job.get(
                    "search_site",
                    job.get("site", ""),
                )
            )

            date_posted = safe(
                job.get(
                    "date_posted",
                    "",
                )
            )

            match_score = format_match_score(
                job.get(
                    "match_score",
                    "",
                )
            )

            url = safe(
                job.get(
                    "job_url",
                    "",
                )
            )

            card = f"""
            <div style="
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 18px;
                margin-bottom: 16px;
                background: #ffffff;
            ">

                <h3 style="
                    margin-top: 0;
                    margin-bottom: 10px;
                ">
                    {title}
                </h3>

                <p>
                    <strong>Company:</strong>
                    {company}
                </p>

                <p>
                    <strong>Location:</strong>
                    {location}
                </p>

                <p>
                    <strong>Source:</strong>
                    {source}
                </p>

                <p>
                    <strong>Date Posted:</strong>
                    {date_posted}
                </p>

                <p>
                    <strong>Match:</strong>
                    {match_score or 'N/A'}
                </p>

                <p>
                    <a
                        href="{url}"
                        target="_blank"
                        style="
                            display: inline-block;
                            padding: 10px 16px;
                            background: #1a73e8;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                        "
                    >
                        View Job
                    </a>
                </p>

                <p style="
                    font-size: 11px;
                    color: #777777;
                    word-break: break-all;
                ">
                    {url}
                </p>

            </div>
            """

            job_cards.append(card)

        html_content = f"""
        <!DOCTYPE html>
        <html>

        <body style="
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
        ">

            <div style="
                max-width: 850px;
                margin: auto;
                background: white;
                padding: 25px;
                border-radius: 10px;
            ">

                <h1>
                    Aruna Linux Job Agent
                </h1>

                <p>
                    <strong>
                        {len(jobs)} new jobs found today
                    </strong>
                </p>

                <hr>

                {''.join(job_cards)}

            </div>

        </body>
        </html>
        """

    with open(
        DIGEST_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(html_content)

    print(
        f"Digest generated: {DIGEST_FILE}"
    )

    return DIGEST_FILE


def send_email(
    html_file,
    job_count,
):
    """
    Send the generated HTML digest by email.
    """

    if not EMAIL_FROM:
        raise ValueError(
            "EMAIL_FROM is missing in .env"
        )

    if not EMAIL_RECIPIENTS:
        raise ValueError(
            "EMAIL_TO is missing or invalid in .env"
        )

    if not EMAIL_PASSWORD:
        raise ValueError(
            "EMAIL_PASSWORD is missing in .env"
        )

    if not os.path.exists(html_file):
        raise FileNotFoundError(
            f"Email HTML file not found: {html_file}"
        )

    with open(
        html_file,
        "r",
        encoding="utf-8",
    ) as file:

        html_content = file.read()

    message = MIMEMultipart(
        "alternative"
    )

    message["From"] = EMAIL_FROM
    message["To"] = ", ".join(EMAIL_RECIPIENTS)

    message["Subject"] = (
        f"Aruna Linux Jobs — "
        f"{job_count} New Jobs"
    )

    plain_text = (
        f"Aruna Job Agent found "
        f"{job_count} new jobs today."
    )

    message.attach(
        MIMEText(
            plain_text,
            "plain",
            "utf-8",
        )
    )

    message.attach(
        MIMEText(
            html_content,
            "html",
            "utf-8",
        )
    )

    print(
        f"Sending email to: "
        f"{', '.join(EMAIL_RECIPIENTS)}..."
    )

    with smtplib.SMTP_SSL(
        EMAIL_HOST,
        EMAIL_PORT,
    ) as server:

        server.login(
            EMAIL_FROM,
            EMAIL_PASSWORD,
        )

        server.sendmail(
            EMAIL_FROM,
            EMAIL_RECIPIENTS,
            message.as_string(),
        )

    print(
        "Aruna email sent successfully."
    )
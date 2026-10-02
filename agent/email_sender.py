import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()


EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(html_file, subject="Siva Job Agent — Daily Job Digest"):
    if not EMAIL_FROM:
        raise ValueError("EMAIL_FROM is missing in .env")

    if not EMAIL_TO:
        raise ValueError("EMAIL_TO is missing in .env")

    if not EMAIL_PASSWORD:
        raise ValueError("EMAIL_PASSWORD is missing in .env")

    if not os.path.exists(html_file):
        raise FileNotFoundError(
            f"Email HTML file not found: {html_file}"
        )

    with open(html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    message = MIMEMultipart("alternative")

    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message["Subject"] = subject

    message.attach(
        MIMEText(
            "Your daily Siva Job Agent report is available in HTML format.",
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

    print(f"Sending email to {EMAIL_TO}...")

    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(
            EMAIL_FROM,
            EMAIL_TO,
            message.as_string(),
        )

    print("Email sent successfully.")


if __name__ == "__main__":
    send_email("data/daily_digest.html")
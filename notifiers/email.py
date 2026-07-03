import logging
import os
import smtplib
from collections import defaultdict
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from models import Job

logger = logging.getLogger(__name__)


def render_html(jobs: list[Job]) -> str:
    by_category: dict[int, list[Job]] = defaultdict(list)
    for job in jobs:
        by_category[job.category].append(job)

    sections: list[str] = []
    for cat in sorted(by_category):
        label = f"Category {cat}" if cat > 0 else "GitHub Repo"
        rows = "".join(
            f"<tr>"
            f"<td style='padding:6px 12px;'>{j.company}</td>"
            f"<td style='padding:6px 12px;'>{j.title}</td>"
            f"<td style='padding:6px 12px;'>{j.location}</td>"
            f"<td style='padding:6px 12px;'><a href='{j.url}'>Apply</a></td>"
            f"</tr>"
            for j in by_category[cat]
        )
        sections.append(
            f"<h3 style='color:#333;border-bottom:1px solid #ddd;padding-bottom:4px;'>{label}</h3>"
            f"<table style='border-collapse:collapse;width:100%;font-family:sans-serif;font-size:14px;'>"
            f"<thead><tr>"
            f"<th style='text-align:left;padding:6px 12px;background:#f5f5f5;'>Company</th>"
            f"<th style='text-align:left;padding:6px 12px;background:#f5f5f5;'>Role</th>"
            f"<th style='text-align:left;padding:6px 12px;background:#f5f5f5;'>Location</th>"
            f"<th style='text-align:left;padding:6px 12px;background:#f5f5f5;'>Link</th>"
            f"</tr></thead>"
            f"<tbody>{rows}</tbody>"
            f"</table>"
        )

    body = "".join(sections)
    today = date.today().strftime("%B %d, %Y")
    return (
        f"<html><body style='font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;'>"
        f"<h2 style='color:#1a1a1a;'>Internship Alerts — {today}</h2>"
        f"{body}"
        f"<p style='color:#999;font-size:12px;margin-top:24px;'>Monitored by internship-runner</p>"
        f"</body></html>"
    )


def send_digest(jobs: list[Job], email_to: str) -> None:
    if not jobs:
        return

    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    today_str = date.today().strftime("%b %d, %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Internship Alert] {len(jobs)} new role(s) — {today_str}"
    msg["To"] = email_to
    msg["From"] = gmail_address
    msg.attach(MIMEText(render_html(jobs), "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_password)
        smtp.send_message(msg)

    logger.info("digest sent to %s with %d jobs", email_to, len(jobs))

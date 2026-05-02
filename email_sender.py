# ============================================================
#           WebEarl Technologies — Email Sender
# ============================================================

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from auth import get_credentials
from config import (
    COMPANY_NAME, COMPANY_EMAIL, COMPANY_ADDRESS,
    COMPANY_WEBSITE, INTERVIEW_EMAIL_SUBJECT,
    INTERVIEW_EMAIL_BODY
)

# --- Template Path ---
TEMPLATE_PATH = os.path.join("templates", "interview_invite.html")


def create_email_message(to_email, subject, body_html, body_plain):
    """
    Creates a MIME email message with both HTML and plain text versions.
    """
    message = MIMEMultipart("alternative")
    message["To"] = to_email
    message["From"] = f"{COMPANY_NAME} <{COMPANY_EMAIL}>"
    message["Subject"] = subject

    # Plain text version
    part1 = MIMEText(body_plain, "plain")
    # HTML version
    part2 = MIMEText(body_html, "html")

    # HTML version is added last — email clients prefer it
    message.attach(part1)
    message.attach(part2)

    return message


def build_plain_email(candidate_name, job_role, interview_date, interview_time):
    """
    Builds plain text version of interview invitation email.
    """
    return INTERVIEW_EMAIL_BODY.format(
        candidate_name=candidate_name,
        role=job_role,
        interview_date=interview_date,
        interview_time=interview_time,
        company_email=COMPANY_EMAIL,
        company_address=COMPANY_ADDRESS,
        company_website=COMPANY_WEBSITE,
    )


def build_html_email(candidate_name, job_role, interview_date, interview_time):
    """
    Loads HTML template from templates/interview_invite.html
    and fills in candidate details dynamically.
    """
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        # Replace all placeholders with actual values
        html = html.replace("{{CANDIDATE_NAME}}", candidate_name)
        html = html.replace("{{JOB_ROLE}}", job_role)
        html = html.replace("{{INTERVIEW_DATE}}", interview_date)
        html = html.replace("{{INTERVIEW_TIME}}", interview_time)
        html = html.replace("{{COMPANY_NAME}}", COMPANY_NAME)
        html = html.replace("{{COMPANY_EMAIL}}", COMPANY_EMAIL)
        html = html.replace("{{COMPANY_ADDRESS}}", COMPANY_ADDRESS)
        html = html.replace("{{COMPANY_WEBSITE}}", COMPANY_WEBSITE)

        print(f"   📄 Email template loaded: {TEMPLATE_PATH}")
        return html

    except FileNotFoundError:
        print(f"   ⚠️  Template not found at: {TEMPLATE_PATH}")
        print(f"   ⚠️  Please create templates/interview_invite.html")
        print(f"   ⚠️  Falling back to plain text email")
        return f"<p>Dear {candidate_name}, your interview for <b>{job_role}</b> is scheduled on {interview_date} at {interview_time}.</p>"

    except Exception as e:
        print(f"   ⚠️  Could not load email template: {e}")
        return ""


def send_interview_invitation(candidate_info, interview_info):
    """
    Main function — sends interview invitation email to candidate.
    """
    print(f"\n📧 Sending interview invitation to: {candidate_info.get('email')}")

    # Get Gmail service
    _, gmail_service, _ = get_credentials()

    if not gmail_service:
        print("❌ Could not connect to Gmail")
        return False

    candidate_name = candidate_info.get("name", "Candidate")
    candidate_email = candidate_info.get("email", "")
    job_role = candidate_info.get("job_role", "Position")
    interview_date = interview_info.get("date", "")
    interview_time = interview_info.get("time", "")

    if not candidate_email:
        print("❌ No candidate email found — cannot send invitation")
        return False

    # Build email subject
    subject = INTERVIEW_EMAIL_SUBJECT.format(role=job_role)

    # Build email body (both plain and HTML)
    plain_body = build_plain_email(
        candidate_name, job_role,
        interview_date, interview_time
    )
    html_body = build_html_email(
        candidate_name, job_role,
        interview_date, interview_time
    )

    # Create email message
    message = create_email_message(
        candidate_email, subject,
        html_body, plain_body
    )

    try:
        # Encode message for Gmail API
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        # Send via Gmail API
        sent_message = gmail_service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()

        message_id = sent_message.get("id", "")

        print(f"   ✅ Interview invitation sent successfully!")
        print(f"   📧 To       : {candidate_email}")
        print(f"   📋 Subject  : {subject}")
        print(f"   🆔 Gmail ID : {message_id}")
        return True

    except Exception as e:
        print(f"   ❌ Could not send email: {e}")
        return False
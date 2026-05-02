# ============================================================
#           WebEarl Technologies — Email Reader
# ============================================================

import os
import base64
import json
from datetime import datetime
from auth import get_credentials
from config import RESUMES_FOLDER

# --- Supported resume file types ---
SUPPORTED_EXTENSIONS = [".pdf", ".doc", ".docx"]


def get_unread_job_emails():
    """
    Fetches unread emails from Gmail that have resume attachments.
    Returns a list of email data dictionaries.
    """
    print("\n" + "="*50)
    print("  📧 Checking Gmail for new applications...")
    print("="*50)

    # Get Gmail service
    _, gmail_service, _ = get_credentials()

    if not gmail_service:
        print("❌ Could not connect to Gmail.")
        return []

    try:
        # Search for unread emails with attachments
        query = "is:unread has:attachment"
        results = gmail_service.users().messages().list(
            userId="me",
            q=query,
            maxResults=50
        ).execute()

        messages = results.get("messages", [])

        if not messages:
            print("📭 No new unread emails with attachments found.")
            return []

        print(f"📬 Found {len(messages)} unread email(s) with attachments\n")

        email_data_list = []

        for msg in messages:
            email_data = process_single_email(gmail_service, msg["id"])
            if email_data:
                email_data_list.append(email_data)

        print(f"\n✅ Successfully processed {len(email_data_list)} job application email(s)")
        return email_data_list

    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        return []


def process_single_email(gmail_service, message_id):
    """
    Processes a single email — extracts body, sender info, and downloads resume.
    """
    try:
        # Get full email details
        message = gmail_service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        # --- Extract Headers ---
        headers = message["payload"]["headers"]
        header_dict = {h["name"].lower(): h["value"] for h in headers}

        sender_name, sender_email = extract_sender(header_dict.get("from", ""))
        subject = header_dict.get("subject", "No Subject")
        date_received = header_dict.get("date", str(datetime.now()))

        print(f"  📩 Processing: {subject}")
        print(f"     From: {sender_name} <{sender_email}>")

        # --- Extract Email Body ---
        body_text = extract_email_body(message["payload"])

        # --- Check if this looks like a job application ---
        if not is_job_application(subject, body_text):
            print(f"     ⏭️  Skipping — does not look like a job application")
            return None

        # --- Download Resume Attachment ---
        resume_path = download_resume(gmail_service, message_id, message["payload"], sender_email)

        if not resume_path:
            print(f"     ⚠️  No valid resume attachment found (PDF/DOC/DOCX)")
            # Still process if body has enough info
            resume_path = "No attachment"

        # --- Mark email as read ---
        mark_as_read(gmail_service, message_id)

        email_data = {
            "message_id": message_id,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "date_received": date_received,
            "body": body_text,
            "resume_path": resume_path,
        }

        print(f"     ✅ Email processed successfully")
        print(f"     📎 Resume saved: {os.path.basename(resume_path) if resume_path != 'No attachment' else 'None'}")

        return email_data

    except Exception as e:
        print(f"     ❌ Error processing email {message_id}: {e}")
        return None


def extract_sender(from_header):
    """
    Extracts sender name and email from the From header.
    Example: 'John Doe <john@email.com>' → ('John Doe', 'john@email.com')
    """
    try:
        if "<" in from_header and ">" in from_header:
            name = from_header.split("<")[0].strip().strip('"')
            email = from_header.split("<")[1].replace(">", "").strip()
        else:
            name = ""
            email = from_header.strip()
        return name, email
    except:
        return "", from_header


def extract_email_body(payload):
    """
    Extracts plain text body from email payload.
    Handles both simple and multipart emails.
    """
    body = ""

    try:
        # Simple email (not multipart)
        if "parts" not in payload:
            if payload.get("mimeType") == "text/plain":
                data = payload.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            return body.strip()

        # Multipart email — search through all parts
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")

            # Plain text part
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break

            # Nested multipart
            elif mime_type.startswith("multipart/"):
                nested_body = extract_email_body(part)
                if nested_body:
                    body = nested_body
                    break

    except Exception as e:
        print(f"     ⚠️  Could not extract email body: {e}")

    return body.strip()


def is_job_application(subject, body):
    """
    Checks if the email is a job or internship application.
    """
    keywords = [
        "apply", "application", "resume", "cv", "intern", "internship",
        "job", "position", "hiring", "opportunity", "candidate",
        "developer", "designer", "marketing", "role", "opening",
        "fresher", "experience", "skills", "portfolio"
    ]

    text = (subject + " " + body).lower()

    matched = sum(1 for keyword in keywords if keyword in text)

    # If 2 or more keywords match, it's likely a job application
    return matched >= 2


def download_resume(gmail_service, message_id, payload, sender_email):
    """
    Downloads resume attachment from email and saves to resumes/ folder.
    Returns the file path if successful, None otherwise.
    """
    try:
        # Make sure resumes folder exists
        os.makedirs(RESUMES_FOLDER, exist_ok=True)

        attachments = find_attachments(payload)

        for attachment in attachments:
            filename = attachment.get("filename", "")
            attachment_id = attachment.get("attachmentId", "")

            # Check if it's a supported resume format
            file_ext = os.path.splitext(filename.lower())[1]
            if file_ext not in SUPPORTED_EXTENSIONS:
                continue

            # Download the attachment
            attachment_data = gmail_service.users().messages().attachments().get(
                userId="me",
                messageId=message_id,
                id=attachment_id
            ).execute()

            file_data = base64.urlsafe_b64decode(attachment_data["data"])

            # Create a clean filename
            clean_email = sender_email.replace("@", "_at_").replace(".", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_filename = f"{clean_email}_{timestamp}{file_ext}"
            save_path = os.path.join(RESUMES_FOLDER, save_filename)

            # Save the file
            with open(save_path, "wb") as f:
                f.write(file_data)

            return save_path

    except Exception as e:
        print(f"     ⚠️  Could not download attachment: {e}")

    return None


def find_attachments(payload):
    """
    Recursively finds all attachments in email payload.
    """
    attachments = []

    try:
        if "parts" in payload:
            for part in payload["parts"]:
                filename = part.get("filename", "")
                body = part.get("body", {})
                attachment_id = body.get("attachmentId", "")

                # If it has a filename and attachmentId it's an attachment
                if filename and attachment_id:
                    attachments.append({
                        "filename": filename,
                        "attachmentId": attachment_id
                    })

                # Recurse into nested parts
                if "parts" in part:
                    attachments.extend(find_attachments(part))

    except Exception as e:
        print(f"     ⚠️  Error finding attachments: {e}")

    return attachments


def mark_as_read(gmail_service, message_id):
    """
    Marks email as read so it won't be processed again next time.
    """
    try:
        gmail_service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except Exception as e:
        print(f"     ⚠️  Could not mark email as read: {e}")


def test_email_reader():
    """
    Test the email reader — run this file directly to test.
    """
    print("\n" + "="*50)
    print("  WebEarl HR — Email Reader Test")
    print("="*50)

    emails = get_unread_job_emails()

    if not emails:
        print("\n📭 No job application emails found.")
        print("   Try sending a test email to your Gmail with a PDF attached")
        print("   with subject like 'Job Application — Python Developer'")
        return

    print(f"\n📋 Summary of emails found:")
    for i, email in enumerate(emails, 1):
        print(f"\n  Email #{i}:")
        print(f"  → From    : {email['sender_name']} <{email['sender_email']}>")
        print(f"  → Subject : {email['subject']}")
        print(f"  → Resume  : {email['resume_path']}")
        print(f"  → Body Preview : {email['body'][:150]}...")


# Run this file directly to test
if __name__ == "__main__":
    test_email_reader()
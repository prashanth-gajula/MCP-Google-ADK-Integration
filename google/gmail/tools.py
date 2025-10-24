from auth.auth import get_gmail_service
import email
import base64
from utils.util import strip_html_tags
from email.mime.text import MIMEText
from base64 import urlsafe_b64encode
from googleapiclient.errors import HttpError



#Tools
def list_labels() -> list[str]:
    service = get_gmail_service()
    resp = service.users().labels().list(userId="me").execute()
    return [label["name"] for label in resp.get("labels", [])]

#read messages
def read_latest_email() -> dict:
    """
    Fetch the most recent email with subject, sender, and full body.
    """
    service = get_gmail_service()

    # 1) Get the most recent message ID
    result = service.users().messages().list(
        userId="me", maxResults=20, q="in:inbox -label:sent"
    ).execute()

    messages = result.get("messages", [])
    if not messages:
        return {"error": "No emails found."}

    msg_id = messages[0]["id"]

    # 2) Get the full message
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()

    # 3) Extract headers
    headers = msg["payload"]["headers"]
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")

    # 4) Extract body (may be in different parts)
    body = ""
    payload = msg.get("payload", {})
    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    else:
        raw_msg = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="raw"
        ).execute()
        raw_email = base64.urlsafe_b64decode(raw_msg["raw"])
    email_message = email.message_from_bytes(raw_email)
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            elif part.get_content_type() == "text/html":
                html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                body =  strip_html_tags(html_body)
    else:
        body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")

    return {
        "subject": subject,
        "from": sender,
        "body": body or "(No body text)"
    }
    
#send email
def send_email(to: str, subject: str, body: str) -> dict:
    """
    Send an email using the Gmail API.
    """
    try:
        service = get_gmail_service()

        # Build MIME message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        # Encode message for Gmail
        raw = urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "status": "success",
            "message_id": sent["id"],
            "to": to,
            "subject": subject
        }

    except HttpError as error:
        return {"status": "error", "error": str(error)}
from auth.auth import get_gmail_service,get_credentials
import email
import base64
from utils.util import strip_html_tags
from email.mime.text import MIMEText
from base64 import urlsafe_b64encode
from googleapiclient.errors import HttpError

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from base64 import urlsafe_b64encode
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv(dotenv_path="agent/.env")

#Tools
def list_labels() -> list[str]:
    service = get_gmail_service()
    resp = service.users().labels().list(userId="me").execute()
    return [label["name"] for label in resp.get("labels", [])]

#read messages
def read_latest_email() -> dict:
    """
    Fetch the most recent email with subject, sender, full body,
    and metadata needed to reply to the thread.
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

    # 2) Get the full message metadata
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()

    # 3) Extract headers
    headers = msg["payload"]["headers"]
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")
    message_id_header = next((h["value"] for h in headers if h["name"] == "Message-ID"), None)

    # 4) Try different body formats
    body = ""
    raw_email = None  

    payload = msg.get("payload", {})

    # A) Inline plain text (simplest case)
    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

    # B) Multipart → fallback to raw
    if not body:
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
                    body = strip_html_tags(html_body)
        else:
            body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")

    return {
        "subject": subject,
        "from": sender,
        "body": body or "(No body text)",
        "thread_id": msg["threadId"],             
        "message_id_header": message_id_header      
    }
    
#send email
def send_email(to: str, subject: str, body: str, attachment_path: str = None) -> dict:
    """
    Send an email via Gmail API, optionally including a file attachment.

    Args:
        to (str): Recipient email address.
        subject (str): Subject of the email.
        body (str): Text body of the email.
        attachment_path (str, optional): Local filesystem path to a file to attach.

    Returns:
        dict: {
            "status": "success",
            "message_id": "<gmail message id>",
            "attached": bool
        }
    """
    try:
        service = get_gmail_service()

        # MIME Multipart container
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject

        # Add body text
        message.attach(MIMEText(body, "plain"))

        # ✅ Optional attachment
        attached = False
        if attachment_path:
            with open(attachment_path, "rb") as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(attachment_path),
                )
                message.attach(attachment)
                attached = True

        # Encode message for Gmail
        raw = urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "status": "success",
            "message_id": sent["id"],
            "attached": attached,
            "to": to,
            "subject": subject
        }

    except HttpError as error:
        return {"status": "error", "error": str(error)}
    
#reply email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def reply_to_email(thread_id: str,in_reply_to: str,to: str,subject: str,body: str,attachment_path: str = None) -> dict:
    """
    Reply to an existing Gmail thread. Supports attachments.

    Args:
        thread_id (str): Gmail thread ID.
        in_reply_to (str): Original Message-ID header from read_latest_email().
        to (str): Recipient email address (original sender).
        subject (str): Subject line (usually "Re: ...").
        body (str): Reply text.
        attachment_path (str, optional): Local file path to attach.

    Returns:
        dict: {
            "status": "success" | "error",
            "message_id": str,
            "thread_id": str,
            "attached": bool
        }
    """
    try:
        service = get_gmail_service()

        # Multipart container
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject

        # Gmail threading headers
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to

        # Body
        message.attach(MIMEText(body, "plain"))

        attached = False
        if attachment_path:
            with open(attachment_path, "rb") as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(attachment_path),
                )
                message.attach(attachment)
                attached = True

        # Encode
        raw = urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw, "threadId": thread_id}
        ).execute()

        return {
            "status": "success",
            "message_id": sent["id"],
            "thread_id": sent["threadId"],
            "attached": attached
        }

    except HttpError as error:
        return {"status": "error", "error": str(error)}
    
#notify email code


def register_gmail_watch():
    """
    Register Gmail watch to receive push notifications when new emails arrive.
    This creates a channel from Gmail → Pub/Sub topic.
    """
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    request_body = {
        "labelIds": ["INBOX"],
        "topicName": os.getenv("PUBSUB_TOPIC_NAME")
    }

    response = service.users().watch(
        userId='me',
        body=request_body
    ).execute()

    print("✅ Gmail watch successfully registered!")
    print(f"Expiration: {response.get('expiration')}")
    print(f"History ID: {response.get('historyId')}")
    return response



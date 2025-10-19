from auth.auth import get_gmail_service


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
        userId="me", maxResults=20, q=""
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
        import base64
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    else:
        # If email is multipart, traverse parts
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain" and "data" in part["body"]:
                import base64
                body += base64.urlsafe_b64decode(
                    part["body"]["data"]
                ).decode("utf-8", errors="ignore")

    return {
        "subject": subject,
        "from": sender,
        "body": body or "(No body text)"
    }
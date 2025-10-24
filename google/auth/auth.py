# google/gmail/server.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow#to handle oauth flow for the desktop apps
from google.auth.transport.requests import Request#to refresh the token if it is expired
from googleapiclient.discovery import build

# Minimal, safe scope to start. We can expand later.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",     
    "https://www.googleapis.com/auth/drive.readonly",     
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send"
]#read only scope was provided

# Paths: keep the token next to credentials.json
BASE_DIR = Path(__file__).parent
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_credentials(scopes: Optional[list[str]] = None) -> Credentials:#handles the authentication part
    """Load/refresh credentials; if not present, run the local OAuth flow."""
    use_scopes = scopes or SCOPES
    creds: Optional[Credentials] = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), use_scopes)#trying to load existing token

    # Refresh if expired, otherwise run auth flow
    if not creds or not creds.valid:#this part of the code checks is the token is expired if it is expired then we will refresh it of perform the login again
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDS_FILE}. "
                    "Download it from Google Cloud → Credentials → OAuth client."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), use_scopes)
            # Opens a browser window on first run; uses loopback (desktop app)
            creds = flow.run_local_server(port=0)#lets python choose any freeport
        # Persist for future runs
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def get_gmail_service():
    """Return an authenticated Gmail API client."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)

def get_drive_service():
    """Return an authenticated Gmail API client."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


if __name__ == "__main__":
    # Quick smoke test: list label names to confirm OAuth works.
    svc = get_gmail_service()
    resp = svc.users().labels().list(userId="me").execute()
    labels = [lbl["name"] for lbl in resp.get("labels", [])]
    print("✅ Gmail auth OK. Labels found:", labels)
    print(f"🔐 Token saved at: {TOKEN_FILE.resolve()}")

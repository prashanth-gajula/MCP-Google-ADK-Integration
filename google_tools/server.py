from fastmcp import FastMCP
from gmail.tools import list_labels, read_latest_email,send_email,reply_to_email
from gdrive.tools import list_drive_files,read_drive_file,download_drive_file

app = FastMCP("gmail-mcp-server")

# Wrap your imported functions with @app.tool()
@app.tool()
def list_labels_tool() -> list[str]:
    """List all Gmail labels"""
    return list_labels()

@app.tool()
def read_latest_email_tool() -> dict:
    """Read the latest email"""
    return read_latest_email()

@app.tool()
def list_drive_files_tool() -> dict:
    """List drive file"""
    return list_drive_files()

@app.tool()
def read_drive_file_tool(file_id: str) -> dict:
    """
    Read file contents from Google Drive by file ID.
    
    Args:
        file_id: The Google Drive file ID (example: '1ZvqzwwJBUSgKsfRn4xdog_9ueA05SNRL')
    
    Returns:
        Dictionary with file name, type, and content
    """
    return read_drive_file(file_id=file_id)

#send email tool
@app.tool()
def send_email_tool(to: str, subject: str, body: str,attachment_path: str = None) -> dict:
    """
    Send an email using the Gmail API, optionally including a file attachment.

    This tool sends a plain-text email to a specified recipient. If a local
    file path is provided via `attachment_path`, the file will be loaded
    from the filesystem and attached to the outgoing message. This allows
    locally cached Drive files (such as resumes) to be attached without
    passing binary or base64 content through the language model context.

    Args:
        to (str):
            Recipient email address. Example: 'user@example.com'
        subject (str):
            Subject line of the email.
        body (str):
            Plain text body content of the email.
        attachment_path (str | None, optional):
            Local filesystem path to a file to attach. Must point to a valid,
            previously downloaded file (e.g., saved in the 'attachments/' folder).
            If None, the email is sent without an attachment.

    Returns:
        dict: {
            "status": "success" | "error",
            "message_id": str,     # Gmail-generated message ID (if successful)
            "attached": bool,      # True if an attachment was included
            "to": str,             # Recipient address
            "subject": str         # Subject line
        }
    """
    return send_email(to=to,subject=subject,body=body,attachment_path=attachment_path)


#download file content from drive
@app.tool()
def download_drive_file_tool(file_id: str, filename: str) -> dict:
    """
    Download a Google Drive file locally for attachment use.

    This tool retrieves a file from Google Drive by its file ID and stores it
    in the local "attachments/" directory. If the file already exists locally,
    it will NOT be downloaded again, allowing reuse across multiple email sends
    without impacting Google Drive quota or passing large binary data through
    the LLM context.
    """
    return download_drive_file(file_id=file_id,filename=filename)

#reply email
@app.tool()
def reply_email_tool(thread_id: str,in_reply_to: str,to: str,subject: str,body: str,attachment_path: str = None) -> dict:
    """
    Reply to an existing Gmail thread. Supports attachments.

    Use this tool when the user asks to respond to a received email.
    The agent must know:
    - thread_id (from read_latest_email_tool)
    - in_reply_to (Message-ID header from read_latest_email_tool)

    Args:
        thread_id (str): Gmail thread ID of the email being replied to.
        in_reply_to (str): Original Message-ID header from the email being replied to.
        to (str): Recipient address (usually the original sender).
        subject (str): Subject line, e.g., "Re: Job Application".
        body (str): Reply body text.
        attachment_path (str, optional): Local file path to attach.

    Returns:
        dict with status, message_id, thread_id, and attached status.
    """
    return reply_to_email(thread_id=thread_id,in_reply_to=in_reply_to,to=to,subject=subject,body=body,attachment_path=attachment_path)


if __name__ == "__main__":
    app.run()
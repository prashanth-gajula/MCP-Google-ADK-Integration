from auth.auth import get_drive_service
from io import BytesIO
from PyPDF2 import PdfReader


def list_drive_files() -> list[dict]:
    """
    List the first 10 files in Google Drive with name and id.
    """
    service = get_drive_service()

    results = service.files().list(
        pageSize=10,
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])

    if not files:
        return [{"message": "No files found."}]

    return {
    "files": [
        {"name": file["name"], "id": file["id"], "type": file["mimeType"]}
        for file in files
    ]
}

#read file contents

def read_drive_file(file_id: str) -> dict:
    """
    Read file contents by Drive file ID and return text content.
    Supports: Google Docs, Google Sheets, PDFs, plain text, JSON.
    """

    service = get_drive_service()

    # Get file metadata
    file = service.files().get(fileId=file_id).execute()
    mime_type = file.get("mimeType")
    name = file.get("name")

    # -------------------------
    # Google Docs → export text
    # -------------------------
    if mime_type == "application/vnd.google-apps.document":
        data = service.files().export(
            fileId=file_id,
            mimeType="text/plain"
        ).execute()
        text = data.decode("utf-8", errors="ignore")
        return {"name": name, "type": mime_type, "content": text}

    # -------------------------
    # Google Sheets → export CSV
    # -------------------------
    if mime_type == "application/vnd.google-apps.spreadsheet":
        data = service.files().export(
            fileId=file_id,
            mimeType="text/csv"
        ).execute()
        text = data.decode("utf-8", errors="ignore")
        return {"name": name, "type": mime_type, "content": text}

    # -------------------------
    # PDF handling
    # -------------------------
    if mime_type == "application/pdf":
        request = service.files().get_media(fileId=file_id)
        file_data = BytesIO(request.execute())
        reader = PdfReader(file_data)

        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        return {"name": name, "type": mime_type, "content": text}

    # -------------------------
    # Plain text, JSON, Markdown
    # -------------------------
    if mime_type.startswith("text/") or mime_type in ["application/json"]:
        request = service.files().get_media(fileId=file_id)
        file_bytes = request.execute()
        text = file_bytes.decode("utf-8", errors="ignore")
        return {"name": name, "type": mime_type, "content": text}

    # -------------------------
    # Unsupported binary formats
    # -------------------------
    return {
        "name": name,
        "type": mime_type,
        "content": "(Binary file cannot be previewed)"
    }
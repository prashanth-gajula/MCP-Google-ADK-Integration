from auth.auth import get_drive_service


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


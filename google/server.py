from fastmcp import FastMCP
from gmail.tools import list_labels, read_latest_email
from gdrive.tools import list_drive_files,read_drive_file

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


if __name__ == "__main__":
    app.run()
from fastmcp import FastMCP
from gmail.tools import list_labels, read_latest_email
from gdrive.tools import list_drive_files

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
    """Read the latest email"""
    return list_drive_files()

if __name__ == "__main__":
    app.run()
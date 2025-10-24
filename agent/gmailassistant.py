import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "basic_agent_no_web"
USER_ID = "user_12345"
SESSION_ID = "session_12345"

async def main():
    toolset = None
    try:
        # create memory session 
        session_service = InMemorySessionService()
        session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        
        # 1. Setup MCP toolset
        toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command="python",
                args=["../google/server.py"]
            )
        )
        await toolset._initialize()
        tool_set = await toolset.load_tools()

        # 2. Create agent
        root_agent = LlmAgent(
    name="gmailassistant",
    description="Assistant that can read Gmail and Google Drive files",
    instruction="""You are a helpful assistant with access to Gmail and Google Drive.

    When a user asks to read a file from Google Drive:
    1. If they provide a file_id directly, use read_drive_file(file_id="...")
    2. If they mention a file name, first use list_drive_files() to find the file ID
    3. Then use read_drive_file(file_id="...") with the found ID

    Always extract and use the exact file_id from the list_drive_files response.
    
    This is the name of the resume Prashanth_Kumar_AI_Engineer_Resume.pdf
    
    When an user asks to send any attachment with the gmail check if the file is available in the temporary folder attachments if it is available
    attach that file with the email and if not download the file to the local attachments directory first and attach the file in that email.
    
    If the user asks to reply to a specific email or the latest email, call reply_email_tool.
    Use the 'thread_id' from the read_latest_email_tool output.
    Always keep the same subject prefixed with "Re:".
    """,
    model="gemini-2.0-flash-exp",
    tools=tool_set
)

        # 3. Create runner instance
        runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break

            content = types.Content(role="user", parts=[types.Part(text=user_input)])

            events = runner.run_async(
                new_message=content,
                user_id=USER_ID,
                session_id=SESSION_ID,
            )

            async for event in events:
                if event.is_final_response():
                    print("Agent:", event.content.parts[0].text)

    finally:
        # ✅ Cleanly close MCP server connection
        if toolset is not None:
            try:
                # Try different close methods
                if hasattr(toolset, 'cleanup'):
                    await toolset.cleanup()
                elif hasattr(toolset, '__aexit__'):
                    await toolset.__aexit__(None, None, None)
                elif hasattr(toolset, 'close'):
                    await toolset.close()
                print("✅ MCP connection closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing MCP connection (can be ignored): {e}")


if __name__ == "__main__":
    asyncio.run(main())
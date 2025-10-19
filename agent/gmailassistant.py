import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "basic_agent_no_web"
USER_ID = "user_12345"
SESSION_ID = "session_12345"

async def main(query):
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
            description="This is my first agent",
            instruction="You are a helpful assistant.",
            model="gemini-2.0-flash",
            tools=tool_set
        )

        # 3. Create runner instance
        runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

        # 4. Format the query 
        content = types.Content(role="user", parts=[types.Part(text=query)])

        print("Running agent with query:", query)
        
        # 5. Run the agent 
        events = runner.run_async(
            new_message=content,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )

        # 6. Print the response
        async for event in events:
            print(event)
            if event.is_final_response():
                final_response = event.content.parts[0].text
                print("Agent Response:", final_response)

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
    asyncio.run(main("can you check and tell me if i have received any emails about job listings in last one hour"))
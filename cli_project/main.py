import asyncio
import sys
import os
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from mcp_client import MCPClient
from core.ollama_service import OllamaService
from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()


def get_command():
    """
    Decide how to run MCP server (uv or python)
    """
    if os.getenv("USE_UV", "0") == "1":
        return "uv", ["run", "mcp_server.py"]
    return "python", ["mcp_server.py"]


async def main():
    # -------------------------------
    # Initialize Ollama
    # -------------------------------
    model = os.getenv("OLLAMA_MODEL", "gemma:latest")
    ollama_service = OllamaService(model=model)

    # -------------------------------
    # MCP Clients Setup
    # -------------------------------
    server_scripts = sys.argv[1:]
    clients = {}

    command, args = get_command()

    async with AsyncExitStack() as stack:
        # Primary MCP server (documents)
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        # Additional MCP servers (optional)
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"

            client = await stack.enter_async_context(
                MCPClient(
                    command="uv",
                    args=["run", server_script]
                )
            )

            clients[client_id] = client

        # -------------------------------
        # Chat + CLI
        # -------------------------------
        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=ollama_service,  # keep name to avoid refactor
        )

        cli = CliApp(chat)

        print("\n✅ MCP + Ollama Agent Ready")
        print(f"🤖 Model: {model}")
        print("Type your query or Ctrl+C to exit\n")

        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy()
        )

    asyncio.run(main())
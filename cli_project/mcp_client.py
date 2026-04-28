import sys
import asyncio
from typing import Optional, Any, Dict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from core.logger import Logger


class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[Dict[str, str]] = None,
    ):
        self._command = command
        self._args = args
        self._env = env

        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    # =========================================================
    # 🔌 CONNECTION
    # =========================================================

    async def connect(self):
        Logger._log("mcpConnectionStart", {
            "command": self._command,
            "args": self._args
        })

        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )

        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        read_stream, write_stream = stdio_transport

        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await self._session.initialize()

        Logger._log("mcpConnectionReady")

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError("MCP session not initialized")
        return self._session

    # =========================================================
    # 🛠 TOOLS
    # =========================================================

    async def list_tools(self) -> list[types.Tool]:
        Logger._log("mcpListToolsRequest")

        result = await self.session().list_tools()

        Logger._log("mcpListToolsResult", {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]
        })

        return result.tools

    async def call_tool(
        self,
        tool_name: str,
        tool_input: dict
    ) -> types.CallToolResult | None:

        Logger._log("mcpCallToolRequest", {
            "tool_name": tool_name,
            "tool_input": tool_input
        })

        result = await self.session().call_tool(tool_name, tool_input)

        Logger._log("mcpCallToolResult", {
            "is_error": result.isError if result else None,
            "content": str(result.content) if result else None
        })

        return result

    # =========================================================
    # 🧠 PROMPTS
    # =========================================================

    async def list_prompts(self) -> list[types.Prompt]:
        Logger._log("mcpListPromptsRequest")

        result = await self.session().list_prompts()

        Logger._log("mcpListPromptsResult", {
            "prompts": [p.name for p in result.prompts]
        })

        return result.prompts

    async def get_prompt(
        self,
        prompt_name: str,
        args: dict[str, str]
    ):
        Logger._log("mcpGetPromptRequest", {
            "name": prompt_name,
            "args": args
        })

        result = await self.session().get_prompt(
            name=prompt_name,
            arguments=args,
        )

        Logger._log("mcpGetPromptResult", {
            "messages": str(result.messages)
        })

        return result.messages

    # =========================================================
    # 📦 RESOURCES
    # =========================================================

    async def read_resource(self, uri: str) -> Any:
        Logger._log("mcpReadResourceRequest", {
            "uri": uri
        })

        result = await self.session().read_resource(uri)

        Logger._log("mcpReadResourceRaw", {
            "contents": str(result.contents)
        })

        extracted = []
        for item in result.contents:
            if hasattr(item, "text"):
                extracted.append(item.text)

        Logger._log("mcpReadResourceParsed", {
            "parsed": extracted
        })

        if len(extracted) == 1:
            return extracted[0]

        return extracted

    # =========================================================
    # 🧹 CLEANUP
    # =========================================================

    async def cleanup(self):
        Logger._log("mcpCleanupStart")

        await self._exit_stack.aclose()
        self._session = None

        Logger._log("mcpCleanupDone")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# =========================================================
# 🧪 TEST
# =========================================================

async def main():
    async with MCPClient(
        command="uv",
        args=["run", "mcp_server.py"],
    ) as client:

        tools = await client.list_tools()
        print("\nTools:", [t.name for t in tools])

        docs = await client.read_resource("docs://documents")
        print("\nDocs:", docs)

        content = await client.read_resource("docs://documents/report.pdf")
        print("\nContent:", content)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy()
        )

    asyncio.run(main())
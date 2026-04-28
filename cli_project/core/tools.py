import json
from typing import Optional, Literal, List

from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient
from anthropic.types import Message, ToolResultBlockParam

from core.logger import Logger


class ToolManager:

    # =========================================================
    # 🛠 GET ALL TOOLS
    # =========================================================

    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[Tool]:
        tools = []

        for client_name, client in clients.items():
            Logger._log("toolsListRequest", {"client": client_name})

            result = await client.list_tools()

            Logger._log("toolsListResult", {
                "client": client_name,
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema,
                    }
                    for t in result
                ]
            })

            tools += [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in result
            ]

        return tools

    # =========================================================
    # 🔍 FIND CLIENT FOR TOOL
    # =========================================================

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:

        for client in clients:
            tools = await client.list_tools()

            for t in tools:
                if t.name == tool_name:
                    return client

        return None

    # =========================================================
    # 🧱 TOOL RESULT BLOCK
    # =========================================================

    @classmethod
    def _build_tool_result_part(
        cls,
        tool_use_id: str,
        text: str,
        status: Literal["success"] | Literal["error"],
    ) -> ToolResultBlockParam:

        return {
            "tool_use_id": tool_use_id,
            "type": "tool_result",
            "content": text,
            "is_error": status == "error",
        }

    # =========================================================
    # 🚀 EXECUTE TOOL
    # =========================================================

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], message: Message
    ) -> List[ToolResultBlockParam]:

        tool_requests = [
            block for block in message.content if block.type == "tool_use"
        ]

        results: list[ToolResultBlockParam] = []

        for tool_request in tool_requests:

            tool_use_id = tool_request.id
            tool_name = tool_request.name
            tool_input = tool_request.input

            Logger._log("toolExecutionStart", {
                "tool_name": tool_name,
                "tool_input": tool_input
            })

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            if not client:
                error_msg = "Tool not found"

                Logger._log("toolExecutionError", error_msg)

                results.append(
                    cls._build_tool_result_part(
                        tool_use_id,
                        json.dumps({"error": error_msg}),
                        "error",
                    )
                )
                continue

            try:
                raw_result: CallToolResult | None = await client.call_tool(
                    tool_name,
                    tool_input,
                )

                Logger._log("callToolRawResult", {
                    "tool_name": tool_name,
                    "raw": str(raw_result)
                })

                # Extract text content
                items = raw_result.content if raw_result else []

                extracted_texts = [
                    item.text
                    for item in items
                    if isinstance(item, TextContent)
                ]

                Logger._log("callToolParsedResult", {
                    "tool_name": tool_name,
                    "parsed": extracted_texts
                })

                content_json = json.dumps(extracted_texts)

                results.append(
                    cls._build_tool_result_part(
                        tool_use_id,
                        content_json,
                        "error" if raw_result and raw_result.isError else "success",
                    )
                )

            except Exception as e:
                error_msg = f"Exception: {str(e)}"

                Logger._log("toolExecutionException", error_msg)

                results.append(
                    cls._build_tool_result_part(
                        tool_use_id,
                        json.dumps({"error": error_msg}),
                        "error",
                    )
                )

        return results
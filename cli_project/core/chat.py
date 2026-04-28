import json
from typing import Dict, List, Any

from mcp_client import MCPClient
from core.tools import ToolManager
from core.logger import Logger


class Chat:
    def __init__(self, claude_service, clients: Dict[str, MCPClient]):
        self.claude_service = claude_service
        self.clients = clients
        self.messages: List[Dict[str, str]] = []

    async def _process_query(self, query: str):
        self.messages.append({
            "role": "user",
            "content": query
        })

    # =========================================================
    # 🧠 SYSTEM PROMPT (STRICT)
    # =========================================================

    def _build_system_prompt(self, tools: List[Dict[str, Any]]) -> str:
        return f"""
You are an AI assistant with access to external tools.

TOOLS (STRICT SCHEMA):
{json.dumps(tools, indent=2)}

STRICT RULES:
1. If using a tool, respond ONLY with raw JSON.
2. DO NOT wrap JSON in markdown.
3. Use EXACT parameter names from input_schema.
4. DO NOT invent parameters.
5. Output MUST be valid JSON.

VALID FORMAT:
{{
  "tool_name": "read_document",
  "tool_input": {{
    "doc_id": "example.txt"
  }}
}}

If you fail to follow schema, you will be asked to correct yourself.
"""

    # =========================================================
    # 🧪 JSON PARSER (STRICT)
    # =========================================================

    def _parse_json(self, text: str):
        text = text.strip()

        # Remove markdown if present
        if text.startswith("```"):
            lines = text.split("\n")
            if len(lines) >= 3:
                text = "\n".join(lines[1:-1])

        return json.loads(text)

    # =========================================================
    # ✅ VALIDATION (STRICT)
    # =========================================================

    def _validate_tool_call(self, tool_call: dict, tools: List[Dict]):
        if "tool_name" not in tool_call or "tool_input" not in tool_call:
            raise ValueError("Missing tool_name or tool_input")

        tool_name = tool_call["tool_name"]
        tool_input = tool_call["tool_input"]

        tool = next((t for t in tools if t["name"] == tool_name), None)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        schema = tool.get("input_schema", {})
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check required fields
        for field in required:
            if field not in tool_input:
                raise ValueError(f"Missing required field: {field}")

        # Check unknown fields
        for field in tool_input:
            if field not in properties:
                raise ValueError(f"Unknown field: {field}")

        return True

    # =========================================================
    # 🛠 EXECUTE TOOL
    # =========================================================

    async def _execute_tool(self, tool_call: dict):
        tool_name = tool_call["tool_name"]
        tool_input = tool_call["tool_input"]

        Logger.call_tool_request(tool_name, tool_input)

        class MockToolUse:
            def __init__(self):
                self.type = "tool_use"
                self.id = "manual_call"
                self.name = tool_name
                self.input = tool_input

        class MockMessage:
            def __init__(self):
                self.content = [MockToolUse()]

        result = await ToolManager.execute_tool_requests(
            self.clients,
            MockMessage()
        )

        Logger.call_tool_result(result)

        return result

    # =========================================================
    # 🔁 MAIN LOOP
    # =========================================================

    async def run(self, query: str) -> str:
        await self._process_query(query)

        # ---------------------------
        # Fetch tools (with logging)
        # ---------------------------
        Logger.tools_list_request()
        tools = await ToolManager.get_all_tools(self.clients)
        Logger.tools_list_result(tools)

        system_prompt = self._build_system_prompt(tools)

        max_retries = 5

        for attempt in range(max_retries):

            Logger.retry_attempt(attempt + 1)

            # ---------------------------
            # MODEL CALL
            # ---------------------------
            Logger.model_request(self.messages, system_prompt)

            response_text = self.claude_service.chat(
                messages=self.messages,
                system=system_prompt,
            )

            Logger.model_response(response_text)

            # ---------------------------
            # Try parsing JSON
            # ---------------------------
            parsed = None

            try:
                parsed = self._parse_json(response_text)
            except Exception:
                # NOT JSON → treat as final answer
                self.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
                return response_text

            # ---------------------------
            # Check if tool call
            # ---------------------------
            if isinstance(parsed, dict) and "tool_name" in parsed:

                try:
                    self._validate_tool_call(parsed, tools)
                except Exception as e:
                    Logger.validation_error(str(e))

                    self.messages.append({
                        "role": "user",
                        "content": f"""
Your tool call is invalid.

Error:
{str(e)}

Expected schema:
{json.dumps(tools, indent=2)}

Fix your response. Return ONLY valid JSON.
"""
                    })
                    continue

                # ---------------------------
                # Execute tool
                # ---------------------------
                tool_result = await self._execute_tool(parsed)

                self.messages.append({
                    "role": "assistant",
                    "content": response_text
                })

                self.messages.append({
                    "role": "user",
                    "content": f"Tool result: {json.dumps(tool_result)}"
                })

                continue

            # ---------------------------
            # Normal response
            # ---------------------------
            self.messages.append({
                "role": "assistant",
                "content": response_text
            })

            return response_text

        return "Error: Max retries exceeded."
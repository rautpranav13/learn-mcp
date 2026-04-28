import json
from datetime import datetime


class Logger:
    """
    Structured console logger for MCP + Agent events
    """

    @staticmethod
    def _log(event: str, data=None):
        timestamp = datetime.utcnow().isoformat()

        print("\n" + "=" * 60)
        print(f"[{timestamp}] {event}")

        if data is not None:
            try:
                if isinstance(data, str):
                    print(data)
                else:
                    print(json.dumps(data, indent=2))
            except Exception:
                print(data)

        print("=" * 60)

    # =========================
    # MCP / Tool Events
    # =========================

    @staticmethod
    def tools_list_request():
        Logger._log("toolsListRequest")

    @staticmethod
    def tools_list_result(tools):
        Logger._log("toolsListResult", tools)

    @staticmethod
    def call_tool_request(tool_name, tool_input):
        Logger._log("callToolRequest", {
            "tool_name": tool_name,
            "tool_input": tool_input
        })

    @staticmethod
    def call_tool_result(result):
        Logger._log("callToolResult", result)

    # =========================
    # Model Events
    # =========================

    @staticmethod
    def model_request(messages, system):
        Logger._log("modelRequest", {
            "system": system,
            "messages": messages
        })

    @staticmethod
    def model_response(response):
        Logger._log("modelResponse", response)

    # =========================
    # Validation / Retry
    # =========================

    @staticmethod
    def validation_error(error):
        Logger._log("validationError", error)

    @staticmethod
    def retry_attempt(attempt):
        Logger._log("retryAttempt", {"attempt": attempt})
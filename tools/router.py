"""
tools/router.py
────────────────────────────────────────────
Central Tool Router

Every AI tool call comes here.

Example:

tool = "open_app"

args = {
    "app": "Google Chrome"
}

↓

Router

↓

MacOSControl.open_application("Google Chrome")
"""

import logging

logger = logging.getLogger(__name__)


class ToolRouter:

    def __init__(self, macos):

        self.macos = macos

    def execute(self, tool_name: str, arguments: dict):

        logger.info(f"Tool Call → {tool_name} {arguments}")

        if tool_name == "open_app":

            app = arguments.get("app", "")

            if not app:
                return "No application name provided."

            return self.macos.open_application(app)

        elif tool_name == "open_website":

            url = arguments.get("url", "")

            if not url:
                return "No URL provided."

            return self.macos.open_website(url)

        elif tool_name == "search_google":

            query = arguments.get("query", "")

            if not query:
                return "No search query provided."

            return self.macos.search_google(query)

        return f"Unknown tool: {tool_name}"
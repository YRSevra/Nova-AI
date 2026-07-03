"""
modules/macos_control.py — macOS Automation
─────────────────────────────────────────────
Controls macOS using AppleScript and shell commands.

This module handles commands like:
- "Open Chrome"
- "Open VS Code"
- "Search YouTube for lo-fi music"
- "Open Downloads folder"
- "Show me the time"
- "Set volume to 50"

HOW IT WORKS:
1. The orchestrator passes the user's text command here
2. We match it against known patterns (regex + keywords)
3. We run the appropriate AppleScript or shell command
4. We return a description of what we did (for Nova to speak)

APPLESCRIPT BASICS:
  osascript -e 'tell application "Safari" to activate'
  osascript -e 'open location "https://google.com"'
"""

import subprocess
import re
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class MacOSControl:
    """Execute macOS automation commands via AppleScript and shell."""

    def __init__(self, config: dict, memory=None):
        self.memory = memory

        # ── App name aliases ──────────────────────────────────────────────
        # Maps what users say → actual app names on macOS
        self.app_aliases = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "safari": "Safari",
            "firefox": "Firefox",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "visual studio code": "Visual Studio Code",
            "terminal": "Terminal",
            "finder": "Finder",
            "whatsapp": "WhatsApp",
            "spotify": "Spotify",
            "notes": "Notes",
            "calendar": "Calendar",
            "messages": "Messages",
            "mail": "Mail",
            "photos": "Photos",
            "music": "Music",
            "xcode": "Xcode",
            "pycharm": "PyCharm",
            "slack": "Slack",
            "discord": "Discord",
            "zoom": "Zoom",
            "notion": "Notion",
        }
        self.website_aliases = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "gmail": "https://mail.google.com",
            "chatgpt": "https://chat.openai.com",
            "github": "https://github.com",
            "linkedin": "https://linkedin.com",
            "stackoverflow": "https://stackoverflow.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "reddit": "https://reddit.com",
            "netflix": "https://netflix.com",
            "amazon": "https://amazon.in",
        }

    def handle(self, command: str) -> str:
        """
        Try to handle a command as a macOS automation action.
        
        Returns:
            A string describing the action taken, OR
            None if this command isn't a macOS action.
        """
        command_lower = command.lower().strip()

        # ── Try each handler in order ─────────────────────────────────────
        handlers = [
            self._handle_open_app,
            self._handle_open_website,
            self._handle_search,
            self._handle_volume,
            self._handle_system_info,
            self._handle_file_operations,
        ]

        for handler in handlers:
            result = handler(command_lower)
            if result:
                return result

        return None  # Not a macOS command — let the AI brain handle it

    # ────────────────────────────────────────────────────────────────────────
    # App Control
    # ────────────────────────────────────────────────────────────────────────

    def _handle_open_app(self, command: str) -> str:
        """Open an application by name."""
        # Match patterns: "open chrome", "launch terminal", "start VS Code"
        pattern = r'(?:open|launch|start|run)\s+(.+?)(?:\s+please)?$'
        match = re.search(pattern, command)
        if not match:
            return None

        app_keyword = match.group(1).strip()

        # Look up the real app name
        app_name = self.app_aliases.get(app_keyword)
        if not app_name:
            # Try to find a partial match
            for alias, real_name in self.app_aliases.items():
                if alias in app_keyword or app_keyword in alias:
                    app_name = real_name
                    break

        if not app_name:
            return None  # Unknown app — let AI handle this

        success = self._open_app(app_name)
        if success:
            if self.memory:
                self.memory.record_app_open(app_name)
            return f"Opening {app_name}."
        else:
            return f"I tried to open {app_name} but couldn't find it. Is it installed?"

    def _open_app(self, app_name: str) -> bool:
        """Open a macOS application using AppleScript."""
        script = f'tell application "{app_name}" to activate'
        result = self._run_applescript(script)
        return result is not None

    # ────────────────────────────────────────────────────────────────────────
    # Website / Browser
    # ────────────────────────────────────────────────────────────────────────

    def _handle_open_website(self, command: str) -> str:
        for site, url in self.website_aliases.items():

            if f"open {site}" in command:

                self._open_url(url)

                return f"Opening {site.title()}."
        
        """Open a website in the default browser."""
        # "open youtube.com", "go to github.com", "open https://..."
        pattern = r'(?:open|go to|visit|navigate to)\s+((?:https?://)?[\w.-]+\.\w{2,}(?:/\S*)?)'
        match = re.search(pattern, command)
        if not match:
            return None

        url = match.group(1)
        if not url.startswith("http"):
            url = "https://" + url

        self._open_url(url)
        return f"Opening {url} in your browser."

    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        # Using 'open' command — works with the default browser
        subprocess.run(["open", url], capture_output=True)

    # ────────────────────────────────────────────────────────────────────────
    # Search
    # ────────────────────────────────────────────────────────────────────────

    def _handle_search(self, command: str) -> str:
        """Handle search commands."""

        # YouTube search: "search youtube for lo-fi music"
        yt_match = re.search(r'(?:search|find|look up)\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)', command)
        if yt_match or "youtube" in command:
            query = yt_match.group(1) if yt_match else re.sub(r'.*youtube\s*', '', command).strip()
            if query:
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                self._open_url(url)
                return f"Searching YouTube for '{query}'."

        # Google search: "google python tutorials", "search for best coffee shops"
        google_match = re.search(
            r'(?:google|search(?: for| google| online)?|look up)\s+(.+)', command
        )
        if google_match:
            query = google_match.group(1)
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            self._open_url(url)
            return f"Searching Google for '{query}'."

        return None

    # ────────────────────────────────────────────────────────────────────────
    # Volume Control
    # ────────────────────────────────────────────────────────────────────────

    def _handle_volume(self, command: str) -> str:
        """Control system volume."""
        # "set volume to 50", "volume 80", "mute", "unmute"
        if "mute" in command:
            self._run_applescript("set volume output muted true")
            return "Muted."

        if "unmute" in command:
            self._run_applescript("set volume output muted false")
            return "Unmuted."

        vol_match = re.search(r'(?:set\s+)?volume(?:\s+to)?\s+(\d+)', command)
        if vol_match:
            level = int(vol_match.group(1))
            # macOS volume is 0-100 but AppleScript uses 0-7
            applescript_vol = min(7, round(level / 100 * 7))
            self._run_applescript(f"set volume output volume {level}")
            return f"Volume set to {level}%."

        return None

    # ────────────────────────────────────────────────────────────────────────
    # System Info
    # ────────────────────────────────────────────────────────────────────────

    def _handle_system_info(self, command: str) -> str:
        """Answer system info questions."""
        if any(word in command for word in ["what time", "current time", "time is it"]):
            now = datetime.now()
            return f"It's {now.strftime('%I:%M %p')}."

        if any(word in command for word in ["what date", "today's date", "what day"]):
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}."

        if "battery" in command:
            result = subprocess.run(
                ["pmset", "-g", "batt"], capture_output=True, text=True
            )
            if result.returncode == 0:
                # Parse: "Now drawing from 'AC Power'; InternalBattery-0 ...	 82%;"
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    return f"Your battery is at {match.group(1)}%."

        if "wifi" in command or "network" in command:
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                capture_output=True, text=True
            )
            match = re.search(r'SSID:\s+(.+)', result.stdout)
            if match:
                return f"You're connected to Wi-Fi network: {match.group(1).strip()}"

        return None

    # ────────────────────────────────────────────────────────────────────────
    # File Operations
    # ────────────────────────────────────────────────────────────────────────

    def _handle_file_operations(self, command: str) -> str:
        """Handle basic file/folder commands."""
        # "open downloads folder", "show desktop"
        folder_map = {
            "downloads": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
            "desktop": os.path.expanduser("~/Desktop"),
            "home": os.path.expanduser("~"),
            "pictures": os.path.expanduser("~/Pictures"),
            "music": os.path.expanduser("~/Music"),
        }

        for keyword, path in folder_map.items():
            if keyword in command and any(v in command for v in ["open", "show", "go to"]):
                subprocess.run(["open", path], capture_output=True)
                return f"Opening your {keyword.title()} folder."

        return None

    # ────────────────────────────────────────────────────────────────────────
    # Utility
    # ────────────────────────────────────────────────────────────────────────

    def _run_applescript(self, script: str) -> str:
        """
        Run an AppleScript command.
        
        Example:
            _run_applescript('tell application "Finder" to open home')
        
        Returns stdout on success, None on failure.
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"AppleScript error: {result.stderr.strip()}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("AppleScript timed out")
            return None
        except Exception as e:
            logger.error(f"AppleScript exception: {e}")
            return None

    def run_shell(self, command: str) -> str:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Shell command error: {e}")
            return ""

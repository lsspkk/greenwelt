# Debug logging system
import sys
from typing import List
from collections import deque


class DebugLog:
    """Cross-platform debug logging system"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.messages: deque = deque(maxlen=100)
        self.is_wasm = sys.platform == "emscripten"
        self.overlay_visible = False
        self.scroll_offset = 0

    def log(self, msg: str, level: str = "INFO"):
        """Log a message"""
        entry = f"[{level}] {msg}"
        self.messages.append(entry)

        # On native Python, also print to terminal
        if not self.is_wasm:
            print(entry, flush=True)

    def info(self, msg: str):
        self.log(msg, "INFO")

    def warn(self, msg: str):
        self.log(msg, "WARN")

    def error(self, msg: str):
        self.log(msg, "ERROR")

    def debug(self, msg: str):
        self.log(msg, "DEBUG")

    def get_messages(self, count: int = 20) -> List[str]:
        """Get the last N messages"""
        msgs = list(self.messages)
        start = max(0, len(msgs) - count - self.scroll_offset)
        end = len(msgs) - self.scroll_offset
        return msgs[start:end]

    def get_all_text(self) -> str:
        """Get all messages as a single string"""
        return "\n".join(self.messages)

    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        self.scroll_offset = 0

    def scroll_up(self):
        max_scroll = max(0, len(self.messages) - 20)
        self.scroll_offset = min(self.scroll_offset + 5, max_scroll)

    def scroll_down(self):
        self.scroll_offset = max(0, self.scroll_offset - 5)


# Global debug instance
debug = DebugLog()

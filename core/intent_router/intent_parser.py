"""Legacy rule-based text command parser."""

from __future__ import annotations

import re
from typing import Dict, Optional


class IntentParser:
    """Transform a small declared command grammar into structured intent fields."""

    def __init__(self):
        self.patterns = {
            r"\bmove\s+(left|right|forward|backward)\b": self._parse_move,
            r"\bpick\s+up\b": self._parse_pick_up,
            r"\bdrop\s+(it|object)\b": self._parse_drop,
            r"\bstop\b": self._parse_stop,
            r"\bswitch\s+mode\s+to\s+(\w+)": self._parse_mode_switch,
        }

    def parse(self, input_text: str) -> Optional[Dict]:
        normalized = (input_text or "").strip().lower()
        for pattern, handler in self.patterns.items():
            match = re.search(pattern, normalized)
            if match:
                return handler(match)
        return None

    def _parse_move(self, match):
        return {"intent": "move", "params": {"direction": match.group(1)}}

    def _parse_pick_up(self, _match):
        return {"intent": "pick_up", "params": {}}

    def _parse_drop(self, _match):
        return {"intent": "drop", "params": {}}

    def _parse_stop(self, _match):
        return {"intent": "stop", "params": {}}

    def _parse_mode_switch(self, match):
        return {"intent": "switch_mode", "params": {"mode": match.group(1)}}

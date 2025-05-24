# /core/intent_router/intent_parser.py

"""
Intent Parser Module

This module takes raw user commands, text inputs, or BCI-decoded intents and converts them
into structured intent dictionaries for downstream AGI routing and planning.
"""

import re
from typing import Dict, Optional

class IntentParser:
    """
    A lightweight rule-based intent parser for transforming natural language or decoded
    brain-computer signals into actionable structured commands.
    """

    def __init__(self):
        # Simple intent mapping dictionary (extendable)
        self.patterns = {
            r"\bmove\s+(left|right|forward|backward)\b": self._parse_move,
            r"\bpick\s+up\b": self._parse_pick_up,
            r"\bdrop\s+(it|object)\b": self._parse_drop,
            r"\bstop\b": self._parse_stop,
            r"\bswitch\s+mode\s+to\s+(\w+)": self._parse_mode_switch,
        }

    def parse(self, input_text: str) -> Optional[Dict]:
        """
        Parse an input command into a structured intent dictionary.

        Parameters:
            input_text (str): Raw user or BCI-decoded command text.

        Returns:
            dict: Parsed intent dictionary or None if not understood.
        """
        input_text = input_text.strip().lower()
        for pattern, handler in self.patterns.items():
            match = re.search(pattern, input_text)
            if match:
                return handler(match)
        return None

    def _parse_move(self, match):
        direction = match.group(1)
        return {"intent": "move", "params": {"direction": direction}}

    def _parse_pick_up(self, match):
        return {"intent": "pick_up", "params": {}}

    def _parse_drop(self, match):
        return {"intent": "drop", "params": {}}

    def _parse_stop(self, match):
        return {"intent": "stop", "params": {}}

    def _parse_mode_switch(self, match):
        mode = match.group(1)
        return {"intent": "switch_mode", "params": {"mode": mode}}

# Example usage
if __name__ == "__main__":
    parser = IntentParser()
    test_inputs = [
        "Move left",
        "Pick up",
        "Drop it",
        "Stop",
        "Switch mode to manual"
    ]
    for command in test_inputs:
        parsed = parser.parse(command)
        print(f"Input: {command} → Intent: {parsed}")

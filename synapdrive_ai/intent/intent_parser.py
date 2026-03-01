"""synapdrive_ai.intent.intent_parser

This repo is intentionally **simulation-first**.

We support two "input" shapes:
1) decoded BCI intent text (e.g. "move left", "stop", "switch mode to manual")
2) raw brain-signal labels produced by our simulator (handled elsewhere)

This parser is a *small, deterministic* rule-based layer that translates text into
structured intents suitable for downstream safety checks and actuation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ParsedIntent:
    """A structured intent parsed from text."""

    intent: str
    params: Dict[str, str]


class IntentParser:
    """Rule-based intent parser.

    Keep this conservative: if we don't understand a command, return None.
    """

    def __init__(self) -> None:
        self._patterns = {
            r"\bmove\s+(left|right|forward|backward)\b": self._parse_move,
            r"\bturn\s+(left|right)\b": self._parse_turn,
            r"\bstop\b": self._parse_stop,
            r"\bpick\s+up\b": self._parse_pick_up,
            r"\bdrop\s+(it|object)\b": self._parse_drop,
            r"\bswitch\s+mode\s+to\s+(\w+)\b": self._parse_mode_switch,
        }

    def parse(self, input_text: str) -> Optional[ParsedIntent]:
        if not input_text:
            return None

        text = input_text.strip().lower()
        for pattern, handler in self._patterns.items():
            match = re.search(pattern, text)
            if match:
                return handler(match)
        return None

    def _parse_move(self, match: re.Match) -> ParsedIntent:
        direction = match.group(1)
        return ParsedIntent(intent="move", params={"direction": direction})

    def _parse_turn(self, match: re.Match) -> ParsedIntent:
        direction = match.group(1)
        return ParsedIntent(intent="turn", params={"direction": direction})

    def _parse_pick_up(self, match: re.Match) -> ParsedIntent:
        return ParsedIntent(intent="pick_up", params={})

    def _parse_drop(self, match: re.Match) -> ParsedIntent:
        return ParsedIntent(intent="drop", params={})

    def _parse_stop(self, match: re.Match) -> ParsedIntent:
        return ParsedIntent(intent="stop", params={})

    def _parse_mode_switch(self, match: re.Match) -> ParsedIntent:
        mode = match.group(1)
        return ParsedIntent(intent="switch_mode", params={"mode": mode})

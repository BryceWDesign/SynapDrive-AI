from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


class PermissionGate:
    """Capability-style permission gate for simulated actions.

    STOP/HALT actions are always permitted. By default the simulation namespace is
    allowed except explicit high-risk administrative patterns.
    """

    def __init__(
        self,
        allow_patterns: Iterable[str] = ("*",),
        deny_patterns: Iterable[str] = (
            "*override_security*",
            "*disable_brakes*",
            "*trigger_launch*",
            "*release_payload*",
        ),
    ) -> None:
        self.allow_patterns: Tuple[str, ...] = tuple(allow_patterns)
        self.deny_patterns: Tuple[str, ...] = tuple(deny_patterns)
        self._revoked = False

    def revoke_all(self) -> None:
        self._revoked = True

    def restore(self) -> None:
        self._revoked = False

    def evaluate(self, action: str) -> PermissionDecision:
        normalized = (action or "unknown").strip().lower()
        if any(token in normalized for token in ("halt", "stop", "hold_position")):
            return PermissionDecision(True, "safe-state action permitted")
        if self._revoked:
            return PermissionDecision(False, "all non-safe capabilities revoked")
        if any(fnmatch.fnmatch(normalized, pattern) for pattern in self.deny_patterns):
            return PermissionDecision(False, "action matches denied capability pattern")
        if any(fnmatch.fnmatch(normalized, pattern) for pattern in self.allow_patterns):
            return PermissionDecision(True, "action matches allowed capability pattern")
        return PermissionDecision(False, "action is outside granted capability patterns")

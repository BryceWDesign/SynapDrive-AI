"""Local access tasks with explicit input transitions, draft approval and privacy.

Outputs stay in a local workspace; there are no account, network or physical endpoints.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from synapdrive_ai.pipeline import SynapDrivePipeline
from synapdrive_ai.runtime.dispatch import digest


@dataclass(frozen=True)
class Preferences:
    version: int = 1
    mode: str = "manual"
    confirmations: int = 2
    dwell_ms: int = 700
    minimum_confidence: float = 0.70

    def __post_init__(self):
        if (
            self.version < 1
            or self.mode not in {"manual", "assisted", "bounded-task"}
            or not 1 <= self.confirmations <= 10
            or not 100 <= self.dwell_ms <= 5000
            or not 0.70 <= self.minimum_confidence <= 1
        ):
            raise ValueError("preferences exceed local operating bounds")


class AccessSession:
    def __init__(self, pipeline=None, *, privacy="private"):
        self.pipe = pipeline or SynapDrivePipeline(False)
        self.preferences = Preferences()
        self.privacy = "locked"
        self.inputs: dict[str, dict] = {
            "declared": {"qualified": True, "identity": "exact-grammar"}
        }
        self.active_input = "declared"
        self.pending_input: str | None = None
        self.draft = ""
        self.suggestion = ""
        self.local_outputs: list[str] = []
        self.events: list[dict] = []
        self._approval: tuple[str, str] | None = None
        self._seen_evidence: set[str] = set()
        self._last = ""
        self._count = 0
        self.set_privacy(privacy)

    def set_privacy(self, mode):
        if mode not in {"locked", "private", "local-audited", "research"}:
            raise ValueError("unknown privacy mode")
        self.privacy = mode
        self._approval = None
        self._last, self._count = "", 0
        if mode == "locked":
            self.draft, self.suggestion = "", ""
            self.local_outputs.clear()
            self.events.clear()
            self.pipe.emergency_stop()
        else:
            self.pipe.resume()

    def set_preferences(self, *, actor="user", **changes):
        if actor != "user":
            raise PermissionError("only the user changes automation preferences")
        self.preferences = replace(
            self.preferences, version=self.preferences.version + 1, **changes
        )
        self._approval = None
        self._last, self._count = "", 0
        return self.preferences

    def register_input(self, name, identity, qualified):
        self.inputs[name] = {"identity": identity, "qualified": bool(qualified)}

    def request_input(self, name):
        if not self.inputs.get(name, {}).get("qualified"):
            raise ValueError("input unavailable or unqualified")
        self.pending_input = name

    def confirm_input(self, name):
        if name != self.pending_input or not self.inputs.get(name, {}).get("qualified"):
            raise ValueError("input transition needs current explicit confirmation")
        self.active_input, self.pending_input = name, None
        self._last, self._count = "", 0

    def command(self, command):
        if self.privacy == "locked":
            raise PermissionError("capture and processing locked")
        if self.active_input != "declared":
            raise PermissionError("switch to declared input before issuing a text command")
        return self.pipe.run_text_command(command)

    def decoded(self, packet, input_name):
        if self.privacy == "locked":
            raise PermissionError("capture and processing locked")
        if input_name != self.active_input or not self.inputs.get(input_name, {}).get("qualified"):
            raise PermissionError("input is not active and qualified")
        if packet.get("qualification_id") != self.inputs[input_name]["identity"]:
            raise ValueError("input qualification identity changed")
        evidence_id = packet.get("evidence_id")
        if not isinstance(evidence_id, str) or evidence_id in self._seen_evidence:
            raise ValueError("missing or reused evidence for sequential confirmation")
        if len(self._seen_evidence) >= 10000:
            raise ValueError("session evidence budget exhausted")
        self._seen_evidence.add(evidence_id)
        action = packet.get("intent", "unknown")
        if (
            action in {"unknown", "rest", "no_command"}
            or packet.get("confidence", 0) < self.preferences.minimum_confidence
        ):
            self._last, self._count = "", 0
            return {"status": "waiting", "reason": "no supported command"}
        self._count = self._count + 1 if action == self._last else 1
        self._last = action
        if self._count < self.preferences.confirmations:
            return {"status": "waiting", "reason": "sequential confirmation"}
        self._last, self._count = "", 0
        return self.pipe.run_intent_packet(packet)

    def edit_draft(self, text):
        if self.privacy == "locked":
            raise PermissionError("processing locked")
        if not isinstance(text, str) or len(text.encode()) > 4096:
            raise ValueError("draft exceeds local content budget")
        self.draft = text
        self._approval = None

    def propose(self, text):
        if self.privacy == "locked":
            raise PermissionError("processing locked")
        if len(text.encode()) > 4096:
            raise ValueError("suggestion budget exceeded")
        self.suggestion = text  # Never silently substitutes for the user's draft.

    def approve(self):
        if self.privacy == "locked" or not self.draft:
            raise PermissionError("no output to approve")
        token = secrets.token_hex(16)
        self._approval = (
            token,
            digest({"text": self.draft, "preferences": asdict(self.preferences)}),
        )
        return token

    def commit_local(self, token):
        expected = digest({"text": self.draft, "preferences": asdict(self.preferences)})
        approval, self._approval = self._approval, None
        if self.privacy == "locked" or approval != (token, expected):
            raise PermissionError("missing, stale or consumed exact-output approval")
        self.local_outputs.append(self.draft)
        self.events.append({"event": "local-output", "length": len(self.draft)})
        return self.draft

    def export(self, path, *, content_key=None, consent=False):
        if self.privacy in {"locked", "private"} or not consent:
            raise PermissionError("this mode has no export permission")
        payload = {
            "schema": "synapdrive.access.v2",
            "preferences": asdict(self.preferences),
            "events": self.events,
            "content_retained": content_key is not None,
            "replay_limit": "content omitted unless separately encrypted",
        }
        if content_key is not None:
            from cryptography.fernet import Fernet

            payload["encrypted_content"] = (
                Fernet(content_key)
                .encrypt(json.dumps({"draft": self.draft, "outputs": self.local_outputs}).encode())
                .decode()
            )
        Path(path).write_text(json.dumps(payload, indent=2) + "\n")

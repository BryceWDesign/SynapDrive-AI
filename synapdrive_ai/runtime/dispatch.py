"""Action-bound, single-use local permits and crash-recoverable dispatch journal.

This is a simulation executor boundary, not isolation from arbitrary same-process code.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


class DispatchJournal:
    def __init__(self, path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS dispatch (id TEXT PRIMARY KEY, packet TEXT, outcome TEXT)"
        )
        self.db.commit()

    def prepare(self, cycle: str, packet: dict) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO dispatch VALUES (?, ?, 'prepared')",
                (cycle, json.dumps(packet, allow_nan=False, sort_keys=True)),
            )

    def finish(self, cycle: str, outcome: str) -> None:
        with self.db:
            self.db.execute("UPDATE dispatch SET outcome=? WHERE id=?", (outcome, cycle))

    def unresolved(self) -> list[str]:
        return [
            r[0]
            for r in self.db.execute(
                "SELECT id FROM dispatch WHERE outcome IN ('prepared','unknown')"
            )
        ]

    def reconcile(self, cycle: str, outcome: str) -> None:
        if outcome not in {"confirmed-executed", "confirmed-not-executed"}:
            raise ValueError("explicit outcome required; uncertain actions must not auto-retry")
        if cycle not in self.unresolved():
            raise ValueError("no unresolved dispatch with this id")
        self.finish(cycle, outcome)


@dataclass(frozen=True)
class Permit:
    token: str
    packet_digest: str
    state_digest: str
    policy_digest: str
    capabilities_digest: str
    expires: float


class DispatchGate:
    def __init__(
        self, journal: DispatchJournal | None = None, clock: Callable[[], float] = time.monotonic
    ):
        self.journal = journal or DispatchJournal()
        self.clock = clock
        self.lock = threading.RLock()
        self.stopped = threading.Event()
        self._issued: dict[str, Permit] = {}

    def issue(
        self, packet: dict, state: dict, policy: dict, capabilities: dict, ttl: float = 1.0
    ) -> Permit:
        if not 0 < ttl <= 5:
            raise ValueError("permit TTL must be in (0, 5]")
        with self.lock:
            if self.stopped.is_set() or self.journal.unresolved():
                raise ValueError("dispatch stopped or requires outcome reconciliation")
            self._issued = {k: v for k, v in self._issued.items() if self.clock() < v.expires}
            if len(self._issued) >= 256:
                raise ValueError("permit budget exceeded")
            permit = Permit(
                uuid.uuid4().hex,
                digest(packet),
                digest(state),
                digest(policy),
                digest(capabilities),
                self.clock() + ttl,
            )
            self._issued[permit.token] = permit
            return permit

    def execute(
        self,
        permit: Permit,
        packet: dict,
        state: dict,
        policy: dict,
        capabilities: dict,
        actuator: Callable[[dict], dict],
    ) -> dict:
        with self.lock:
            issued = self._issued.pop(permit.token, None)
            if issued != permit or self.stopped.is_set() or self.clock() >= permit.expires:
                raise ValueError("invalid, used, expired or vetoed permit")
            if (digest(packet), digest(state), digest(policy), digest(capabilities)) != (
                permit.packet_digest,
                permit.state_digest,
                permit.policy_digest,
                permit.capabilities_digest,
            ):
                raise ValueError("permit binding changed")
            self.journal.prepare(
                permit.token,
                {"packet": packet, "world": state, "policy": policy, "capabilities": capabilities},
            )
            if self.stopped.is_set() or self.clock() >= permit.expires:
                self.journal.finish(permit.token, "cancelled-before-dispatch")
                raise ValueError("permit expired or vetoed while preparing dispatch")
            try:
                result = actuator(packet)
                self.journal.finish(permit.token, str(result.get("status", "unknown")))
                return result
            except BaseException:
                self.journal.finish(permit.token, "unknown")
                raise

    def veto(self) -> None:
        self.stopped.set()

    def resume(self) -> None:
        with self.lock:
            if self.journal.unresolved():
                raise ValueError("unresolved action outcomes")
            self._issued.clear()
            self.stopped.clear()

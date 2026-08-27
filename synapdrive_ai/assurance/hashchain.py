from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


def canonical_json(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


@dataclass(frozen=True)
class ChainEntry:
    index: int
    previous_hash: str
    event_hash: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
            "payload": self.payload,
        }


class EvidenceHashChain:
    GENESIS = "0" * 64

    def __init__(self) -> None:
        self._entries: List[ChainEntry] = []

    def append(self, payload: Dict[str, Any]) -> ChainEntry:
        previous = self._entries[-1].event_hash if self._entries else self.GENESIS
        event_hash = self._digest(len(self._entries) + 1, previous, payload)
        entry = ChainEntry(len(self._entries) + 1, previous, event_hash, dict(payload))
        self._entries.append(entry)
        return entry

    def entries(self) -> List[ChainEntry]:
        return list(self._entries)

    @classmethod
    def verify(cls, entries: Iterable[ChainEntry | Dict[str, Any]]) -> bool:
        previous = cls.GENESIS
        for expected_index, raw in enumerate(entries, 1):
            if isinstance(raw, ChainEntry):
                entry = raw
            else:
                entry = ChainEntry(
                    index=int(raw["index"]),
                    previous_hash=str(raw["previous_hash"]),
                    event_hash=str(raw["event_hash"]),
                    payload=dict(raw["payload"]),
                )
            if entry.index != expected_index or entry.previous_hash != previous:
                return False
            expected = cls._digest(entry.index, entry.previous_hash, entry.payload)
            if entry.event_hash != expected:
                return False
            previous = entry.event_hash
        return True

    @staticmethod
    def _digest(index: int, previous_hash: str, payload: Dict[str, Any]) -> str:
        h = hashlib.sha256()
        h.update(str(index).encode("ascii"))
        h.update(b"|")
        h.update(previous_hash.encode("ascii"))
        h.update(b"|")
        h.update(canonical_json(payload))
        return h.hexdigest()

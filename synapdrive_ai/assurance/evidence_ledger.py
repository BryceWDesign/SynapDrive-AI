from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from synapdrive_ai.assurance.hashchain import ChainEntry, EvidenceHashChain


class SessionEvidenceLedger:
    """Tamper-evident append-only evidence ledger for pipeline cycles."""

    def __init__(self) -> None:
        self.chain = EvidenceHashChain()

    def record(self, payload: Dict[str, Any]) -> ChainEntry:
        return self.chain.append(payload)

    def export_jsonl(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as handle:
            for entry in self.chain.entries():
                handle.write(json.dumps(entry.to_dict(), sort_keys=True, default=str) + "\n")

    @staticmethod
    def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
        rows = []
        with Path(path).open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    @staticmethod
    def verify(entries: Iterable[ChainEntry | Dict[str, Any]]) -> bool:
        return EvidenceHashChain.verify(entries)

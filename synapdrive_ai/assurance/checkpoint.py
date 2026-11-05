"""Completeness verification against an independently retained signed checkpoint."""

from __future__ import annotations

import base64

from synapdrive_ai.assurance.hashchain import EvidenceHashChain, canonical_json


def create_checkpoint(entries, run_id, private_key):
    rows = [e.to_dict() if hasattr(e, "to_dict") else e for e in entries]
    if not run_id or not EvidenceHashChain.verify(rows):
        raise ValueError("run identity and valid ledger required")
    payload = {
        "schema": "synapdrive.checkpoint.v2",
        "run_id": run_id,
        "count": len(rows),
        "head": rows[-1]["event_hash"] if rows else EvidenceHashChain.GENESIS,
    }
    return {
        "payload": payload,
        "signature": base64.b64encode(private_key.sign(canonical_json(payload))).decode(),
    }


def verify_checkpoint(entries, checkpoint, run_id, public_key):
    try:
        payload = checkpoint["payload"]
        if payload["schema"] != "synapdrive.checkpoint.v2" or payload["run_id"] != run_id:
            return False
        public_key.verify(
            base64.b64decode(checkpoint["signature"], validate=True), canonical_json(payload)
        )
        return EvidenceHashChain.verify(
            entries, expected_count=payload["count"], expected_head=payload["head"]
        )
    except Exception:
        return False

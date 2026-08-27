from __future__ import annotations

import argparse
import json
from pathlib import Path

from synapdrive_ai.assurance.evidence_ledger import SessionEvidenceLedger
from synapdrive_ai.assurance.signing import Ed25519EvidenceSigner, verify_ed25519


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="SynapDrive evidence-chain and signature utilities."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    verify_chain = sub.add_parser("verify-chain")
    verify_chain.add_argument("evidence")

    keygen = sub.add_parser("keygen")
    keygen.add_argument("--private", required=True)
    keygen.add_argument("--public", required=True)

    sign = sub.add_parser("sign")
    sign.add_argument("evidence")
    sign.add_argument("--private", required=True)
    sign.add_argument("--out", required=True)

    verify_sig = sub.add_parser("verify-signature")
    verify_sig.add_argument("evidence")
    verify_sig.add_argument("--public", required=True)
    verify_sig.add_argument("--signature", required=True)

    args = parser.parse_args(argv)
    if args.command == "verify-chain":
        rows = SessionEvidenceLedger.load_jsonl(args.evidence)
        ok = SessionEvidenceLedger.verify(rows)
        print(json.dumps({"chain_valid": ok, "entries": len(rows)}, indent=2))
        return 0 if ok else 2
    if args.command == "keygen":
        signer = Ed25519EvidenceSigner.generate()
        signer.save_private_pem(args.private)
        signer.save_public_pem(args.public)
        print(json.dumps({"private": args.private, "public": args.public}, indent=2))
        return 0
    if args.command == "sign":
        signer = Ed25519EvidenceSigner.load_private_pem(args.private)
        signature = signer.sign_file(args.evidence)
        Path(args.out).write_text(json.dumps(signature, indent=2), encoding="utf-8")
        print(json.dumps(signature, indent=2))
        return 0

    signature = json.loads(Path(args.signature).read_text(encoding="utf-8"))
    payload = Path(args.evidence).read_bytes()
    ok = verify_ed25519(Path(args.public).read_bytes(), payload, signature["signature_b64"])
    print(json.dumps({"signature_valid": ok, "algorithm": signature.get("algorithm")}, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

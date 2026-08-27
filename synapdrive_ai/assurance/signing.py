from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class Ed25519EvidenceSigner:
    """Detached Ed25519 signatures for exported evidence bytes."""

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self.private_key = private_key

    @classmethod
    def generate(cls) -> "Ed25519EvidenceSigner":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def load_private_pem(cls, path: str | Path) -> "Ed25519EvidenceSigner":
        key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise TypeError("private key is not Ed25519")
        return cls(key)

    def save_private_pem(self, path: str | Path) -> None:
        raw = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        Path(path).write_bytes(raw)

    def save_public_pem(self, path: str | Path) -> None:
        raw = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        Path(path).write_bytes(raw)

    def sign(self, payload: bytes) -> str:
        return base64.b64encode(self.private_key.sign(payload)).decode("ascii")

    def sign_file(self, path: str | Path) -> dict[str, str]:
        payload = Path(path).read_bytes()
        return {
            "algorithm": "Ed25519",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "signature_b64": self.sign(payload),
        }


def verify_ed25519(public_pem: bytes, payload: bytes, signature_b64: str) -> bool:
    key = serialization.load_pem_public_key(public_pem)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("public key is not Ed25519")
    try:
        key.verify(base64.b64decode(signature_b64), payload)
    except (InvalidSignature, ValueError):
        return False
    return True

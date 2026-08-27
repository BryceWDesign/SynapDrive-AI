from synapdrive_ai.assurance.signing import Ed25519EvidenceSigner, verify_ed25519


def test_ed25519_sign_and_verify(tmp_path):
    signer = Ed25519EvidenceSigner.generate()
    public = tmp_path / "public.pem"
    signer.save_public_pem(public)
    payload = b"evidence"
    signature = signer.sign(payload)
    assert verify_ed25519(public.read_bytes(), payload, signature) is True


def test_ed25519_detects_tamper(tmp_path):
    signer = Ed25519EvidenceSigner.generate()
    public = tmp_path / "public.pem"
    signer.save_public_pem(public)
    signature = signer.sign(b"evidence")
    assert verify_ed25519(public.read_bytes(), b"tampered", signature) is False


def test_private_key_roundtrip(tmp_path):
    signer = Ed25519EvidenceSigner.generate()
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    signer.save_private_pem(private)
    signer.save_public_pem(public)
    loaded = Ed25519EvidenceSigner.load_private_pem(private)
    signature = loaded.sign(b"abc")
    assert verify_ed25519(public.read_bytes(), b"abc", signature) is True

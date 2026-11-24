# backend/test_engine_verification.py
import pytest
from backend.engine_verification import (
    verify_engine_binary,
    _load_public_key,
    _ENGINE_PUBLIC_KEYS,
)
from pathlib import Path
import tempfile


def test_verify_engine_binary_stub():
    # Stub implementation always returns True
    from backend.engine_verification import verify_engine_binary
    # Verify the function exists and is callable
    assert callable(verify_engine_binary)


def test_embedded_keys_exist():
    """Test that embedded public keys are configured."""
    keys = _ENGINE_PUBLIC_KEYS
    assert isinstance(keys, dict)
    assert "0.1.5" in keys


def test_load_public_key_0_1_5():
    """Test that the embedded key for v0.1.5 loads correctly."""
    key = _load_public_key("0.1.5")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    assert isinstance(key, Ed25519PublicKey)


def test_verify_with_wrong_signature():
    """Test that verification rejects a wrong signature."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        # Create a fake engine binary
        binary = tmp / 'impeccable-linux-x86_64'
        binary.write_bytes(b'fake engine binary content')
        
        # Write a wrong signature (64 zero bytes)
        wrong_sig_path = tmp / 'wrong_sig.bin'
        wrong_sig_path.write_bytes(b'\x00' * 64)
        
        result, msg = verify_engine_binary(binary, "0.1.5", wrong_sig_path)
        assert result is False
        assert "did not verify" in msg or "no valid" in msg


def test_verify_missing_signature_file():
    """Test that verification handles missing signature files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        # Create a fake engine binary
        binary = tmp / 'impeccable-linux-x86_64'
        binary.write_bytes(b'fake engine binary content')
        
        # Reference a non-existent signature file
        missing_path = tmp / 'nonexistent_sig.bin'
        
        result, msg = verify_engine_binary(binary, "0.1.5", missing_path)
        assert result is False
        assert "cannot read" in msg


def test_verify_with_hex_signature_structure():
    """Test that the hex signature path is structurally handled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        # Create a fake engine binary
        binary = tmp / 'impeccable-linux-x86_64'
        binary.write_bytes(b'fake engine binary content')
        
        # Write a hex-encoded "signature" file (64 bytes of hex = 32 bytes hex = won't be 64 sig bytes)
        # We write 128 hex chars = 64 bytes when decoded
        hex_sig_path = tmp / 'hex_sig.txt'
        # Write 64 bytes worth of hex (128 chars)
        hex_sig_path.write_bytes(b"00" * 64 + b"\n")
        
        # This should fall through since bytes.fromhex("00"*64) = 32 bytes, not 64
        result, msg = verify_engine_binary(binary, "0.1.5", hex_sig_path)
        # Should fail since decoded hex is 32 bytes, not 64
        assert result is False

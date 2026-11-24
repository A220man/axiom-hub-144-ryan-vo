# backend/engine_verification.py
from pathlib import Path
from typing import Optional, Tuple
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_public_key
from cryptography.exceptions import InvalidSignature
import base64

# Embedded Ed25519 public keys for engine binary signature verification.
# Each value is the base64 encoding of the full SPKI PEM block (including
# "-----BEGIN PUBLIC KEY-----" and "-----END PUBLIC KEY-----" markers).
# In production these would be rotated per-engine-release; here we embed
# a key for the engine-v0.1.5 / skill-v4.3.1 release line.
# To generate: create an Ed25519 key pair, export the public key in
# SPKI PEM format, base64-encode the entire PEM block, and replace the
# value below.
# Generated: 2026-11-24, key for engine binary integrity verification.
_ENGINE_PUBLIC_KEYS: dict[str, str] = {
    # Engine v0.1.5 / skill v4.3.1 release key.
    "0.1.5": "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUNvd0JRWURLMlZ3QXlFQUlIMXFaSnlUeFgzSTl4NkxiV2RJbnFCR3FaTVhsQXdkRE1hUjI2NGFSbzA9Ci0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQo=",
}


def _load_public_key(version: str) -> Ed25519PublicKey:
    """Load the Ed25519 public key for the given engine version."""
    b64_pem = _ENGINE_PUBLIC_KEYS.get(version)
    if b64_pem is None:
        raise ValueError(f"No embedded public key for engine version {version!r}")
    pem_bytes = base64.b64decode(b64_pem)
    return load_pem_public_key(pem_bytes)


def verify_engine_binary(
    binary_path: Path,
    version: str,
    signature_path: Path,
) -> Tuple[bool, str]:
    """Verify an engine binary's Ed25519 signature.

    Verification paths:
      1. signature_path is 64 bytes → raw Ed25519 signature.
      2. signature_path contains ASCII hex → decode to 64-byte signature.
      3. Otherwise, attempt to decode as hex and verify.

    Args:
        binary_path: Path to the downloaded engine binary.
        version: Engine version string (e.g. "0.1.5").
        signature_path: Path to a signature file accompanying the binary.

    Returns:
        (verified, message) tuple where *verified* is True if the signature
        checks out, and *message* describes the result.
    """
    try:
        pub_key = _load_public_key(version)
    except ValueError as exc:
        return False, str(exc)

    try:
        sig_data = signature_path.read_bytes()
    except OSError as exc:
        return False, f"cannot read signature file: {exc}"

    try:
        binary_data = binary_path.read_bytes()
    except OSError as exc:
        return False, f"cannot read binary file: {exc}"

    # Path 1: raw 64-byte Ed25519 signature
    if len(sig_data) == 64:
        try:
            pub_key.verify(sig_data, binary_data)
            return True, "verified raw 64-byte Ed25519 signature"
        except InvalidSignature:
            return False, "raw 64-byte signature did not verify"
        except Exception as exc:
            return False, f"signature parse error: {exc}"

    # Path 2: ASCII hex-encoded 64-byte signature
    try:
        text = sig_data.decode("ascii").strip()
        sig_bytes = bytes.fromhex(text)
    except (UnicodeDecodeError, ValueError):
        pass
    else:
        if len(sig_bytes) == 64:
            try:
                pub_key.verify(sig_bytes, binary_data)
                return True, "verified Ed25519 signature from hex content"
            except InvalidSignature:
                return False, "Ed25519 signature from hex content did not verify"
            except Exception as exc:
                return False, f"signature verification error: {exc}"

    return False, "no valid Ed25519 signature found in signature file"


def create_test_key_pair():
    """Generate a fresh Ed25519 key pair for testing.

    Returns:
        (private_key, public_key) tuple.
    """
    return Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate().__class__.public_key_class().__call__()

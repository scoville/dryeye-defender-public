"""License key generation and validation."""
import base64

from dryeye_defender.licensing.keygen import (
    VERIFYING_KEY_STRING,
    generate_license_key,
    generate_sk_and_vk,
    validate_license_key,
)

# Signed by python-ecdsa 0.18.0 Ed25519 over b"user@example.com.42" with seed 0x11 * 32.
# No issued license for VERIFYING_KEY_STRING is checked in, so this vector is the
# compatibility lock for keys already signed by the old library.
ECDSA_018_SIGNING_KEY = "11" * 32
ECDSA_018_VERIFYING_KEY = "d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737"
ECDSA_018_LICENSE = (
    "dXNlckBleGFtcGxlLmNvbS40Mg==."
    "vlL8i51x2+xklswcWElHxF3WojTL/bI9dATqcMdNOcZtPyOoPcUnn3edOoKaPXDhqRqXgPDhGSqoYDb649pmCA=="
)


def test_generated_license_key_validates_with_matching_verifying_key() -> None:
    """A freshly generated Ed25519 keypair must verify its own license."""
    signing_key, verifying_key = generate_sk_and_vk()
    license_key = generate_license_key("user@example.com", 42, signing_key)

    assert validate_license_key(license_key, verifying_key) is True


def test_ecdsa_018_license_still_validates() -> None:
    """A signature produced by python-ecdsa 0.18.0 must still verify."""
    assert validate_license_key(ECDSA_018_LICENSE, ECDSA_018_VERIFYING_KEY) is True
    assert generate_license_key("user@example.com", 42, ECDSA_018_SIGNING_KEY) == ECDSA_018_LICENSE


def test_shipped_verifying_key_rejects_unrelated_license() -> None:
    """The default production key is used, and it must not accept another key's license."""
    assert validate_license_key(ECDSA_018_LICENSE) is False
    assert validate_license_key(ECDSA_018_LICENSE, VERIFYING_KEY_STRING) is False


def test_validate_license_key_rejects_tampered_payload() -> None:
    """Rewriting the email or order number while keeping the signature must fail."""
    signing_key, verifying_key = generate_sk_and_vk()
    license_key = generate_license_key("user@example.com", 42, signing_key)
    _payload, signature = license_key.split(".")
    other_payload = base64.b64encode(b"other@example.com.99").decode()

    assert validate_license_key(f"{other_payload}.{signature}", verifying_key) is False


def test_validate_license_key_rejects_tampered_signature() -> None:
    """A still-decodable signature mutation must fail in verify, not in base64."""
    signing_key, verifying_key = generate_sk_and_vk()
    license_key = generate_license_key("user@example.com", 42, signing_key)
    payload, signature = license_key.split(".")
    signature_bytes = bytearray(base64.b64decode(signature))
    signature_bytes[0] ^= 0x01
    tampered_signature = base64.b64encode(bytes(signature_bytes)).decode()

    assert validate_license_key(f"{payload}.{tampered_signature}", verifying_key) is False


def test_validate_license_key_rejects_other_verifying_key() -> None:
    """A well-formed signature must not verify under a different public key."""
    signing_key, verifying_key = generate_sk_and_vk()
    _other_signing_key, other_verifying_key = generate_sk_and_vk()
    license_key = generate_license_key("user@example.com", 42, signing_key)

    assert verifying_key != other_verifying_key
    assert validate_license_key(license_key, other_verifying_key) is False


def test_validate_license_key_rejects_malformed_input() -> None:
    """Garbage input is a rejected license, not an exception."""
    assert validate_license_key("not-a-license") is False

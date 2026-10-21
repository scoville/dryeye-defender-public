"""License key generation and validation."""
from dryeye_defender.licensing.keygen import (
    generate_license_key,
    generate_sk_and_vk,
    validate_license_key,
)


def test_generated_license_key_validates_with_matching_verifying_key() -> None:
    """A key signed with a fresh Ed25519 seed must verify against its public key."""
    signing_key, verifying_key = generate_sk_and_vk()
    license_key = generate_license_key("user@example.com", 42, signing_key)

    assert validate_license_key(license_key, verifying_key) is True


def test_validate_license_key_rejects_tampered_payload() -> None:
    """Changing the signed payload must fail closed."""
    signing_key, verifying_key = generate_sk_and_vk()
    license_key = generate_license_key("user@example.com", 42, signing_key)
    payload, signature = license_key.split(".")
    flipped = "A" if signature[0] != "A" else "B"
    tampered = f"{payload}.{flipped}{signature[1:]}"

    assert validate_license_key(tampered, verifying_key) is False


def test_validate_license_key_rejects_malformed_input() -> None:
    """Garbage input is a user error, not an exception."""
    assert validate_license_key("not-a-license") is False

from types import SimpleNamespace

import pytest

import utils.encryption as encryption
from utils.encryption import encrypted, decrypted, rekey_collection


def test_rekey_collection_reencrypts_selected_attribute():
    old_key = b"0123456789abcdef0123456789abcdef"
    new_key = b"fedcba9876543210fedcba9876543210"

    records = [
        SimpleNamespace(secret=encrypted(old_key, "alpha")),
        SimpleNamespace(secret=encrypted(old_key, "beta")),
    ]

    rekey_collection(records, old_key, new_key, "secret")

    assert decrypted(new_key, records[0].secret) == "alpha"
    assert decrypted(new_key, records[1].secret) == "beta"
    assert records[0].secret != encrypted(old_key, "alpha")


def test_rekey_collection_rejects_missing_attribute():
    old_key = b"0123456789abcdef0123456789abcdef"
    new_key = b"fedcba9876543210fedcba9876543210"

    records = [SimpleNamespace(other="value")]

    try:
        rekey_collection(records, old_key, new_key, "secret")
    except ValueError as exc:
        assert "secret" in str(exc)
    else:
        raise AssertionError("Expected rekey_collection to raise ValueError")


def test_rekey_collection_does_not_partially_update_on_error():
    old_key = b"0123456789abcdef0123456789abcdef"
    new_key = b"fedcba9876543210fedcba9876543210"

    records = [
        SimpleNamespace(secret=encrypted(old_key, "alpha")),
        SimpleNamespace(other="value"),
    ]

    with pytest.raises(ValueError):
        rekey_collection(records, old_key, new_key, "secret")

    assert decrypted(old_key, records[0].secret) == "alpha"


def test_encrypted_rejects_non_string_payload():
    with pytest.raises((TypeError, ValueError)):
        encrypted(b"0123456789abcdef0123456789abcdef", None)


def test_decrypted_returns_plaintext_when_payload_is_already_cleartext():
    value = "already-readable"

    assert decrypted(b"0123456789abcdef0123456789abcdef", value) == value


def test_make_cipher_rejects_invalid_key_length():
    with pytest.raises(ValueError, match="32 bytes"):
        encryption.make_cipher(b"short")


def test_make_key_uses_development_defaults_when_secrets_are_missing(monkeypatch):
    monkeypatch.setattr(encryption, "SECRET_KEY", "")
    monkeypatch.setattr(encryption, "SECOND_KEY", "")

    key = encryption.make_key(b"0123456789abcdef0123456789abcdef", "password")

    assert isinstance(key, bytes)
    assert len(key) == 32

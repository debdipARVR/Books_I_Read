from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parent
SECRETS_TOML = ROOT / ".streamlit" / "secrets.toml"
KEY_FILE = ROOT / ".streamlit" / "fernet.key"
COVERS_DIR = ROOT / "uploads" / "covers"

FERNET_ENV_NAMES = ("FERNET_KEY", "COVER_FERNET_KEY")


def _from_mapping(data: dict) -> str | None:
    for name in FERNET_ENV_NAMES:
        value = data.get(name)
        if value:
            return str(value).strip()
    nested = data.get("fernet")
    if isinstance(nested, dict):
        for name in ("key", "FERNET_KEY"):
            value = nested.get(name)
            if value:
                return str(value).strip()
    return None


def _from_secrets_toml() -> str | None:
    if not SECRETS_TOML.is_file():
        return None
    try:
        import tomllib

        data = tomllib.loads(SECRETS_TOML.read_text(encoding="utf-8"))
    except Exception:
        return None
    return _from_mapping(data) if isinstance(data, dict) else None


def _from_streamlit() -> str | None:
    try:
        import streamlit as st

        return _from_mapping(dict(st.secrets))
    except Exception:
        return None


def load_fernet_key() -> bytes:
    """CLI / offline helper. The website does not use this — it asks the visitor."""
    for name in FERNET_ENV_NAMES:
        env = os.environ.get(name, "").strip()
        if env:
            return env.encode("ascii")

    for reader in (_from_streamlit, _from_secrets_toml):
        value = reader()
        if value:
            return value.encode("ascii")

    if KEY_FILE.is_file():
        text = KEY_FILE.read_text(encoding="utf-8").strip()
        if text:
            return text.encode("ascii")

    raise RuntimeError(
        "Fernet key not found. Enter it in the app, or set FERNET_KEY for encrypt_covers.py."
    )


def normalize_key(key: str | bytes) -> bytes:
    if isinstance(key, bytes):
        return key.strip()
    return key.strip().encode("ascii")


def fernet_from_key(key: str | bytes) -> Fernet:
    return Fernet(normalize_key(key))


@lru_cache(maxsize=1)
def fernet() -> Fernet:
    return Fernet(load_fernet_key())


def encrypt_bytes(data: bytes, key: str | bytes | None = None) -> bytes:
    cipher = fernet_from_key(key) if key is not None else fernet()
    return cipher.encrypt(data)


def decrypt_bytes(token: bytes, key: str | bytes | None = None) -> bytes:
    if key is None or (isinstance(key, str) and not key.strip()):
        raise RuntimeError("Enter the Fernet key to decrypt covers.")
    return fernet_from_key(key).decrypt(token)


def looks_encrypted(data: bytes) -> bool:
    return data.startswith(b"gAAAAA")


def encrypted_cover_path(path: Path) -> Path:
    if path.name.endswith(".enc"):
        return path
    return path.with_name(path.name + ".enc")


def first_encrypted_cover() -> Path | None:
    if not COVERS_DIR.is_dir():
        return None
    return next(iter(sorted(COVERS_DIR.glob("*.enc"))), None)


def try_unlock(key: str, sample: Path | None = None) -> str | None:
    """Return an error message, or None if the key unlocks the shelf."""
    if not (key or "").strip():
        return "Paste your Fernet key to decrypt the covers."
    try:
        cipher = fernet_from_key(key)
    except Exception:
        return "That is not a valid Fernet key."
    probe = sample or first_encrypted_cover()
    if probe and probe.is_file():
        try:
            cipher.decrypt(probe.read_bytes())
        except InvalidToken:
            return "This key does not decrypt the covers on this shelf."
        except OSError:
            return "Could not read an encrypted cover to check the key."
    return None


def write_encrypted_cover(path: Path, jpeg_bytes: bytes, key: str | bytes | None = None) -> Path:
    dest = encrypted_cover_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(encrypt_bytes(jpeg_bytes, key))
    return dest


def read_cover_bytes(path: Path, key: str | bytes | None = None) -> bytes:
    data = path.read_bytes()
    if path.name.endswith(".enc") or looks_encrypted(data):
        if key is None or (isinstance(key, str) and not key.strip()):
            raise RuntimeError("Enter the Fernet key to decrypt covers.")
        try:
            return decrypt_bytes(data, key)
        except InvalidToken as exc:
            raise RuntimeError(f"Could not decrypt cover {path.name}. Check the Fernet key.") from exc
    return data

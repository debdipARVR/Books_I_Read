from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parent
SECRETS_TOML = ROOT / ".streamlit" / "secrets.toml"
KEY_FILE = ROOT / ".streamlit" / "fernet.key"

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
        "Fernet key not found. Set FERNET_KEY in .streamlit/secrets.toml "
        "(local) or Streamlit Cloud secrets, or export FERNET_KEY."
    )


@lru_cache(maxsize=1)
def fernet() -> Fernet:
    return Fernet(load_fernet_key())


def encrypt_bytes(data: bytes) -> bytes:
    return fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return fernet().decrypt(token)


def looks_encrypted(data: bytes) -> bool:
    return data.startswith(b"gAAAAA")


def encrypted_cover_path(path: Path) -> Path:
    if path.name.endswith(".enc"):
        return path
    return path.with_name(path.name + ".enc")


def write_encrypted_cover(path: Path, jpeg_bytes: bytes) -> Path:
    dest = encrypted_cover_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(encrypt_bytes(jpeg_bytes))
    return dest


def read_cover_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.name.endswith(".enc") or looks_encrypted(data):
        try:
            return decrypt_bytes(data)
        except InvalidToken as exc:
            raise RuntimeError(f"Could not decrypt cover {path.name}. Check FERNET_KEY.") from exc
    return data

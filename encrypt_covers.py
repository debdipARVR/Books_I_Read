"""Encrypt cover images at rest with Fernet. Decrypt happens in-memory at runtime."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from PIL import Image

from crypto_covers import (
    KEY_FILE,
    ROOT,
    SECRETS_TOML,
    encrypt_bytes,
    encrypted_cover_path,
    looks_encrypted,
)

COVERS = ROOT / "uploads" / "covers"
DATA = ROOT / "data" / "library.json"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def ensure_key() -> str:
    if KEY_FILE.is_file():
        existing = KEY_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    key = Fernet.generate_key().decode("ascii")
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(key + "\n", encoding="utf-8")

    if not SECRETS_TOML.is_file():
        SECRETS_TOML.write_text(f'FERNET_KEY = "{key}"\n', encoding="utf-8")
    elif "FERNET_KEY" not in SECRETS_TOML.read_text(encoding="utf-8"):
        with SECRETS_TOML.open("a", encoding="utf-8") as handle:
            handle.write(f'\nFERNET_KEY = "{key}"\n')
    return key


def jpeg_bytes(path: Path) -> bytes:
    with Image.open(path) as img:
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92, optimize=True)
        return buf.getvalue()


def encrypt_file(path: Path) -> Path:
    dest = encrypted_cover_path(path)
    raw = path.read_bytes()
    if looks_encrypted(raw):
        if dest != path:
            dest.write_bytes(raw)
            path.unlink()
        return dest
    payload = raw if path.suffix.lower() in {".jpg", ".jpeg"} else jpeg_bytes(path)
    dest.write_bytes(encrypt_bytes(payload))
    if dest != path:
        path.unlink()
    return dest


def rewrite_library() -> int:
    if not DATA.is_file():
        return 0
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    changed = 0
    for book in payload.get("books", []):
        raw = book.get("cover_path") or ""
        if not raw:
            continue
        path = Path(raw)
        if path.name.endswith(".enc"):
            continue
        new_path = encrypted_cover_path(path).as_posix()
        if new_path != raw:
            book["cover_path"] = new_path
            changed += 1
    DATA.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return changed


def main() -> None:
    key = ensure_key()
    print("FERNET_KEY (keep this private; also in .streamlit/secrets.toml):")
    print(key)

    COVERS.mkdir(parents=True, exist_ok=True)
    encrypted = 0
    skipped = 0
    for path in sorted(COVERS.iterdir()):
        if not path.is_file():
            continue
        if path.name.endswith(".enc"):
            skipped += 1
            continue
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        encrypt_file(path)
        encrypted += 1
        print(f"encrypted {path.name}")

    updated = rewrite_library()
    print(f"Done. Encrypted {encrypted} images, {skipped} already .enc, updated {updated} library paths.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

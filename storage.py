from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "library.json"
UPLOADS = ROOT / "uploads"

CATEGORIES = [
    "Tech / Python",
    "Habits / Productivity",
    "Mind / Spiritual",
    "Business / Finance",
    "Literature",
    "Health / Wellness",
    "Biography",
    "Other",
]


def _empty_library() -> dict[str, Any]:
    return {
        "books": [],
        "settings": {
            "pages_per_hour": 30,
            "minutes_per_day": 45,
            "mode": "sequential",
            "start_date": date.today().isoformat(),
            "rest_weekdays": [],
        },
        "progress_log": [],
    }


def ensure_dirs() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    (UPLOADS / "covers").mkdir(parents=True, exist_ok=True)


def load_library() -> dict[str, Any]:
    ensure_dirs()
    if not DATA_PATH.is_file():
        DATA_PATH.write_text(json.dumps(_empty_library(), indent=2), encoding="utf-8")
    with DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_library(payload: dict[str, Any]) -> None:
    ensure_dirs()
    DATA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def new_book(
    *,
    title: str,
    author: str = "",
    pages: int = 0,
    cover_path: str = "",
    notes: str = "",
    priority: int = 3,
    source_image: str = "",
    category: str = "Other",
) -> dict[str, Any]:
    cat = category.strip() if category else "Other"
    if cat not in CATEGORIES:
        cat = "Other"
    return {
        "id": str(uuid.uuid4()),
        "title": title.strip() or "Untitled",
        "author": author.strip(),
        "pages": max(int(pages or 0), 0),
        "pages_read": 0,
        "cover_path": cover_path,
        "notes": notes.strip(),
        "priority": int(priority),
        "status": "unread",
        "category": cat,
        "source_image": source_image,
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }


def append_progress(
    library: dict[str, Any],
    book: dict[str, Any],
    pages: int,
    *,
    note: str = "",
) -> dict[str, Any]:
    """Add pages to a book, write a progress_log entry, and auto-finish at 100%."""
    pages = max(int(pages or 0), 0)
    if pages <= 0:
        return {"added": 0, "finished": False, "celebration": False}

    total = max(int(book.get("pages") or 0), 0)
    before = int(book.get("pages_read") or 0)
    if total:
        added = min(pages, max(total - before, 0))
    else:
        added = pages
    if added <= 0:
        return {"added": 0, "finished": False, "celebration": False}

    book["pages_read"] = before + added
    if book.get("status") == "unread":
        book["status"] = "reading"

    finished = False
    celebration = False
    if total and book["pages_read"] >= total:
        book["pages_read"] = total
        if book.get("status") != "done":
            celebration = True
        book["status"] = "done"
        finished = True

    library.setdefault("progress_log", []).append(
        {
            "id": str(uuid.uuid4()),
            "book_id": book["id"],
            "title": book.get("title") or "Untitled",
            "pages": added,
            "note": note,
            "at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return {"added": added, "finished": finished, "celebration": celebration}

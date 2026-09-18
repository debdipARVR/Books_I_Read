from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Any


WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def remaining_pages(book: dict[str, Any]) -> int:
    return max(int(book.get("pages") or 0) - int(book.get("pages_read") or 0), 0)


def daily_page_budget(settings: dict[str, Any]) -> int:
    pages_per_hour = max(float(settings.get("pages_per_hour") or 30), 1)
    minutes = max(int(settings.get("minutes_per_day") or 45), 5)
    return max(int(round(pages_per_hour * (minutes / 60.0))), 1)


def active_books(books: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = [
        book
        for book in books
        if book.get("status") != "done" and remaining_pages(book) > 0
    ]
    return sorted(queue, key=lambda book: (-int(book.get("priority") or 0), book.get("title") or ""))


def build_schedule(
    books: list[dict[str, Any]],
    settings: dict[str, Any],
    horizon_days: int = 1200,
) -> list[dict[str, Any]]:
    queue = [
        {
            "id": book["id"],
            "title": book.get("title") or "Untitled",
            "left": remaining_pages(book),
            "priority": int(book.get("priority") or 3),
        }
        for book in active_books(books)
    ]
    if not queue:
        return []

    budget = daily_page_budget(settings)
    rest = {int(day) for day in settings.get("rest_weekdays") or []}
    start = date.fromisoformat(settings.get("start_date") or date.today().isoformat())
    mode = settings.get("mode") or "sequential"

    leftovers = {item["id"]: item["left"] for item in queue}
    titles = {item["id"]: item["title"] for item in queue}
    days: list[dict[str, Any]] = []
    cursor = start
    safety = 0

    while any(pages > 0 for pages in leftovers.values()) and safety < horizon_days:
        safety += 1
        if cursor.weekday() in rest:
            days.append({"date": cursor.isoformat(), "rest": True, "assignments": [], "pages": 0})
            cursor += timedelta(days=1)
            continue

        remaining_budget = budget
        assignments: list[dict[str, Any]] = []

        if mode == "parallel":
            live = [item for item in queue if leftovers[item["id"]] > 0]
            weight = sum(max(item["priority"], 1) for item in live) or 1
            for item in live:
                share = max(int(round(budget * (item["priority"] / weight))), 1)
                take = min(share, leftovers[item["id"]], remaining_budget)
                if take <= 0:
                    continue
                leftovers[item["id"]] -= take
                remaining_budget -= take
                assignments.append({"book_id": item["id"], "title": titles[item["id"]], "pages": take})
                if remaining_budget <= 0:
                    break
        else:
            for item in queue:
                if leftovers[item["id"]] <= 0 or remaining_budget <= 0:
                    continue
                take = min(leftovers[item["id"]], remaining_budget)
                leftovers[item["id"]] -= take
                remaining_budget -= take
                assignments.append({"book_id": item["id"], "title": titles[item["id"]], "pages": take})
                if remaining_budget <= 0:
                    break

        days.append(
            {
                "date": cursor.isoformat(),
                "rest": False,
                "assignments": assignments,
                "pages": sum(item["pages"] for item in assignments),
            }
        )
        cursor += timedelta(days=1)

    return days


def estimated_finish(schedule: list[dict[str, Any]]) -> str | None:
    reading_days = [day for day in schedule if not day.get("rest") and day.get("pages")]
    if not reading_days:
        return None
    return reading_days[-1]["date"]


def days_until_book_finish(book: dict[str, Any], settings: dict[str, Any]) -> int | None:
    left = remaining_pages(book)
    if left <= 0:
        return 0
    budget = daily_page_budget(settings)
    rest = {int(day) for day in settings.get("rest_weekdays") or []}
    cursor = date.today()
    days = 0
    safety = 0
    while left > 0 and safety < 2000:
        safety += 1
        if cursor.weekday() not in rest:
            left -= budget
            days += 1
        cursor += timedelta(days=1)
    return days


def _log_dates(progress_log: list[dict[str, Any]]) -> set[date]:
    dates: set[date] = set()
    for entry in progress_log or []:
        raw = entry.get("at") or ""
        try:
            dates.add(datetime.fromisoformat(raw).date())
        except ValueError:
            try:
                dates.add(date.fromisoformat(raw[:10]))
            except ValueError:
                continue
    return dates


def reading_streak(progress_log: list[dict[str, Any]]) -> int:
    dates = _log_dates(progress_log)
    if not dates:
        return 0
    streak = 0
    cursor = date.today()
    # Allow streak to start from yesterday if nothing logged today yet
    if cursor not in dates:
        cursor -= timedelta(days=1)
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def pages_in_range(progress_log: list[dict[str, Any]], start: date, end: date) -> int:
    total = 0
    for entry in progress_log or []:
        raw = entry.get("at") or ""
        try:
            day = datetime.fromisoformat(raw).date()
        except ValueError:
            try:
                day = date.fromisoformat(raw[:10])
            except ValueError:
                continue
        if start <= day <= end:
            total += int(entry.get("pages") or 0)
    return total


def reading_score(
    books: list[dict[str, Any]],
    progress_log: list[dict[str, Any]],
    settings: dict[str, Any],
) -> dict[str, Any]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    pages_week = pages_in_range(progress_log, week_start, today)
    pages_total = sum(int(entry.get("pages") or 0) for entry in progress_log or [])
    finished = sum(1 for book in books if book.get("status") == "done")
    streak = reading_streak(progress_log)
    active_days = len(_log_dates(progress_log))
    avg_day = round(pages_total / active_days, 1) if active_days else 0.0
    budget = daily_page_budget(settings)
    speed_bonus = min(int(avg_day), budget * 2) * 2

    score = (
        pages_total
        + finished * 50
        + streak * 15
        + pages_week * 2
        + speed_bonus
    )
    return {
        "score": int(score),
        "streak": streak,
        "pages_week": pages_week,
        "pages_total": pages_total,
        "finished": finished,
        "avg_pages_day": avg_day,
    }


def length_label(pages: int) -> str:
    if pages <= 0:
        return "Unknown length"
    if pages <= 160:
        return "Quick read"
    if pages <= 350:
        return "Medium read"
    return "Deep dive"


def recommend_books(
    books: list[dict[str, Any]],
    *,
    limit: int = 3,
    prefer_category: str | None = None,
) -> list[dict[str, Any]]:
    unread = [book for book in books if (book.get("status") or "unread") == "unread"]
    if not unread:
        return []

    def rank(book: dict[str, Any]) -> tuple:
        pages = int(book.get("pages") or 0)
        priority = int(book.get("priority") or 0)
        cat_bonus = 2 if prefer_category and book.get("category") == prefer_category else 0
        # Prefer higher priority, then shorter books as easier wins, then category match
        return (-(priority + cat_bonus), pages if pages else 9999, book.get("title") or "")

    ranked = sorted(unread, key=rank)
    return ranked[:limit]


def surprise_pick(books: list[dict[str, Any]]) -> dict[str, Any] | None:
    pool = [book for book in books if (book.get("status") or "unread") in {"unread", "reading"}]
    if not pool:
        return None
    weights = [max(int(book.get("priority") or 1), 1) for book in pool]
    return random.choices(pool, weights=weights, k=1)[0]

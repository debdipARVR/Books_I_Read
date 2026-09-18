from __future__ import annotations

import base64
import html
import io
from datetime import date
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

from analytics import (
    activity_charts,
    category_donut,
    completion_projections,
    length_distribution,
    priority_bars,
    status_donut,
    weekly_trend,
)
from planner import (
    WEEKDAY_NAMES,
    active_books,
    build_schedule,
    daily_page_budget,
    days_until_book_finish,
    estimated_finish,
    length_label,
    reading_score,
    recommend_books,
    remaining_pages,
    surprise_pick,
)
from storage import CATEGORIES, UPLOADS, append_progress, load_library, new_book, save_library

st.set_page_config(page_title="Shelf Plan", page_icon="📖", layout="wide")

st.markdown(
    """
    <style>
      @import url("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600&display=swap");
      html, body, [class*="css"] { font-family: "Source Sans 3", sans-serif; }
      .stApp {
        background:
          radial-gradient(900px 420px at 8% -8%, #fff6e8 0%, transparent 55%),
          linear-gradient(180deg, #f4ead8 0%, #e7d5b8 100%);
        color: #2b2118;
      }
      .block-container { padding-top: 1.1rem; padding-bottom: 3rem; max-width: 1180px; }
      h1, h2, h3 { font-family: "Fraunces", serif; color: #3a2718; letter-spacing: -0.02em; }
      header[data-testid="stHeader"] { background: transparent; }
      #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"],
      [data-testid="stDecoration"], [data-testid="stStatusWidget"],
      [data-testid="stAppDeployButton"] { display: none !important; }
      button[kind="headerNoPadding"], [data-testid="StyledFullScreenButton"],
      button[title="Fullscreen"], button[aria-label="Fullscreen"] {
        display: none !important;
      }
      section[data-testid="stSidebar"],
      div[data-testid="stSidebar"],
      [data-testid="stSidebarContent"] {
        background: linear-gradient(180deg, #3a2718 0%, #24170f 100%) !important;
      }
      section[data-testid="stSidebar"] p,
      section[data-testid="stSidebar"] span,
      section[data-testid="stSidebar"] label,
      section[data-testid="stSidebar"] small {
        color: #f6f0e6 !important;
      }

      .eyebrow { letter-spacing: 0.18em; text-transform: uppercase; font-size: 0.72rem; color: #8a6a45; }
      .hero { padding: 0.1rem 0 0.35rem; }
      .hero p { color: #6d573f; margin-top: 0.15rem; }
      .muted { color: #7a654d; }
      .stat {
        background: #fffaf3; border: 1px solid #e4d3b8; border-radius: 18px;
        padding: 0.85rem 1rem;
      }
      .stat b { font-family: "Fraunces", serif; font-size: 1.4rem; display: block; }

      .score-bar {
        display: flex; flex-wrap: wrap; gap: 0.55rem; margin: 0.6rem 0 0.9rem;
      }
      .score-chip {
        background: #fffaf3; border: 1px solid #e4d3b8; border-radius: 999px;
        padding: 0.45rem 0.85rem; font-size: 0.92rem; color: #3a2718;
      }
      .score-chip strong { font-family: "Fraunces", serif; }

      .now-card {
        background: #fffaf3; border: 1px solid #e4d3b8; border-radius: 22px;
        padding: 0.85rem 1rem 1rem; margin-bottom: 0.75rem;
      }
      .pulled {
        background: #fffaf3; border: 1px solid #e4d3b8; border-radius: 22px;
        padding: 0.55rem 0.35rem 0.25rem; margin-bottom: 0.85rem;
      }
      .section-head { margin: 1rem 0 0.3rem; }
      .section-head h2 { margin: 0; font-size: 1.45rem; }
      .empty-shelf {
        background: rgba(255,250,243,0.55); border: 1px dashed #d7c3a4;
        border-radius: 16px; padding: 0.9rem 1rem; color: #7a654d; margin-bottom: 0.6rem;
      }
      .shelf-plank {
        height: 11px; margin: -0.35rem 0 1rem;
        border-radius: 2px 2px 6px 6px;
        background: linear-gradient(180deg, #c79255 0%, #8b5a2b 42%, #5c3a1e 100%);
        box-shadow: 0 8px 14px rgba(58, 39, 24, 0.18);
      }
      .spine-fallback {
        aspect-ratio: 3 / 4; display: flex; align-items: flex-end; justify-content: center;
        text-align: center; padding: 0.8rem; border-radius: 3px 8px 8px 3px;
        background: linear-gradient(180deg, #7b2e2e, #4d1c1c); color: #f6e7c8;
        font-family: "Fraunces", serif; font-size: 0.92rem;
        box-shadow: 4px 8px 18px rgba(58, 39, 24, 0.28);
      }
      .rec-card {
        background: #fffaf3; border: 1px solid #e4d3b8; border-radius: 16px;
        padding: 0.75rem 0.85rem; margin-bottom: 0.45rem;
      }
      .plan-day {
        background: #fffaf3; border: 1px solid #e4d3b8; border-radius: 14px;
        padding: 0.7rem 0.9rem; margin-bottom: 0.45rem;
      }

      [data-testid="stImage"] img,
      a.cover-link img {
        border-radius: 3px 9px 9px 3px;
        box-shadow: 5px 10px 22px rgba(58, 39, 24, 0.28);
        object-fit: cover; aspect-ratio: 3 / 4; width: 100%; background: #d7c3a4;
        display: block;
      }
      a.cover-link {
        display: block; text-decoration: none; line-height: 0;
        transition: transform 0.15s ease, filter 0.15s ease;
      }
      a.cover-link:hover { transform: translateY(-3px); filter: brightness(1.03); }
      a.cover-link:active { transform: translateY(0); }

      @media (max-width: 900px) {
        .block-container { padding-left: 0.85rem; padding-right: 0.85rem; }
        .stApp div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.35rem !important; }
        .stApp div[data-testid="stHorizontalBlock"] > div {
          min-width: calc(33.33% - 0.35rem) !important;
          flex: 1 1 calc(33.33% - 0.35rem) !important;
        }
      }
      @media (max-width: 520px) {
        .stApp div[data-testid="stHorizontalBlock"] > div {
          min-width: calc(50% - 0.3rem) !important;
          flex: 1 1 calc(50% - 0.3rem) !important;
        }
        h1 { font-size: 1.75rem !important; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

SHELF_COLS = 6
STATUS_LABELS = {"unread": "Want to read", "reading": "Currently reading", "done": "Finished"}


def persist(library: dict) -> None:
    save_library(library)
    st.rerun()


@st.cache_data(show_spinner=False)
def thumb_bytes(path: str, width: int = 260) -> bytes:
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        width = max(int(width), 80)
        w, h = img.size
        if w > width:
            img = img.resize((width, max(1, int(h * width / w))), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=72, optimize=True)
        return buf.getvalue()


def short_title(title: str, limit: int = 32) -> str:
    text = (title or "Untitled").strip() or "Untitled"
    return text if len(text) <= limit else text[: limit - 1] + "…"


def cover_path(book: dict) -> Path | None:
    raw = book.get("cover_path") or ""
    path = Path(raw) if raw else None
    return path if path and path.is_file() else None


def show_cover(book: dict, width: int = 260) -> None:
    path = cover_path(book)
    if path:
        st.image(thumb_bytes(str(path), width), width="stretch")
    else:
        st.markdown(
            f'<div class="spine-fallback">{html.escape(short_title(book.get("title") or "Untitled", 40))}</div>',
            unsafe_allow_html=True,
        )


def book_by_id(books: list[dict], book_id: str | None) -> dict | None:
    if not book_id:
        return None
    return next((book for book in books if book.get("id") == book_id), None)


def todays_assignment(books: list[dict], settings: dict) -> tuple[dict | None, dict | None, dict | None]:
    schedule = build_schedule(books, settings)
    today = date.today().isoformat()
    day = next((entry for entry in schedule if entry["date"] == today), None)
    if day and not day.get("rest") and day.get("assignments"):
        assignment = day["assignments"][0]
        return book_by_id(books, assignment.get("book_id")), assignment, day
    queue = active_books(books)
    return (queue[0], None, day) if queue else (None, None, day)


def render_cover_tile(book: dict, key_prefix: str, width: int = 240) -> None:
    """Cover image only — tapping the cover opens the book via query param."""
    del key_prefix  # kept for call-site compatibility
    path = cover_path(book)
    title = html.escape(book.get("title") or "Untitled")
    if path:
        b64 = base64.b64encode(thumb_bytes(str(path), width)).decode("ascii")
        st.markdown(
            f'<a class="cover-link" href="?open={book["id"]}" title="{title}">'
            f'<img src="data:image/jpeg;base64,{b64}" alt="{title}" /></a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<a class="cover-link" href="?open={book["id"]}" title="{title}">'
            f'<div class="spine-fallback">{title}</div></a>',
            unsafe_allow_html=True,
        )


def render_shelf(books: list[dict], key_prefix: str) -> None:
    if not books:
        return
    for row_start in range(0, len(books), SHELF_COLS):
        row = books[row_start : row_start + SHELF_COLS]
        cols = st.columns(SHELF_COLS, gap="small")
        for index, book in enumerate(row):
            with cols[index]:
                render_cover_tile(book, key_prefix)
        st.markdown('<div class="shelf-plank"></div>', unsafe_allow_html=True)


def section_header(eyebrow: str, title: str, count: int | None = None) -> None:
    count_html = (
        f" <span class='muted' style='font-size:1rem'>({count})</span>" if count is not None else ""
    )
    st.markdown(
        f'<div class="section-head"><div class="eyebrow">{html.escape(eyebrow)}</div>'
        f"<h2>{html.escape(title)}{count_html}</h2></div>",
        unsafe_allow_html=True,
    )


def log_pages(library: dict, book: dict, pages: int, *, note: str = "") -> None:
    result = append_progress(library, book, pages, note=note)
    if result["celebration"]:
        st.session_state.celebrate_id = book["id"]
        st.balloons()
    persist(library)


def render_page_logger(library: dict, book: dict, key_prefix: str) -> None:
    st.caption("Log pages read")
    q10, q25, q50, custom_col = st.columns(4)
    if q10.button("+10", key=f"{key_prefix}-q10-{book['id']}", width="stretch"):
        log_pages(library, book, 10)
    if q25.button("+25", key=f"{key_prefix}-q25-{book['id']}", width="stretch"):
        log_pages(library, book, 25)
    if q50.button("+50", key=f"{key_prefix}-q50-{book['id']}", width="stretch"):
        log_pages(library, book, 50)
    custom = custom_col.number_input(
        "Custom",
        min_value=1,
        max_value=max(int(book.get("pages") or 500), 1),
        value=min(20, max(int(book.get("pages") or 20), 1)),
        key=f"{key_prefix}-custom-{book['id']}",
        label_visibility="collapsed",
    )
    if st.button("Log pages", key=f"{key_prefix}-log-{book['id']}", width="stretch"):
        log_pages(library, book, int(custom))


def render_currently_reading(library: dict, reading: list[dict], settings: dict) -> None:
    section_header("In progress", "Currently reading", len(reading))
    if not reading:
        st.markdown(
            '<div class="empty-shelf">Nothing open yet — pick a cover below and tap Start reading.</div>',
            unsafe_allow_html=True,
        )
        return

    for book in reading:
        pages = int(book.get("pages") or 0)
        read = int(book.get("pages_read") or 0)
        left = remaining_pages(book)
        pct = int(round((read / pages) * 100)) if pages else 0
        days = days_until_book_finish(book, settings)
        days_txt = "done" if days == 0 else (f"~{days} day{'s' if days != 1 else ''} left" if days else "—")

        st.markdown('<div class="now-card">', unsafe_allow_html=True)
        cover_col, copy_col = st.columns([0.85, 2.4], gap="medium")
        with cover_col:
            show_cover(book, 220)
        with copy_col:
            st.subheader(book.get("title") or "Untitled")
            st.caption(
                f"{book.get('author') or 'Unknown author'}"
                + (f" · {book.get('category')}" if book.get("category") else "")
            )
            st.write(f"**{read} / {pages}** pages · {pct}% · {days_txt}")
            if pages:
                st.progress(min(read / pages, 1.0))
            if left:
                st.caption(f"{left} pages remaining · {length_label(pages)}")
            render_page_logger(library, book, f"now-{book['id']}")
            actions = st.columns(3)
            if actions[0].button("Open details", key=f"now-open-{book['id']}", width="stretch"):
                st.session_state.open_book_id = book["id"]
                st.rerun()
            if actions[1].button("Mark finished", key=f"now-done-{book['id']}", width="stretch"):
                if pages:
                    book["pages_read"] = pages
                book["status"] = "done"
                st.session_state.celebrate_id = book["id"]
                st.balloons()
                persist(library)
            if actions[2].button("Pause", key=f"now-pause-{book['id']}", width="stretch"):
                book["status"] = "unread"
                persist(library)
        st.markdown("</div>", unsafe_allow_html=True)


def render_pulled_book(book: dict, library: dict, settings: dict) -> None:
    st.markdown('<div class="pulled">', unsafe_allow_html=True)
    top = st.columns([8, 1])
    top[0].markdown('<div class="eyebrow">Pulled from the shelf</div>', unsafe_allow_html=True)
    if top[1].button("Close", key="close-pulled"):
        st.session_state.open_book_id = None
        st.rerun()

    visual, details = st.columns([1, 1.7], gap="large")
    with visual:
        show_cover(book, 420)
    with details:
        st.subheader(book.get("title") or "Untitled")
        st.caption(book.get("author") or "Unknown author")
        if book.get("category"):
            st.caption(book["category"])
        left = remaining_pages(book)
        pages = int(book.get("pages") or 0)
        read = int(book.get("pages_read") or 0)
        status = book.get("status") or "unread"
        days = days_until_book_finish(book, settings)
        days_txt = ""
        if status == "reading" and days is not None:
            days_txt = f" · ~{days} days to finish"
        st.write(
            f"{STATUS_LABELS.get(status, status)} · {read} / {pages} pages · {left} left{days_txt}"
        )
        if pages:
            st.progress(min(read / pages, 1.0))
        if book.get("notes"):
            st.markdown(f"<p class='muted'>{html.escape(book['notes'])}</p>", unsafe_allow_html=True)

        render_page_logger(library, book, f"pull-{book['id']}")

        actions = st.columns(3)
        if actions[0].button("Start reading", width="stretch", disabled=status == "reading", key=f"pull-start-{book['id']}"):
            book["status"] = "reading"
            persist(library)
        if actions[1].button("Mark finished", width="stretch", disabled=status == "done", key=f"pull-done-{book['id']}"):
            book["status"] = "done"
            if pages:
                book["pages_read"] = pages
            st.session_state.celebrate_id = book["id"]
            st.balloons()
            persist(library)
        if actions[2].button("Want to read", width="stretch", disabled=status == "unread", key=f"pull-want-{book['id']}"):
            book["status"] = "unread"
            persist(library)

        with st.expander("Edit details", expanded=False):
            new_title = st.text_input("Title", value=book.get("title", ""), key=f"title-{book['id']}")
            new_author = st.text_input("Author", value=book.get("author", ""), key=f"author-{book['id']}")
            new_pages = st.number_input("Pages", min_value=0, value=pages, key=f"pages-{book['id']}")
            new_read = st.number_input(
                "Pages read",
                min_value=0,
                max_value=max(int(new_pages or 0), read),
                value=read,
                key=f"read-{book['id']}",
            )
            new_priority = st.slider("Priority", 1, 5, int(book.get("priority") or 3), key=f"pri-{book['id']}")
            cat_val = book.get("category") or "Other"
            if cat_val not in CATEGORIES:
                cat_val = "Other"
            new_category = st.selectbox(
                "Category",
                CATEGORIES,
                index=CATEGORIES.index(cat_val),
                key=f"cat-{book['id']}",
            )
            new_notes = st.text_area("Notes", value=book.get("notes") or "", key=f"notes-{book['id']}")
            save_col, drop_col = st.columns(2)
            if save_col.button("Save changes", key=f"save-{book['id']}", width="stretch"):
                book["title"] = new_title
                book["author"] = new_author
                book["pages"] = int(new_pages)
                book["pages_read"] = int(new_read)
                book["priority"] = int(new_priority)
                book["category"] = new_category
                book["notes"] = new_notes
                if book["pages"] and book["pages_read"] >= book["pages"]:
                    book["status"] = "done"
                elif book["pages_read"] > 0 and book.get("status") == "unread":
                    book["status"] = "reading"
                persist(library)
            if drop_col.button("Remove from shelf", key=f"del-{book['id']}", width="stretch"):
                library["books"] = [item for item in library["books"] if item["id"] != book["id"]]
                st.session_state.open_book_id = None
                persist(library)
    st.markdown("</div>", unsafe_allow_html=True)


def render_score_widget(stats: dict) -> None:
    streak = stats["streak"]
    streak_label = f"{streak}-day streak" if streak else "No streak yet"
    st.markdown(
        f"""
        <div class="score-bar">
          <div class="score-chip"><strong>Score {stats['score']}</strong></div>
          <div class="score-chip">🔥 {html.escape(streak_label)}</div>
          <div class="score-chip">This week <strong>{stats['pages_week']}</strong> pages</div>
          <div class="score-chip">Finished <strong>{stats['finished']}</strong></div>
          <div class="score-chip">Avg <strong>{stats['avg_pages_day']}</strong> pages/day</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendations(library: dict, books: list[dict], reading: list[dict]) -> None:
    prefer = reading[0].get("category") if reading else None
    picks = recommend_books(books, limit=3, prefer_category=prefer)
    section_header("For you", "What to read next")
    if not picks:
        st.caption("Your want-to-read shelf is empty.")
        return

    top = st.columns([2, 1])
    with top[1]:
        if st.button("Surprise me / Spin the shelf", width="stretch", key="surprise"):
            pick = surprise_pick(books)
            if pick:
                st.session_state.open_book_id = pick["id"]
                st.session_state.surprise_title = pick.get("title")
                st.rerun()
    if st.session_state.get("surprise_title"):
        st.success(f"Shelf spun → **{st.session_state.surprise_title}**")
        st.session_state.surprise_title = None

    for book in picks:
        pages = int(book.get("pages") or 0)
        st.markdown(
            f'<div class="rec-card"><strong>{html.escape(book.get("title") or "Untitled")}</strong><br>'
            f'<span class="muted">{html.escape(book.get("author") or "")} · '
            f'{html.escape(book.get("category") or "Other")} · {length_label(pages)}'
            f' ({pages or "?"} pages) · Priority {int(book.get("priority") or 0)}</span></div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        if c1.button("Open", key=f"rec-open-{book['id']}", width="stretch"):
            st.session_state.open_book_id = book["id"]
            st.rerun()
        if c2.button("Start reading", key=f"rec-start-{book['id']}", width="stretch"):
            book["status"] = "reading"
            st.session_state.open_book_id = book["id"]
            persist(library)


# ---------------------------------------------------------------------------
# App body
# ---------------------------------------------------------------------------

library = load_library()
books = library.setdefault("books", [])
settings = library.setdefault("settings", {})
log = library.setdefault("progress_log", [])

# Only shelves with real cover image files
books = [book for book in books if cover_path(book)]

st.session_state.setdefault("open_book_id", None)
st.session_state.setdefault("celebrate_id", None)
st.session_state.setdefault("page", "Library")

# Cover tap → open pulled sheet
open_from_url = st.query_params.get("open")
if open_from_url:
    st.session_state.open_book_id = open_from_url
    st.session_state.page = "Library"
    try:
        del st.query_params["open"]
    except Exception:
        st.query_params.clear()
    st.rerun()

want = [book for book in books if (book.get("status") or "unread") == "unread"]
reading = [book for book in books if book.get("status") == "reading"]
finished = [book for book in books if book.get("status") == "done"]
want = sorted(want, key=lambda book: (-int(book.get("priority") or 0), book.get("title") or ""))
reading = sorted(reading, key=lambda book: (-int(book.get("priority") or 0), book.get("title") or ""))
stats = reading_score(books, log, settings)
pick, assignment, _today_day = todays_assignment(books, settings)

with st.sidebar:
    st.markdown("### Shelf Plan")
    st.radio("Go to", ["Library", "Planner", "Today", "Analytics"], key="page", label_visibility="collapsed")
    page = st.session_state.page
    st.caption("Cover-first shelf · track pages · build your streak.")
    st.markdown(
        f"<p class='muted'>{len(books)} on the shelf<br>{len(want)} want to read<br>"
        f"{len(reading)} currently reading<br>{len(finished)} finished<br>"
        f"Score {stats['score']} · 🔥 {stats['streak']}-day streak</p>",
        unsafe_allow_html=True,
    )

if page == "Library":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Personal library</div><h1>Your shelf</h1>'
        f"<p>{len(books)} covers on the shelf. Tap a cover to pull it down.</p></div>",
        unsafe_allow_html=True,
    )
    render_score_widget(stats)

    counts = st.columns(3)
    counts[0].markdown(
        f'<div class="stat"><span class="muted">Want to read</span><b>{len(want)}</b></div>',
        unsafe_allow_html=True,
    )
    counts[1].markdown(
        f'<div class="stat"><span class="muted">Currently reading</span><b>{len(reading)}</b></div>',
        unsafe_allow_html=True,
    )
    counts[2].markdown(
        f'<div class="stat"><span class="muted">Finished</span><b>{len(finished)}</b></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.celebrate_id:
        celeb = book_by_id(books, st.session_state.celebrate_id)
        if celeb:
            st.success(f"Finished **{celeb.get('title') or 'Untitled'}** — nice work!")
        st.session_state.celebrate_id = None

    pulled = book_by_id(books, st.session_state.open_book_id)
    if pulled:
        st.write("")
        render_pulled_book(pulled, library, settings)

    render_currently_reading(library, reading, settings)
    render_recommendations(library, books, reading)

    if reading:
        section_header("Open now", "On the reading shelf", len(reading))
        render_shelf(reading, "reading")

    section_header("The stack", "Want to read", len(want))
    if want:
        render_shelf(want, "want")
    else:
        st.markdown('<div class="empty-shelf">The want-to-read shelf is empty.</div>', unsafe_allow_html=True)

    if finished:
        section_header("Already read", "Finished", len(finished))
        render_shelf(finished, "done")
    else:
        st.caption("Finished books will line up on their own shelf.")

    with st.expander("Add a book to the shelf"):
        with st.form("add_book", clear_on_submit=True):
            cols = st.columns([1.4, 1.2, 0.6, 0.5])
            title = cols[0].text_input("Title")
            author = cols[1].text_input("Author")
            pages = cols[2].number_input("Pages", min_value=0, step=1, value=0)
            priority = cols[3].slider("Priority", 1, 5, 3)
            category = st.selectbox("Category / Genre", CATEGORIES, index=CATEGORIES.index("Other"))
            notes = st.text_area("Notes", placeholder="Edition, why you want to read it, where it sits…")
            photo = st.file_uploader("Cover photo", type=["jpg", "jpeg", "png", "webp"])
            submitted = st.form_submit_button("Add to shelf", width="stretch")
        if submitted:
            cover = ""
            source_image = ""
            if photo is not None:
                dest = UPLOADS / "covers" / f"{date.today().isoformat()}-{photo.name}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                image = ImageOps.exif_transpose(Image.open(io.BytesIO(photo.getvalue()))).convert("RGB")
                image.thumbnail((600, 900), Image.Resampling.LANCZOS)
                image.save(dest, "JPEG", quality=92)
                cover = str(dest)
                source_image = photo.name
            if not cover:
                st.error("Add a cover photo so it can sit on the shelf.")
            else:
                books.append(
                    new_book(
                        title=title or (Path(source_image).stem if source_image else "Unidentified book"),
                        author=author,
                        pages=int(pages),
                        cover_path=cover,
                        notes=notes,
                        priority=int(priority),
                        source_image=source_image,
                        category=category,
                    )
                )
                library["books"] = books
                persist(library)

elif page == "Planner":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Cadence</div><h1>Reading planner</h1>'
        "<p>Turn the shelf into a daily stack without living in a spreadsheet.</p></div>",
        unsafe_allow_html=True,
    )
    render_score_widget(stats)
    c1, c2, c3 = st.columns(3)
    settings["pages_per_hour"] = c1.number_input(
        "Pages per hour", min_value=5, max_value=120, value=int(settings.get("pages_per_hour") or 30)
    )
    settings["minutes_per_day"] = c2.number_input(
        "Minutes per day", min_value=5, max_value=240, value=int(settings.get("minutes_per_day") or 45)
    )
    settings["mode"] = c3.selectbox(
        "Mode",
        ["sequential", "parallel"],
        index=0 if (settings.get("mode") or "sequential") == "sequential" else 1,
    )
    settings["start_date"] = st.date_input(
        "Plan start",
        value=date.fromisoformat(settings.get("start_date") or date.today().isoformat()),
    ).isoformat()
    rest = st.multiselect(
        "Rest weekdays",
        options=list(range(7)),
        default=[int(x) for x in (settings.get("rest_weekdays") or [])],
        format_func=lambda i: WEEKDAY_NAMES[i],
    )
    settings["rest_weekdays"] = rest
    if st.button("Save plan settings", width="stretch"):
        persist(library)

    schedule = build_schedule(books, settings)
    finish = estimated_finish(schedule)
    budget = daily_page_budget(settings)
    st.write(f"Daily budget **{budget} pages**. " + (f"Whole shelf finishes around **{finish}**." if finish else ""))
    for day in schedule[:21]:
        if day.get("rest"):
            st.markdown(
                f'<div class="plan-day"><strong>{day["date"]}</strong> · rest day</div>',
                unsafe_allow_html=True,
            )
        else:
            bits = ", ".join(f'{a["title"]} ({a["pages"]}p)' for a in day.get("assignments") or [])
            st.markdown(
                f'<div class="plan-day"><strong>{day["date"]}</strong> · {day["pages"]} pages'
                f'<br><span class="muted">{html.escape(bits)}</span></div>',
                unsafe_allow_html=True,
            )

elif page == "Today":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Today</div><h1>Read something</h1>'
        "<p>Log pages, keep the streak, finish books.</p></div>",
        unsafe_allow_html=True,
    )
    render_score_widget(stats)
    if pick:
        show_cover(pick, 320)
        st.subheader(pick.get("title") or "Untitled")
        st.caption(pick.get("author") or "")
        if assignment:
            st.write(f"Planned for today: **{assignment['pages']} pages**.")
        render_page_logger(library, pick, "today")
        if st.button("Start reading", key="today-start", width="stretch"):
            pick["status"] = "reading"
            st.session_state.open_book_id = pick["id"]
            persist(library)
    else:
        st.info("No active books. Add covers on the Library page.")

    st.subheader("Recent log")
    recent = list(reversed(log[-12:]))
    if not recent:
        st.caption("No pages logged yet — use +10 / +25 on a book.")
    for entry in recent:
        st.write(f"{entry.get('at', '')[:16]} · **{entry.get('pages')}** pages · {entry.get('title')}")

elif page == "Analytics":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Insights</div><h1>Analytics</h1>'
        "<p>Genre mix, velocity, length, and finish projections for your shelf.</p></div>",
        unsafe_allow_html=True,
    )
    render_score_widget(stats)

    total_pages = sum(int(b.get("pages") or 0) for b in books)
    pages_read = sum(int(b.get("pages_read") or 0) for b in books)
    kpi = st.columns(4)
    kpi[0].markdown(
        f'<div class="stat"><span class="muted">Titles</span><b>{len(books)}</b></div>',
        unsafe_allow_html=True,
    )
    kpi[1].markdown(
        f'<div class="stat"><span class="muted">Shelf pages</span><b>{total_pages:,}</b></div>',
        unsafe_allow_html=True,
    )
    kpi[2].markdown(
        f'<div class="stat"><span class="muted">Pages read</span><b>{pages_read:,}</b></div>',
        unsafe_allow_html=True,
    )
    kpi[3].markdown(
        f'<div class="stat"><span class="muted">Log entries</span><b>{len(log)}</b></div>',
        unsafe_allow_html=True,
    )

    st.write("")
    section_header("Composition", "Genre & status")
    genre_mode = st.radio(
        "Genre chart measures",
        ["By book count", "By total pages"],
        horizontal=True,
        label_visibility="collapsed",
        key="genre-mode",
    )
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.plotly_chart(
            category_donut(books, by_pages=(genre_mode == "By total pages")),
            width="stretch",
            config={"displayModeBar": False},
        )
    with c2:
        st.plotly_chart(status_donut(books), width="stretch", config={"displayModeBar": False})

    section_header("Pace", "Activity & weekly trend")
    lookback = st.slider("Activity window (days)", 7, 60, 30, key="activity-days")
    st.plotly_chart(
        activity_charts(log, days=int(lookback)),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.plotly_chart(weekly_trend(log, weeks=8), width="stretch", config={"displayModeBar": False})

    section_header("Shelf shape", "Length & priority")
    st.plotly_chart(length_distribution(books), width="stretch", config={"displayModeBar": False})
    p1, p2 = st.columns([1.2, 1], gap="large")
    with p1:
        st.plotly_chart(
            completion_projections(books, settings, log),
            width="stretch",
            config={"displayModeBar": False},
        )
    with p2:
        st.plotly_chart(priority_bars(books), width="stretch", config={"displayModeBar": False})
        st.caption("Terracotta bars = currently reading · amber = want to read.")

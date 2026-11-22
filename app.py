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
from crypto_covers import read_cover_bytes, try_unlock, write_encrypted_cover
from shelf_store import (
    CATEGORIES,
    UPLOADS,
    append_progress,
    load_library,
    new_book,
    resolve_path,
    save_library,
    stored_path,
)

st.set_page_config(page_title="Shelf Plan · Windows Phone Metro", page_icon="📱", layout="wide")

# ---------------------------------------------------------------------------
# Windows Phone Metro Design System CSS (Square Blocks & Live Tiles)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      @import url("https://fonts.googleapis.com/css2?family=Segoe+UI:wght@200;300;400;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap");

      html, body, [class*="css"] {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif !important;
      }
      .stApp {
        background-color: #0d0f12 !important;
        color: #c9d1d9 !important;
      }
      .block-container {
        padding-top: 1.0rem;
        padding-bottom: 3.5rem;
        max-width: 1240px;
      }

      /* Metro Typography Hierarchy */
      h1, h2, h3, h4 {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 200 !important;
        color: #ffffff !important;
        letter-spacing: -0.035em !important;
      }
      h1 { font-size: 2.8rem !important; line-height: 1.1 !important; }
      h2 { font-size: 1.75rem !important; line-height: 1.15 !important; }
      h3 { font-size: 1.35rem !important; }

      /* Eliminate default Streamlit Chrome */
      header[data-testid="stHeader"] { background: transparent !important; }
      #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"],
      [data-testid="stDecoration"], [data-testid="stStatusWidget"],
      [data-testid="stAppDeployButton"] { display: none !important; }
      button[kind="headerNoPadding"], [data-testid="StyledFullScreenButton"],
      button[title="Fullscreen"], button[aria-label="Fullscreen"] {
        display: none !important;
      }

      /* Windows Phone Sidebar / Pivot Menu */
      section[data-testid="stSidebar"],
      div[data-testid="stSidebar"],
      [data-testid="stSidebarContent"] {
        background-color: #14181d !important;
        border-right: 1px solid #22272e !important;
      }
      section[data-testid="stSidebar"] p,
      section[data-testid="stSidebar"] span,
      section[data-testid="stSidebar"] label,
      section[data-testid="stSidebar"] small {
        color: #c9d1d9 !important;
      }

      /* Windows Phone Start Screen Panorama Header */
      .metro-panorama {
        padding: 0.2rem 0 1.0rem 0;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid #22272e;
      }
      .metro-kicker {
        font-family: 'JetBrains Mono', 'Consolas', monospace !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.18em !important;
        text-transform: uppercase !important;
        color: #0078d4 !important;
        font-weight: 600 !important;
        margin-bottom: 0.25rem;
      }
      .metro-panorama-title {
        font-family: 'Segoe UI', -apple-system, sans-serif !important;
        font-weight: 200 !important;
        font-size: 3.2rem !important;
        letter-spacing: -0.04em !important;
        color: #ffffff !important;
        line-height: 1.05 !important;
        margin: 0 !important;
      }
      .metro-pivot {
        color: #57606a !important;
        font-weight: 200 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.02em !important;
        margin-left: 0.4rem;
      }
      .metro-subhead {
        color: #8b949e !important;
        font-size: 0.95rem !important;
        margin-top: 0.3rem !important;
      }

      /* Windows Phone Square Block Live Tiles */
      .metro-tile-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 10px;
        margin: 0.8rem 0 1.4rem 0;
      }
      .metro-tile {
        position: relative;
        aspect-ratio: 1 / 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 1.0rem;
        box-sizing: border-box;
        text-decoration: none !important;
        border-radius: 0px !important;
        box-shadow: none !important;
        transition: transform 0.12s ease, filter 0.12s ease, border-color 0.12s ease;
        user-select: none;
        overflow: hidden;
      }
      .metro-tile:hover {
        filter: brightness(1.12);
        transform: translateY(-2px);
      }
      .metro-tile:active {
        transform: scale(0.97);
      }

      /* Windows Phone Flat Accent Colors */
      .metro-cobalt { background-color: #0078d4 !important; color: #ffffff !important; }
      .metro-mango { background-color: #f09609 !important; color: #ffffff !important; }
      .metro-emerald { background-color: #107c41 !important; color: #ffffff !important; }
      .metro-cyan { background-color: #00a4ef !important; color: #ffffff !important; }
      .metro-magenta { background-color: #d80073 !important; color: #ffffff !important; }
      .metro-crimson { background-color: #e81123 !important; color: #ffffff !important; }
      .metro-purple { background-color: #6a00ff !important; color: #ffffff !important; }
      .metro-teal { background-color: #00aba9 !important; color: #ffffff !important; }
      .metro-slate {
        background-color: #14181d !important;
        color: #ffffff !important;
        border: 1px solid #22272e !important;
      }

      /* Inside Live Tile Elements */
      .tile-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
      }
      .tile-kicker {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        opacity: 0.85;
      }
      .tile-badge {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        padding: 2px 6px;
        background: rgba(0, 0, 0, 0.35);
        color: #ffffff;
      }
      .tile-huge {
        font-family: 'Segoe UI', -apple-system, sans-serif !important;
        font-weight: 200 !important;
        font-size: 2.8rem !important;
        line-height: 1.0 !important;
        letter-spacing: -0.04em !important;
        color: #ffffff !important;
        margin: auto 0 0 0;
      }
      .tile-huge-sub {
        font-size: 1.1rem !important;
        font-weight: 300 !important;
        opacity: 0.85;
        margin-left: 2px;
      }
      .tile-label {
        font-family: 'JetBrains Mono', 'Segoe UI', monospace !important;
        font-size: 0.70rem !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        font-weight: 600 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        margin-top: 0.35rem;
      }

      /* Windows Phone Square Book Tile */
      .metro-book-tile {
        position: relative;
        aspect-ratio: 1 / 1;
        background: #14181d;
        border: 2px solid #22272e;
        border-radius: 0px !important;
        box-shadow: none !important;
        overflow: hidden;
        display: block;
        text-decoration: none !important;
        transition: transform 0.12s ease, border-color 0.12s ease, filter 0.12s ease;
      }
      .metro-book-tile.portrait {
        aspect-ratio: 3 / 4 !important;
      }
      .metro-book-tile:hover {
        border-color: #0078d4 !important;
        filter: brightness(1.08);
        transform: translateY(-2px);
      }
      .metro-book-tile:active {
        transform: scale(0.97);
      }
      .metro-book-tile img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        display: block !important;
        border-radius: 0px !important;
        border: none !important;
      }
      .metro-book-overlay {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(180deg, rgba(13,15,18,0) 0%, rgba(13,15,18,0.82) 32%, rgba(13,15,18,0.98) 100%);
        padding: 1.3rem 0.65rem 0.45rem;
        box-sizing: border-box;
      }
      .metro-book-title {
        font-family: 'Segoe UI', -apple-system, sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2 !important;
      }
      .metro-book-meta {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.65rem !important;
        color: #8b949e !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 2px;
        letter-spacing: 0.02em;
      }
      .metro-book-indicator {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
      }
      .metro-book-indicator.unread { background-color: #0078d4; }
      .metro-book-indicator.reading { background-color: #f09609; }
      .metro-book-indicator.done { background-color: #107c41; }

      .metro-book-badge {
        position: absolute;
        top: 6px;
        right: 6px;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        padding: 2px 6px;
        background: rgba(13, 15, 18, 0.88);
        border: 1px solid #22272e;
        color: #ffffff;
      }
      .metro-book-badge.reading { border-color: #f09609; color: #f09609; }
      .metro-book-badge.done { border-color: #107c41; color: #107c41; }
      .metro-book-badge.unread { border-color: #0078d4; color: #0078d4; }

      /* Fallback Square Spine Tile */
      .metro-spine-tile {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 0.85rem;
        box-sizing: border-box;
        background: #14181d;
        border: 1px solid #22272e;
        text-align: left;
      }
      .metro-spine-cat {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #0078d4;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 600;
      }
      .metro-spine-title {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 300;
        font-size: 0.95rem;
        color: #ffffff;
        line-height: 1.25;
        margin: auto 0;
      }
      .metro-spine-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #768390;
      }

      /* Metro Hairline Shelf Divider */
      .metro-shelf-divider {
        height: 1px !important;
        background: #22272e !important;
        margin: 1.1rem 0 1.5rem 0 !important;
        position: relative;
      }
      .metro-shelf-divider::before {
        content: "";
        position: absolute;
        left: 0;
        top: -1px;
        width: 48px;
        height: 3px;
        background: #0078d4;
      }

      /* Section Headers */
      .section-head { margin: 1.4rem 0 0.5rem; }
      .section-head h2 { margin: 0; font-size: 1.55rem; color: #ffffff !important; }

      /* Currently Reading & Detail Cards */
      .now-card {
        background: #14181d !important;
        border: 1px solid #22272e !important;
        border-radius: 0px !important;
        padding: 1.0rem 1.15rem 1.15rem;
        margin-bottom: 0.9rem;
        box-shadow: none !important;
      }
      .pulled {
        background: #14181d !important;
        border: 1px solid #22272e !important;
        border-radius: 0px !important;
        padding: 0.85rem 1.0rem 1.0rem;
        margin-bottom: 1.2rem;
        box-shadow: none !important;
      }
      .empty-shelf {
        background: #14181d !important;
        border: 1px dashed #22272e !important;
        border-radius: 0px !important;
        padding: 1.2rem 1.2rem;
        color: #768390 !important;
        margin-bottom: 0.8rem;
        font-size: 0.95rem;
      }
      .rec-card {
        background: #14181d !important;
        border: 1px solid #22272e !important;
        border-radius: 0px !important;
        padding: 0.85rem 1.0rem;
        margin-bottom: 0.45rem;
        box-shadow: none !important;
      }
      .plan-day {
        background: #14181d !important;
        border: 1px solid #22272e !important;
        border-radius: 0px !important;
        padding: 0.8rem 1.0rem;
        margin-bottom: 0.45rem;
        box-shadow: none !important;
      }

      /* Metro Flat Buttons */
      button, div[data-testid="stButton"] > button {
        background-color: #14181d !important;
        border: 1px solid #22272e !important;
        color: #ffffff !important;
        border-radius: 0px !important;
        font-family: 'Segoe UI', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        box-shadow: none !important;
        transition: all 0.12s ease !important;
      }
      button:hover, div[data-testid="stButton"] > button:hover {
        background-color: #0078d4 !important;
        border-color: #0078d4 !important;
        color: #ffffff !important;
      }
      button:active, div[data-testid="stButton"] > button:active {
        transform: scale(0.97) !important;
      }

      /* Windows Phone Lock Screen Unlock Card */
      .unlock-card {
        max-width: 500px;
        margin: 3.0rem auto 0;
        background: #14181d !important;
        border: 1px solid #22272e !important;
        border-radius: 0px !important;
        padding: 2.0rem 2.0rem 1.6rem;
        box-shadow: none !important;
      }
      .unlock-card h1 {
        margin: 0.2rem 0 0.5rem;
        color: #ffffff !important;
        font-size: 2.4rem !important;
      }
      .unlock-card p {
        color: #8b949e !important;
        margin: 0 0 0.6rem;
        font-size: 0.95rem;
      }

      /* Responsive Reflow */
      @media (max-width: 900px) {
        .block-container { padding-left: 0.85rem; padding-right: 0.85rem; }
        .stApp div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.35rem !important; }
        .stApp div[data-testid="stHorizontalBlock"] > div {
          min-width: calc(50% - 0.35rem) !important;
          flex: 1 1 calc(50% - 0.35rem) !important;
        }
      }
      @media (max-width: 520px) {
        .metro-panorama-title { font-size: 2.2rem !important; }
        .stApp div[data-testid="stHorizontalBlock"] > div {
          min-width: 100% !important;
          flex: 1 1 100% !important;
        }
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


def session_key() -> str:
    return str(st.session_state.get("fernet_key") or "")


def render_unlock_gate() -> None:
    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"],
          [data-testid="collapsedControl"] { display: none !important; }
        </style>
        <div class="unlock-card">
          <div class="metro-kicker">00 // LOCK SCREEN</div>
          <h1>unlock shelf</h1>
          <p>Covers stay encrypted until you enter your Fernet key. Decryption is performed in memory for this session only.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("unlock-shelf"):
        entered = st.text_input(
            "Fernet key",
            type="password",
            placeholder="Paste Fernet key to unlock square live tiles...",
        )
        submitted = st.form_submit_button("Unlock Live Tiles", width="stretch")
    if submitted:
        error = try_unlock(entered)
        if error:
            st.error(error)
        else:
            st.session_state.fernet_key = entered.strip()
            st.rerun()
    st.stop()


@st.cache_data(show_spinner=False)
def thumb_bytes(path: str, width: int = 280, key: str = "") -> bytes:
    raw = read_cover_bytes(Path(path), key)
    with Image.open(io.BytesIO(raw)) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        width = max(int(width), 80)
        w, h = img.size
        if w > width:
            img = img.resize((width, max(1, int(h * width / w))), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=78, optimize=True)
        return buf.getvalue()


def short_title(title: str, limit: int = 32) -> str:
    text = (title or "Untitled").strip() or "Untitled"
    return text if len(text) <= limit else text[: limit - 1] + "…"


def cover_path(book: dict) -> Path | None:
    return resolve_path(book.get("cover_path") or "")


def show_cover(book: dict, width: int = 280) -> None:
    path = cover_path(book)
    key = session_key()
    if path and key:
        st.image(thumb_bytes(str(path), width, key), width="stretch")
    else:
        title = html.escape(short_title(book.get("title") or "Untitled", 40))
        cat = html.escape(book.get("category") or "General")
        st.markdown(
            f'<div class="metro-spine-tile"><div class="metro-spine-cat">{cat}</div>'
            f'<div class="metro-spine-title">{title}</div></div>',
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


def render_cover_tile(book: dict, key_prefix: str, width: int = 280, portrait: bool = False) -> None:
    """Authentic Windows Phone Square Block Live Tile with image and bottom metadata overlay."""
    del key_prefix
    path = cover_path(book)
    title = html.escape(book.get("title") or "Untitled")
    author = html.escape(book.get("author") or "Unknown author")
    pages = int(book.get("pages") or 0)
    read = int(book.get("pages_read") or 0)
    status = book.get("status") or "unread"
    category = html.escape(book.get("category") or "Other")
    pages_txt = f"{read}/{pages}p" if (status == "reading" and pages) else (f"{pages}p" if pages else "")

    # Status badge for live tile
    badge_html = ""
    if status == "reading" and pages:
        pct = int(round((read / pages) * 100))
        badge_html = f'<div class="metro-book-badge reading">⚡ {pct}%</div>'
    elif status == "done":
        badge_html = '<div class="metro-book-badge done">✓ DONE</div>'
    elif int(book.get("priority") or 0) >= 4:
        badge_html = f'<div class="metro-book-badge unread">★ P{int(book.get("priority") or 0)}</div>'

    shape_class = "portrait" if portrait else "square"
    key = session_key()

    if path and key:
        b64 = base64.b64encode(thumb_bytes(str(path), width, key)).decode("ascii")
        st.markdown(
            f'<a class="metro-book-tile {shape_class}" href="?open={book["id"]}" title="{title}">'
            f'<img src="data:image/jpeg;base64,{b64}" alt="{title}" />'
            f'{badge_html}'
            f'<div class="metro-book-overlay">'
            f'  <div class="metro-book-title">{title}</div>'
            f'  <div class="metro-book-meta">{author}{" · " + pages_txt if pages_txt else ""}</div>'
            f'</div>'
            f'<div class="metro-book-indicator {status}"></div>'
            f'</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<a class="metro-book-tile {shape_class}" href="?open={book["id"]}" title="{title}">'
            f'<div class="metro-spine-tile">'
            f'  <div class="metro-spine-cat">{category}</div>'
            f'  <div class="metro-spine-title">{title}</div>'
            f'  <div class="metro-spine-meta">{author}{" · " + pages_txt if pages_txt else ""}</div>'
            f'  {badge_html}'
            f'  <div class="metro-book-indicator {status}"></div>'
            f'</div>'
            f'</a>',
            unsafe_allow_html=True,
        )


def render_shelf(books: list[dict], key_prefix: str, cols: int = 6, portrait: bool = False) -> None:
    if not books:
        return
    for row_start in range(0, len(books), cols):
        row = books[row_start : row_start + cols]
        columns = st.columns(cols, gap="small")
        for index, book in enumerate(row):
            with columns[index]:
                render_cover_tile(book, key_prefix, portrait=portrait)
        st.markdown('<div class="metro-shelf-divider"></div>', unsafe_allow_html=True)


def section_header(eyebrow: str, title: str, count: int | None = None) -> None:
    count_html = (
        f" <span class='metro-subhead' style='font-size:1.1rem;font-weight:300'>({count})</span>"
        if count is not None
        else ""
    )
    st.markdown(
        f'<div class="section-head"><div class="metro-kicker">{html.escape(eyebrow)}</div>'
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
    st.caption("LOG PAGES READ")
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
    if st.button("Log Pages", key=f"{key_prefix}-log-{book['id']}", width="stretch"):
        log_pages(library, book, int(custom))


def render_score_widget(stats: dict) -> None:
    """Windows Phone Start Screen Live Tile Row."""
    streak = stats["streak"]
    streak_label = f"{streak} DAYS" if streak else "0 DAYS"
    st.markdown(
        f"""
        <div class="metro-tile-row">
          <div class="metro-tile metro-cobalt">
            <div class="tile-top">
              <div class="tile-kicker">SCORE</div>
              <div class="tile-badge">XP</div>
            </div>
            <div class="tile-huge">{stats['score']}</div>
            <div class="tile-label">READING SCORE</div>
          </div>
          <div class="metro-tile metro-mango">
            <div class="tile-top">
              <div class="tile-kicker">STREAK</div>
              <div class="tile-badge">🔥 LIVE</div>
            </div>
            <div class="tile-huge">{streak}<span class="tile-huge-sub">D</span></div>
            <div class="tile-label">{streak_label}</div>
          </div>
          <div class="metro-tile metro-cyan">
            <div class="tile-top">
              <div class="tile-kicker">THIS WEEK</div>
              <div class="tile-badge">PAGES</div>
            </div>
            <div class="tile-huge">{stats['pages_week']}</div>
            <div class="tile-label">WEEKLY VELOCITY</div>
          </div>
          <div class="metro-tile metro-magenta">
            <div class="tile-top">
              <div class="tile-kicker">FINISHED</div>
              <div class="tile-badge">✓ BOOKS</div>
            </div>
            <div class="tile-huge">{stats['finished']}</div>
            <div class="tile-label">COMPLETED TITLES</div>
          </div>
          <div class="metro-tile metro-slate">
            <div class="tile-top">
              <div class="tile-kicker">DAILY PACE</div>
              <div class="tile-badge">AVG</div>
            </div>
            <div class="tile-huge">{stats['avg_pages_day']}<span class="tile-huge-sub">P/D</span></div>
            <div class="tile-label">AVERAGE CADENCE</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_currently_reading(library: dict, reading: list[dict], settings: dict) -> None:
    section_header("In Progress", "Currently reading", len(reading))
    if not reading:
        st.markdown(
            '<div class="empty-shelf">Nothing open right now. Pick a live tile below and tap <b>Start Reading</b>.</div>',
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
            show_cover(book, 260)
        with copy_col:
            st.subheader(book.get("title") or "Untitled")
            st.caption(
                f"{book.get('author') or 'Unknown author'}"
                + (f" · {book.get('category')}" if book.get("category") else "")
            )
            st.write(f"**{read} / {pages}** pages · **{pct}%** · {days_txt}")
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
            if actions[2].button("Pause reading", key=f"now-pause-{book['id']}", width="stretch"):
                book["status"] = "unread"
                persist(library)
        st.markdown("</div>", unsafe_allow_html=True)


def render_pulled_book(book: dict, library: dict, settings: dict) -> None:
    st.markdown('<div class="pulled">', unsafe_allow_html=True)
    top = st.columns([8, 1])
    top[0].markdown('<div class="metro-kicker">INSPECT // PULLED FROM SHELF</div>', unsafe_allow_html=True)
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
            f"**{STATUS_LABELS.get(status, status)}** · {read} / {pages} pages · {left} left{days_txt}"
        )
        if pages:
            st.progress(min(read / pages, 1.0))
        if book.get("notes"):
            st.markdown(f"<p class='metro-subhead'>{html.escape(book['notes'])}</p>", unsafe_allow_html=True)

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

        with st.expander("Edit book metadata", expanded=False):
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


def render_recommendations(library: dict, books: list[dict], reading: list[dict]) -> None:
    prefer = reading[0].get("category") if reading else None
    picks = recommend_books(books, limit=3, prefer_category=prefer)
    section_header("Editorial Recommendations", "What to read next")
    if not picks:
        st.caption("Your want-to-read shelf is empty.")
        return

    top = st.columns([2, 1])
    with top[1]:
        if st.button("🎲 Spin the Shelf / Random Pick", width="stretch", key="surprise"):
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
            f'<span class="metro-subhead">{html.escape(book.get("author") or "")} · '
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
# App state & credentials
# ---------------------------------------------------------------------------

st.session_state.setdefault("fernet_key", "")
if not session_key():
    render_unlock_gate()

library = load_library()
books = library.setdefault("books", [])
settings = library.setdefault("settings", {})
log = library.setdefault("progress_log", [])

# Only shelves with real cover image files
books = [book for book in books if cover_path(book)]

st.session_state.setdefault("open_book_id", None)
st.session_state.setdefault("celebrate_id", None)
st.session_state.setdefault("page", "Library")

# Cover tap → open pulled sheet via query param
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

# ---------------------------------------------------------------------------
# Windows Phone Sidebar Pivot
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1.0rem;">
          <div class="metro-kicker">WINDOWS PHONE METRO</div>
          <h2 style="margin: 0; font-size: 1.8rem; font-weight: 200;">books <span style="color:#57606a;">| hub</span></h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.radio("Pivot to", ["Library", "Planner", "Today", "Analytics"], key="page", label_visibility="collapsed")
    page = st.session_state.page

    st.markdown("---")
    tile_view = st.selectbox(
        "Live Tile Geometry",
        ["Square Blocks (1:1)", "Portrait Covers (3:4)"],
        index=0,
    )
    is_portrait = "Portrait" in tile_view

    shelf_cols_pref = st.slider("Tiles per row", min_value=3, max_value=8, value=6, step=1)

    st.markdown(
        f"""
        <div style="margin-top: 1.0rem;">
          <div class="metro-tile metro-slate" style="aspect-ratio: auto; padding: 0.85rem; margin-bottom: 0.5rem;">
            <div class="tile-kicker">SHELF OVERVIEW</div>
            <div style="font-size: 1.3rem; font-weight: 300; color: #ffffff; margin-top: 0.2rem;">
              {len(books)} <span style="font-size: 0.85rem; color: #8b949e;">TOTAL TITLES</span>
            </div>
            <div style="font-size: 0.82rem; color: #8b949e; margin-top: 0.3rem;">
              {len(reading)} reading · {len(want)} want · {len(finished)} done
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔒 Lock Shelf", width="stretch"):
        st.session_state.fernet_key = ""
        st.session_state.open_book_id = None
        st.rerun()

# ---------------------------------------------------------------------------
# View: Library
# ---------------------------------------------------------------------------

if page == "Library":
    st.markdown(
        f"""
        <div class="metro-panorama">
          <div class="metro-kicker">01 // START SCREEN</div>
          <h1 class="metro-panorama-title">books <span class="metro-pivot">shelf</span></h1>
          <div class="metro-subhead">{len(books)} square block live tiles. Tap any tile to inspect and log pages.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Live Tile Score Hub
    render_score_widget(stats)

    # Status Quick Filter Tiles
    st.markdown(
        f"""
        <div class="metro-tile-row" style="margin-top: 0.4rem;">
          <div class="metro-tile metro-mango">
            <div class="tile-top">
              <div class="tile-kicker">READING</div>
              <div class="tile-badge">ACTIVE</div>
            </div>
            <div class="tile-huge">{len(reading)}</div>
            <div class="tile-label">CURRENTLY READING</div>
          </div>
          <div class="metro-tile metro-cobalt">
            <div class="tile-top">
              <div class="tile-kicker">STACK</div>
              <div class="tile-badge">QUEUE</div>
            </div>
            <div class="tile-huge">{len(want)}</div>
            <div class="tile-label">WANT TO READ</div>
          </div>
          <div class="metro-tile metro-emerald">
            <div class="tile-top">
              <div class="tile-kicker">ARCHIVE</div>
              <div class="tile-badge">FINISHED</div>
            </div>
            <div class="tile-huge">{len(finished)}</div>
            <div class="tile-label">BOOKS COMPLETED</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.celebrate_id:
        celeb = book_by_id(books, st.session_state.celebrate_id)
        if celeb:
            st.success(f"Finished **{celeb.get('title') or 'Untitled'}** — congratulations on another completed title!")
        st.session_state.celebrate_id = None

    pulled = book_by_id(books, st.session_state.open_book_id)
    if pulled:
        st.write("")
        render_pulled_book(pulled, library, settings)

    render_currently_reading(library, reading, settings)
    render_recommendations(library, books, reading)

    if reading:
        section_header("Active Tiles", "On the reading shelf", len(reading))
        render_shelf(reading, "reading", cols=shelf_cols_pref, portrait=is_portrait)

    section_header("The Reading Stack", "Want to read", len(want))
    if want:
        render_shelf(want, "want", cols=shelf_cols_pref, portrait=is_portrait)
    else:
        st.markdown('<div class="empty-shelf">The want-to-read shelf is empty.</div>', unsafe_allow_html=True)

    if finished:
        section_header("Hall of Completion", "Finished titles", len(finished))
        render_shelf(finished, "done", cols=shelf_cols_pref, portrait=is_portrait)
    else:
        st.caption("Finished books will line up on their own shelf.")

    with st.expander("➕ Add a new book to the shelf"):
        with st.form("add_book", clear_on_submit=True):
            cols = st.columns([1.4, 1.2, 0.6, 0.5])
            title = cols[0].text_input("Title")
            author = cols[1].text_input("Author")
            pages = cols[2].number_input("Pages", min_value=0, step=1, value=0)
            priority = cols[3].slider("Priority", 1, 5, 3)
            category = st.selectbox("Category / Genre", CATEGORIES, index=CATEGORIES.index("Other"))
            notes = st.text_area("Notes", placeholder="Edition, why you want to read it, where it sits…")
            photo = st.file_uploader("Cover photo", type=["jpg", "jpeg", "png", "webp"])
            submitted = st.form_submit_button("Add to Shelf", width="stretch")
        if submitted:
            cover = ""
            source_image = ""
            if photo is not None:
                dest = UPLOADS / "covers" / f"{date.today().isoformat()}-{Path(photo.name).stem}.jpg.enc"
                dest.parent.mkdir(parents=True, exist_ok=True)
                image = ImageOps.exif_transpose(Image.open(io.BytesIO(photo.getvalue()))).convert("RGB")
                image.thumbnail((600, 900), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                image.save(buf, format="JPEG", quality=92)
                dest = write_encrypted_cover(dest, buf.getvalue(), session_key())
                cover = stored_path(dest)
                source_image = photo.name
            if not cover:
                st.error("Add a cover photo so it can sit on the shelf as a live tile.")
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

# ---------------------------------------------------------------------------
# View: Planner
# ---------------------------------------------------------------------------

elif page == "Planner":
    st.markdown(
        """
        <div class="metro-panorama">
          <div class="metro-kicker">02 // CADENCE</div>
          <h1 class="metro-panorama-title">planner <span class="metro-pivot">schedule</span></h1>
          <div class="metro-subhead">Turn the shelf into an automatic daily reading cadence.</div>
        </div>
        """,
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
        "Plan start date",
        value=date.fromisoformat(settings.get("start_date") or date.today().isoformat()),
    ).isoformat()
    rest = st.multiselect(
        "Rest weekdays",
        options=list(range(7)),
        default=[int(x) for x in (settings.get("rest_weekdays") or [])],
        format_func=lambda i: WEEKDAY_NAMES[i],
    )
    settings["rest_weekdays"] = rest
    if st.button("Save Plan Settings", width="stretch"):
        persist(library)

    schedule = build_schedule(books, settings)
    finish = estimated_finish(schedule)
    budget = daily_page_budget(settings)

    st.markdown(
        f"""
        <div class="metro-tile-row" style="margin: 1.2rem 0;">
          <div class="metro-tile metro-emerald">
            <div class="tile-top">
              <div class="tile-kicker">DAILY TARGET</div>
              <div class="tile-badge">PAGES</div>
            </div>
            <div class="tile-huge">{budget}</div>
            <div class="tile-label">DAILY PAGE BUDGET</div>
          </div>
          <div class="metro-tile metro-cobalt">
            <div class="tile-top">
              <div class="tile-kicker">PROJECTED FINISH</div>
              <div class="tile-badge">ETA</div>
            </div>
            <div class="tile-huge" style="font-size: 1.6rem !important;">{finish or "—"}</div>
            <div class="tile-label">FULL SHELF COMPLETION</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("Upcoming Itinerary", "Next 21 reading days")
    for day in schedule[:21]:
        if day.get("rest"):
            st.markdown(
                f'<div class="plan-day"><strong>{day["date"]}</strong> · <span class="metro-subhead">Rest Day</span></div>',
                unsafe_allow_html=True,
            )
        else:
            bits = ", ".join(f'{a["title"]} ({a["pages"]}p)' for a in day.get("assignments") or [])
            st.markdown(
                f'<div class="plan-day"><strong>{day["date"]}</strong> · <b>{day["pages"]} pages</b>'
                f'<br><span class="metro-subhead">{html.escape(bits)}</span></div>',
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# View: Today
# ---------------------------------------------------------------------------

elif page == "Today":
    st.markdown(
        """
        <div class="metro-panorama">
          <div class="metro-kicker">03 // FOCUS</div>
          <h1 class="metro-panorama-title">today <span class="metro-pivot">reading</span></h1>
          <div class="metro-subhead">Log pages, maintain your daily streak, and build velocity.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_score_widget(stats)

    if pick:
        st.markdown('<div class="now-card">', unsafe_allow_html=True)
        t_col, c_col = st.columns([1, 2], gap="large")
        with t_col:
            show_cover(pick, 340)
        with c_col:
            st.subheader(pick.get("title") or "Untitled")
            st.caption(f"{pick.get('author') or 'Unknown'} · {pick.get('category') or 'General'}")
            if assignment:
                st.write(f"Planned target for today: **{assignment['pages']} pages**.")
            render_page_logger(library, pick, "today")
            if st.button("Start Reading This Book", key="today-start", width="stretch"):
                pick["status"] = "reading"
                st.session_state.open_book_id = pick["id"]
                persist(library)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No active books assigned for today. Pick one on the Library page.")

    section_header("Audit Trail", "Recent reading log")
    recent = list(reversed(log[-14:]))
    if not recent:
        st.caption("No pages logged yet — use +10 / +25 to record today's reading.")
    for entry in recent:
        st.markdown(
            f'<div class="plan-day"><span class="metro-kicker">{entry.get("at", "")[:10]}</span> '
            f'· <b>+{entry.get("pages")} pages</b> · {html.escape(entry.get("title") or "Untitled")}</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# View: Analytics
# ---------------------------------------------------------------------------

elif page == "Analytics":
    st.markdown(
        """
        <div class="metro-panorama">
          <div class="metro-kicker">04 // TELEMETRY</div>
          <h1 class="metro-panorama-title">analytics <span class="metro-pivot">insights</span></h1>
          <div class="metro-subhead">Genre mix, reading velocity, book length distribution, and completion projections.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_score_widget(stats)

    total_pages = sum(int(b.get("pages") or 0) for b in books)
    pages_read = sum(int(b.get("pages_read") or 0) for b in books)

    st.markdown(
        f"""
        <div class="metro-tile-row">
          <div class="metro-tile metro-cobalt">
            <div class="tile-top">
              <div class="tile-kicker">TITLES</div>
              <div class="tile-badge">COUNT</div>
            </div>
            <div class="tile-huge">{len(books)}</div>
            <div class="tile-label">SHELF CATALOG</div>
          </div>
          <div class="metro-tile metro-mango">
            <div class="tile-top">
              <div class="tile-kicker">TOTAL PAGES</div>
              <div class="tile-badge">VOLUME</div>
            </div>
            <div class="tile-huge" style="font-size:2.2rem !important;">{total_pages:,}</div>
            <div class="tile-label">CATALOG PAGES</div>
          </div>
          <div class="metro-tile metro-emerald">
            <div class="tile-top">
              <div class="tile-kicker">PAGES READ</div>
              <div class="tile-badge">PROGRESS</div>
            </div>
            <div class="tile-huge" style="font-size:2.2rem !important;">{pages_read:,}</div>
            <div class="tile-label">PAGES COMPLETED</div>
          </div>
          <div class="metro-tile metro-magenta">
            <div class="tile-top">
              <div class="tile-kicker">LOG ENTRIES</div>
              <div class="tile-badge">RECORDS</div>
            </div>
            <div class="tile-huge">{len(log)}</div>
            <div class="tile-label">SESSIONS LOGGED</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    section_header("Composition", "Genre & status telemetry")
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

    section_header("Velocity", "Activity & weekly trend")
    lookback = st.slider("Activity window (days)", 7, 60, 30, key="activity-days")
    st.plotly_chart(
        activity_charts(log, days=int(lookback)),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.plotly_chart(weekly_trend(log, weeks=8), width="stretch", config={"displayModeBar": False})

    section_header("Distribution", "Length & priority")
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
        st.caption("Windows Phone accents: Cyan (P1) · Cobalt (P2) · Mango (P3) · Magenta (P4) · Crimson (P5).")

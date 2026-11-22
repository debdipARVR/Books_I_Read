"""Plotly charts for Shelf Plan analytics — Windows Phone Metro palette."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from planner import daily_page_budget, remaining_pages

# Windows Phone Metro flat chromatic palette: Cobalt, Mango, Emerald, Cyan, Magenta, Purple, Crimson, Amber
PALETTE = [
    "#0078d4",  # Cobalt Blue
    "#f09609",  # Mango Orange
    "#107c41",  # Emerald Green
    "#00a4ef",  # Cyan
    "#d80073",  # Magenta
    "#6a00ff",  # Purple
    "#e81123",  # Crimson
    "#ffb900",  # Amber / Gold
]

STATUS_COLORS = {
    "unread": "#0078d4",
    "reading": "#f09609",
    "done": "#107c41",
}

STATUS_LABELS = {
    "unread": "Want to read",
    "reading": "Currently reading",
    "done": "Finished",
}

LENGTH_BUCKETS = [
    ("Quick reads (<200p)", 0, 200, "#00a4ef"),
    ("Standard (200–400p)", 200, 400, "#0078d4"),
    ("Deep dives (>400p)", 400, 10_000, "#6a00ff"),
]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(20,24,29,0.75)",
    font=dict(family="Segoe UI, -apple-system, sans-serif", color="#c9d1d9", size=12),
    margin=dict(l=16, r=16, t=56, b=72),
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.12,
        xanchor="center",
        x=0.5,
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#8b949e"),
    ),
    hoverlabel=dict(
        bgcolor="#14181d",
        font_size=12,
        font_family="Segoe UI, -apple-system, sans-serif",
        font_color="#ffffff",
        bordercolor="#22272e",
    ),
)


def _apply_layout(fig: go.Figure, *, height: int = 360, title: str = "") -> go.Figure:
    fig.update_layout(
        **CHART_LAYOUT,
        height=height,
        title=dict(
            text=title,
            x=0.02,
            xanchor="left",
            font=dict(family="Segoe UI, -apple-system, sans-serif", size=16, color="#ffffff"),
        ),
    )
    fig.update_xaxes(gridcolor="#22272e", zeroline=False, showline=False, color="#8b949e")
    fig.update_yaxes(gridcolor="#22272e", zeroline=False, showline=False, color="#8b949e")
    return fig


def _empty_fig(message: str, height: int = 320) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#768390", family="Segoe UI, -apple-system, sans-serif"),
    )
    fig.update_layout(
        **CHART_LAYOUT,
        height=height,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def category_donut(books: list[dict[str, Any]], *, by_pages: bool = False) -> go.Figure:
    totals: dict[str, float] = defaultdict(float)
    for book in books:
        cat = (book.get("category") or "Other").strip() or "Other"
        if by_pages:
            totals[cat] += max(int(book.get("pages") or 0), 0)
        else:
            totals[cat] += 1
    if not totals:
        return _empty_fig("No books on the shelf yet.")

    labels = sorted(totals.keys(), key=lambda k: -totals[k])
    values = [totals[k] for k in labels]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    metric = "pages" if by_pages else "books"

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=colors, line=dict(color="#0d0f12", width=2)),
                textinfo="percent",
                textposition="inside",
                insidetextorientation="horizontal",
                hovertemplate="<b>%{label}</b><br>%{value:.0f} " + metric + "<br>%{percent}<extra></extra>",
                sort=False,
            )
        ]
    )
    title = "Pages by genre" if by_pages else "Books by genre"
    center = f"<b>{sum(values):.0f}</b><br><span style='font-size:11px;color:#8b949e'>{metric.upper()}</span>"
    fig.add_annotation(
        text=center,
        x=0.5,
        y=0.5,
        font=dict(size=18, family="Segoe UI, -apple-system, sans-serif", color="#ffffff"),
        showarrow=False,
    )
    fig = _apply_layout(fig, height=400, title=title)
    fig.update_layout(legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", yanchor="top"), margin=dict(b=90, t=50, l=10, r=10))
    return fig


def status_donut(books: list[dict[str, Any]]) -> go.Figure:
    counts = {"unread": 0, "reading": 0, "done": 0}
    for book in books:
        status = book.get("status") or "unread"
        if status not in counts:
            status = "unread"
        counts[status] += 1
    if sum(counts.values()) == 0:
        return _empty_fig("No shelf status yet.")

    labels = [STATUS_LABELS[k] for k in counts if counts[k] > 0]
    values = [counts[k] for k in counts if counts[k] > 0]
    colors = [STATUS_COLORS[k] for k in counts if counts[k] > 0]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=colors, line=dict(color="#0d0f12", width=2)),
                textinfo="value",
                textposition="inside",
                hovertemplate="<b>%{label}</b><br>%{value} books (%{percent})<extra></extra>",
                sort=False,
            )
        ]
    )
    fig.add_annotation(
        text=f"<b>{sum(values)}</b><br><span style='font-size:11px;color:#8b949e'>ON SHELF</span>",
        x=0.5,
        y=0.5,
        font=dict(size=18, family="Segoe UI, -apple-system, sans-serif", color="#ffffff"),
        showarrow=False,
    )
    fig = _apply_layout(fig, height=400, title="Reading status")
    fig.update_layout(legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", yanchor="top"), margin=dict(b=90, t=50, l=10, r=10))
    return fig


def _parse_log_day(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None


def activity_charts(progress_log: list[dict[str, Any]], *, days: int = 30) -> go.Figure:
    end = date.today()
    start = end - timedelta(days=max(days - 1, 0))
    daily: dict[date, int] = {start + timedelta(days=i): 0 for i in range((end - start).days + 1)}

    for entry in progress_log or []:
        day = _parse_log_day(entry.get("at") or "")
        if day is None or day < start or day > end:
            continue
        daily[day] = daily.get(day, 0) + int(entry.get("pages") or 0)

    if not any(daily.values()):
        return _empty_fig("Log pages on Library or Today to see velocity here.")

    xs = sorted(daily.keys())
    ys = [daily[d] for d in xs]
    cumulative = []
    running = 0
    for y in ys:
        running += y
        cumulative.append(running)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=xs,
            y=ys,
            name="Daily pages",
            marker=dict(color="#0078d4", line=dict(width=0)),
            hovertemplate="%{x|%b %d}<br>%{y} pages<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=cumulative,
            name="Cumulative",
            mode="lines+markers",
            line=dict(color="#f09609", width=2.5),
            marker=dict(size=5, color="#ffb900"),
            fill="tozeroy",
            fillcolor="rgba(240, 150, 9, 0.12)",
            hovertemplate="%{x|%b %d}<br>Cumulative %{y} pages<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_yaxes(title_text="Pages / day", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative", secondary_y=True, showgrid=False)
    return _apply_layout(fig, height=400, title=f"Reading velocity · last {days} days")


def weekly_trend(progress_log: list[dict[str, Any]], *, weeks: int = 8) -> go.Figure:
    end = date.today()
    # Align to Monday
    this_monday = end - timedelta(days=end.weekday())
    buckets: list[tuple[date, int]] = []
    for i in range(weeks - 1, -1, -1):
        monday = this_monday - timedelta(weeks=i)
        buckets.append((monday, 0))

    week_map = {m: i for i, (m, _) in enumerate(buckets)}
    totals = [0] * weeks

    for entry in progress_log or []:
        day = _parse_log_day(entry.get("at") or "")
        if day is None:
            continue
        monday = day - timedelta(days=day.weekday())
        idx = week_map.get(monday)
        if idx is None:
            continue
        totals[idx] += int(entry.get("pages") or 0)

    if not any(totals):
        return _empty_fig("Weekly trends appear after a few logging days.")

    labels = [m.strftime("%b %d") for m, _ in buckets]
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=totals,
                marker=dict(
                    color=totals,
                    colorscale=[[0, "#161b22"], [0.5, "#0078d4"], [1, "#00a4ef"]],
                    line=dict(width=0),
                ),
                hovertemplate="Week of %{x}<br>%{y} pages<extra></extra>",
            )
        ]
    )
    return _apply_layout(fig, height=340, title=f"Weekly pages · last {weeks} weeks")


def length_distribution(books: list[dict[str, Any]]) -> go.Figure:
    if not books:
        return _empty_fig("Add books to see length mix.")

    counts = []
    colors = []
    labels = []
    for label, lo, hi, color in LENGTH_BUCKETS:
        n = sum(1 for b in books if lo <= int(b.get("pages") or 0) < hi)
        labels.append(label)
        counts.append(n)
        colors.append(color)

    # Histogram of raw page counts
    pages = [int(b.get("pages") or 0) for b in books if int(b.get("pages") or 0) > 0]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Length buckets", "Page histogram"), horizontal_spacing=0.12)

    fig.add_trace(
        go.Bar(
            x=labels,
            y=counts,
            marker=dict(color=colors, line=dict(width=0)),
            hovertemplate="%{x}<br>%{y} books<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    if pages:
        fig.add_trace(
            go.Histogram(
                x=pages,
                nbinsx=12,
                marker=dict(color="#6a00ff", line=dict(color="#0d0f12", width=1)),
                hovertemplate="%{x} pages bin<br>%{y} books<extra></extra>",
                showlegend=False,
            ),
            row=1,
            col=2,
        )
    fig.update_layout(
        **CHART_LAYOUT,
        height=380,
        title=dict(text="Book length mix", font=dict(family="Segoe UI, -apple-system, sans-serif", size=16, color="#ffffff")),
    )
    fig.update_xaxes(gridcolor="#22272e", tickangle=-20, row=1, col=1)
    fig.update_xaxes(title_text="Pages", gridcolor="#22272e", row=1, col=2)
    fig.update_yaxes(title_text="Books", gridcolor="#22272e")
    return fig


def completion_projections(
    books: list[dict[str, Any]],
    settings: dict[str, Any],
    progress_log: list[dict[str, Any]],
) -> go.Figure:
    """Project finish dates for active books from recent velocity or plan budget."""
    active = [
        b
        for b in books
        if (b.get("status") or "unread") in {"unread", "reading"} and remaining_pages(b) > 0
    ]
    if not active:
        return _empty_fig("Nothing left to project — shelf is clear.")

    # Velocity from last 14 days of logging, else fall back to daily budget
    end = date.today()
    start = end - timedelta(days=13)
    pages_recent = 0
    active_days = set()
    for entry in progress_log or []:
        day = _parse_log_day(entry.get("at") or "")
        if day is None or day < start or day > end:
            continue
        pages_recent += int(entry.get("pages") or 0)
        active_days.add(day)
    if active_days:
        velocity = max(pages_recent / max(len(active_days), 1), 1.0)
        velocity_label = f"~{velocity:.0f} pages/day from your recent log"
    else:
        velocity = float(daily_page_budget(settings))
        velocity_label = f"~{velocity:.0f} pages/day from your plan budget"

    # Focus on currently reading first, then top priority unread (cap 8)
    reading = [b for b in active if b.get("status") == "reading"]
    unread = sorted(
        [b for b in active if b.get("status") != "reading"],
        key=lambda b: (-int(b.get("priority") or 0), remaining_pages(b)),
    )
    focus = (reading + unread)[:8]

    titles = []
    lefts = []
    days_needed = []
    finish_labels = []
    colors = []
    for book in focus:
        left = remaining_pages(book)
        days = max(int(round(left / velocity)), 1)
        finish = end + timedelta(days=days)
        titles.append((book.get("title") or "Untitled")[:36])
        lefts.append(left)
        days_needed.append(days)
        finish_labels.append(finish.isoformat())
        colors.append("#f09609" if book.get("status") == "reading" else "#0078d4")

    fig = go.Figure(
        data=[
            go.Bar(
                y=titles[::-1],
                x=days_needed[::-1],
                orientation="h",
                marker=dict(color=colors[::-1], line=dict(width=0)),
                customdata=list(zip(lefts[::-1], finish_labels[::-1])),
                hovertemplate="<b>%{y}</b><br>%{customdata[0]} pages left<br>~%{x} days<br>ETA %{customdata[1]}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        **CHART_LAYOUT,
        height=max(320, 56 * len(focus) + 80),
        title=dict(
            text=f"Completion projections<br><span style='font-size:11px;color:#8b949e'>{velocity_label}</span>",
            font=dict(family="Segoe UI, -apple-system, sans-serif", size=16, color="#ffffff"),
        ),
        xaxis_title="Days until finish (at current velocity)",
    )
    fig.update_xaxes(gridcolor="#22272e")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def priority_bars(books: list[dict[str, Any]]) -> go.Figure:
    counts = {i: 0 for i in range(1, 6)}
    for book in books:
        p = int(book.get("priority") or 3)
        p = min(max(p, 1), 5)
        counts[p] += 1
    if not books:
        return _empty_fig("No priority data yet.")

    fig = go.Figure(
        data=[
            go.Bar(
                x=[f"P{i}" for i in range(1, 6)],
                y=[counts[i] for i in range(1, 6)],
                marker=dict(
                    color=["#00a4ef", "#0078d4", "#f09609", "#d80073", "#e81123"],
                    line=dict(width=0),
                ),
                hovertemplate="Priority %{x}<br>%{y} books<extra></extra>",
            )
        ]
    )
    return _apply_layout(fig, height=300, title="Priority stack")

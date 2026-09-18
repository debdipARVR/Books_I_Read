"""Filter out non-cover entries and assign categories."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "library.json"

# Stapled notes / inner pages / TOC scans — not shelf covers
EXCLUDE_TITLES = {
    "FAANG SDET DS Missing Problems",
    "Python SDET Detailed Revision Book",
    "Playwright with pytest & Python: The Complete Book",
    "LeetCode Solutions Book",
    "Web & API Architecture Reference Guide",
    "Comprehensive DeepEval: Testing a Chatbot with Python",
}

CATEGORY_BY_TITLE = {
    "Programming in Python: A Problem Solving Approach (2nd Edition)": "Tech / Python",
    "Let Us Python (7th Edition)": "Tech / Python",
    "Data Analytics with R": "Tech / Python",
    "Deep Learning with Python (2nd Edition)": "Tech / Python",
    "Head First Agile": "Tech / Python",
    "Head First Data Analysis / Excel": "Tech / Python",
    "Nexus: A Brief History of Information Networks from the Stone Age to AI": "Tech / Python",
    "The Bitcoin Saga: A Mixed Montage": "Tech / Python",
    "Atomic Habits: Tiny Changes, Remarkable Results": "Habits / Productivity",
    "Deep Work: Rules for Focused Success in a Distracted World": "Habits / Productivity",
    "Eat That Frog!: 21 Great Ways to Stop Procrastinating": "Habits / Productivity",
    "No Excuses!: The Power of Self-Discipline": "Habits / Productivity",
    "The Mountain Is You: Transforming Self-Sabotage into Self-Mastery": "Habits / Productivity",
    "Emotional Intelligence Habits": "Habits / Productivity",
    "Range: How Generalists Triumph in a Specialized World": "Habits / Productivity",
    "Meditations": "Mind / Spiritual",
    "Introduction to Bhagavad-gita": "Mind / Spiritual",
    "Bhagavad-gita As It Is": "Mind / Spiritual",
    "The Science of Self-Realization": "Mind / Spiritual",
    "Shrimad Bhagavad Gita (Code 2099)": "Mind / Spiritual",
    "Gita for Everyday Living": "Mind / Spiritual",
    "The Power of Thoughts": "Mind / Spiritual",
    "Life's Amazing Secrets: How to Find Balance and Purpose": "Mind / Spiritual",
    "Extra Sensory Potentials of the Mind": "Mind / Spiritual",
    "Dignity of Organisational Skill": "Mind / Spiritual",
    "How to Overcome Mental Tension": "Mind / Spiritual",
    "Code Name God: The Spiritual Odyssey of a Man of Science": "Mind / Spiritual",
    "Feeling Good: The New Mood Therapy": "Mind / Spiritual",
    "The Courage to Be Disliked": "Mind / Spiritual",
    "Ikigai: The Japanese Secret to a Long and Happy Life": "Mind / Spiritual",
    "Zen: The Art of Simple Living": "Mind / Spiritual",
    "Man's Search for Meaning": "Mind / Spiritual",
    "The Power of Positive Thinking": "Mind / Spiritual",
    "40 Sufi Comics": "Mind / Spiritual",
    "Zero to One: Notes on Startups, or How to Build the Future": "Business / Finance",
    "Think and Grow Rich (21st Century Edition)": "Business / Finance",
    "The Richest Man in Babylon": "Business / Finance",
    "The Five Dysfunctions of a Team": "Business / Finance",
    "The Case of the Bonsai Manager": "Business / Finance",
    "The Ambuja Story": "Business / Finance",
    "HBR Guide to Better Business Writing": "Business / Finance",
    "The Quick and Easy Way to Effective Speaking": "Business / Finance",
    "Let's Talk Money": "Business / Finance",
    "The Hungry Tide": "Literature",
    "The Home and the World (Ghare Baire)": "Literature",
    "One Indian Girl": "Literature",
    "Vagabond (Manga Series)": "Literature",
    "Deep Focus: Reflections on Cinema": "Literature",
    "Sapiens: A Brief History of Humankind": "Literature",
    "Mossad: The Greatest Missions of the Israeli Secret Service": "Literature",
    "OPEN Magazine (July 2026 Issue)": "Literature",
    "Back to the Roots: Celebrating Indian Wisdom and Wellness": "Health / Wellness",
    "Own Your Body: A Doctor's Life-Saving Tips": "Health / Wellness",
    "How Not to Die": "Health / Wellness",
    "Elon Musk: Quest for a Fantastic Future": "Biography",
    "Sachin Tendulkar (Pictorial Biography)": "Biography",
    "Bhagat Singh (Pictorial Biography)": "Biography",
    "The Last Lecture": "Biography",
}


def main() -> None:
    lib = json.loads(DATA.read_text(encoding="utf-8"))
    before = len(lib.get("books", []))
    kept = []
    for book in lib.get("books", []):
        title = book.get("title") or ""
        if title in EXCLUDE_TITLES:
            continue
        cover = Path(book.get("cover_path") or "")
        if not cover.is_file():
            print(f"DROP (no cover file): {title}")
            continue
        book["category"] = CATEGORY_BY_TITLE.get(title, book.get("category") or "Other")
        kept.append(book)

    lib["books"] = kept
    lib.setdefault("progress_log", [])
    DATA.write_text(json.dumps(lib, indent=2), encoding="utf-8")
    print(f"Cleaned library: {before} → {len(kept)} books with real covers")
    for b in kept:
        print(f"  [{b.get('category')}] {b['title']}")


if __name__ == "__main__":
    main()

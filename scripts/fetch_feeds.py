#!/usr/bin/env python3
"""
Pulls racing and sport RSS/Atom feeds and writes feeds.json for the dashboard.

Runs on GitHub Actions, not in the browser — which is the whole point. A static
page cannot fetch these feeds directly (no CORS headers on news sites), so we
fetch server-side and commit the result for the dashboard to read same-origin.

Standard library only: no pip install, nothing to break on a dependency bump.

To add or remove a source, edit FEEDS below. A dead URL is skipped with a
warning rather than failing the run.
"""

import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

# (label, category, url)  — category drives the filter chips in the dashboard
FEEDS = [
    # ── Australian racing ────────────────────────────────────────────────
    ("Racenet",           "racing", "https://www.racenet.com.au/rss"),
    ("Racing.com",        "racing", "https://www.racing.com/rss"),
    ("Punters",           "racing", "https://www.punters.com.au/rss/"),
    ("Roar Racing",       "racing", "https://www.theroar.com.au/horse-racing/feed/"),
    ("Just Horse Racing", "racing", "https://www.justhorseracing.com.au/feed/"),
    ("Guardian Racing",   "racing", "https://www.theguardian.com/sport/horse-racing/rss"),

    # ── AFL ──────────────────────────────────────────────────────────────
    ("AFL.com.au",        "afl",    "https://www.afl.com.au/rss"),
    ("Roar AFL",          "afl",    "https://www.theroar.com.au/afl/feed/"),
    ("Guardian AFL",      "afl",    "https://www.theguardian.com/sport/afl/rss"),

    # ── Rugby league ─────────────────────────────────────────────────────
    ("Roar NRL",          "nrl",    "https://www.theroar.com.au/nrl/feed/"),
    ("Zero Tackle",       "nrl",    "https://www.zerotackle.com/feed/"),
    ("Guardian League",   "nrl",    "https://www.theguardian.com/sport/rugbyleague/rss"),

    # ── Rugby union ──────────────────────────────────────────────────────
    ("Roar Union",        "union",  "https://www.theroar.com.au/rugby-union/feed/"),
    ("Guardian Union",    "union",  "https://www.theguardian.com/sport/rugby-union/rss"),

    # ── General Australian sport ─────────────────────────────────────────
    ("ABC Sport",         "sport",  "https://www.abc.net.au/news/feed/45924/rss.xml"),
    ("SMH Sport",         "sport",  "https://www.smh.com.au/rss/sport.xml"),
    ("The Age Sport",     "sport",  "https://www.theage.com.au/rss/sport.xml"),
    ("Roar Sport",        "sport",  "https://www.theroar.com.au/feed/"),
    ("Guardian AU Sport", "sport",  "https://www.theguardian.com/sport/australia-sport/rss"),
]

MAX_PER_FEED = 10
MAX_TOTAL = 90
EXCERPT_CHARS = 210
TIMEOUT = 20

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(text):
    """Strip markup and collapse whitespace. Feeds embed HTML in descriptions."""
    if not text:
        return ""
    text = TAG_RE.sub(" ", text)
    text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
                .replace("&hellip;", "…").replace("&mdash;", "—").replace("&ndash;", "–")
                .replace("&rsquo;", "'").replace("&lsquo;", "'")
                .replace("&ldquo;", '"').replace("&rdquo;", '"'))
    return WS_RE.sub(" ", text).strip()


def excerpt(text):
    text = clean(text)
    if len(text) <= EXCERPT_CHARS:
        return text
    cut = text[:EXCERPT_CHARS].rsplit(" ", 1)[0]
    return cut + "…"


def parse_date(raw):
    """RSS uses RFC-822, Atom uses ISO-8601. Try both, fall back to now."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def text_of(node, *paths):
    for path in paths:
        found = node.find(path, NS) if ":" in path or path.startswith("atom") else node.find(path)
        if found is not None:
            if found.text and found.text.strip():
                return found.text
            href = found.get("href")
            if href:
                return href
    return ""


def parse_feed(xml_bytes, label, category):
    """Handles RSS 2.0 <item> and Atom <entry> in one pass."""
    root = ET.fromstring(xml_bytes)
    nodes = root.findall(".//item") or root.findall(".//atom:entry", NS)
    out = []

    for node in nodes[:MAX_PER_FEED]:
        title = clean(text_of(node, "title", "atom:title"))
        link = text_of(node, "link", "atom:link").strip()
        if not title or not link:
            continue

        raw_date = text_of(node, "pubDate", "atom:published", "atom:updated", "dc:date")
        dt = parse_date(raw_date)

        desc = text_of(node, "description", "atom:summary", "atom:content")

        # some feeds leak off-topic items - keep it to sport
        if "theguardian.com" in link and not any(
                seg in link for seg in ("/sport/", "/football/", "/sport-", "/afl", "/nrl")):
            continue

        out.append({
            "title": title,
            "link": link,
            "excerpt": excerpt(desc),
            "source": label,
            "category": category,
            "published": dt.isoformat() if dt else None,
            "ts": int(dt.timestamp()) if dt else 0,
        })
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def main():
    items, ok, failed = [], [], []

    for label, category, url in FEEDS:
        try:
            items.extend(parse_feed(fetch(url), label, category))
            ok.append(label)
            print(f"  ok      {label}")
        except Exception as exc:
            failed.append(label)
            print(f"  skipped {label}: {type(exc).__name__}: {exc}", file=sys.stderr)

    # de-duplicate by link, newest first
    seen, unique = set(), []
    for item in sorted(items, key=lambda i: i["ts"], reverse=True):
        if item["link"] in seen:
            continue
        seen.add(item["link"])
        unique.append(item)

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "sources_ok": ok,
        "sources_failed": failed,
        "items": unique[:MAX_TOTAL],
    }

    with open("feeds.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    print(f"\n{len(payload['items'])} items from {len(ok)}/{len(FEEDS)} feeds")
    if failed:
        print(f"failed: {', '.join(failed)}")

    # only a total wipeout is worth failing the run over
    if not ok:
        print("ERROR: every feed failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

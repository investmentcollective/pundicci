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

    # ── Tipsters & form ──────────────────────────────────────────────────
    # Mostly WordPress, so /feed/ and /category/<x>/feed/ are the conventions.
    # These sites run on bookmaker affiliate revenue - PROMO_TERMS below
    # strips the promo-code and "best betting site" filler they publish
    # alongside genuine tips.
    ("KRUZEY",            "tips",   "https://www.kruzey.com.au/feed/"),
    ("JHR Tips",          "tips",   "https://www.justhorseracing.com.au/category/tips/feed/"),
    ("Expert Footy Tips", "tips",   "https://expertfootytips.com.au/feed/"),
    ("Racing & Sports",   "tips",   "https://www.racingandsports.com.au/rss"),
    ("Just Racing",       "tips",   "https://www.justracing.com.au/feed/"),
    ("RacingBase",        "tips",   "https://www.racingbase.com.au/feed/"),
    ("Great Tip Off",     "tips",   "https://thegreattipoff.com/feed/"),

    # ── General Australian sport ─────────────────────────────────────────
    ("ABC Sport",         "sport",  "https://www.abc.net.au/news/feed/45924/rss.xml"),
    ("SMH Sport",         "sport",  "https://www.smh.com.au/rss/sport.xml"),
    ("The Age Sport",     "sport",  "https://www.theage.com.au/rss/sport.xml"),
    ("Roar Sport",        "sport",  "https://www.theroar.com.au/feed/"),
    ("Guardian AU Sport", "sport",  "https://www.theguardian.com/sport/australia-sport/rss"),
]

# ══════════════════════════════════════════════════════════════════════════
#  Relevance filter
#  Publishers mix Australian and overseas coverage in the same feed, so every
#  item is screened on its title + excerpt. Edit these lists to tune it.
# ══════════════════════════════════════════════════════════════════════════

# Australian publishers. Their items pass without needing a positive AU
# signal, but are still screened against BLOCK_TERMS and JUNK_TERMS.
TRUSTED_AU_DOMAINS = (
    "abc.net.au", "smh.com.au", "theage.com.au", "theroar.com.au",
    "afl.com.au", "nrl.com", "racenet.com.au", "racing.com",
    "punters.com.au", "justhorseracing.com.au", "zerotackle.com",
)

# Overseas competitions and venues. Terms are deliberately specific:
# "Ascot", "Sandown", "Newcastle" and "Doncaster" all exist in both
# Australia and Britain, so only unambiguous forms are listed.
BLOCK_TERMS = (
    # British & Irish racing
    "goodwood", "royal ascot", "cheltenham", "aintree", "newmarket",
    "epsom", "haydock", "kempton", "ebor", "grand national", "st leger",
    "british flat", "curragh", "punchestown", "leopardstown",
    "1,000 guineas", "2,000 guineas", "kentucky derby", "breeders' cup",
    "sandown park", "doncaster cup", "dubai world cup",
    # Super League / English rugby league
    "super league", "wigan", "st helens", "leeds rhinos", "hull kr",
    "hull fc", "warrington", "castleford", "catalans", "salford red",
    "huddersfield", "leigh leopards", "wakefield trinity", "challenge cup",
    # English & European rugby union
    "premiership rugby", "gallagher premiership", "saracens",
    "northampton saints", "sale sharks", "harlequins", "leicester tigers",
    "gloucester rugby", "exeter chiefs", "six nations", "top 14",
    # codes the collective never bets
    "nfl", "nba", "mlb", "nhl", "super bowl", "liv golf", "pga tour",
    "us open", "wimbledon", "roland garros", "formula one",
    "premier league", "la liga", "serie a", "bundesliga",
)

# Positive Australian / trans-Tasman signals. Required from overseas outlets.
AU_TERMS = (
    # racing venues and features
    "flemington", "caulfield", "randwick", "rosehill", "moonee valley",
    "doomben", "eagle farm", "morphettville", "warwick farm", "canterbury",
    "melbourne cup", "cox plate", "golden slipper", "caulfield cup",
    "the everest", "doncaster mile", "blue diamond", "victoria derby",
    "spring carnival", "racing victoria", "racing nsw", "racing queensland",
    # NRL
    "nrl", "state of origin", "maroons", "melbourne storm", "penrith",
    "panthers", "broncos", "roosters", "rabbitohs", "bulldogs", "sharks",
    "eels", "sea eagles", "knights", "titans", "cowboys", "raiders",
    "dragons", "dolphins", "warriors",
    # AFL
    "afl", "carlton", "collingwood", "essendon", "geelong", "hawthorn",
    "richmond", "st kilda", "western bulldogs", "adelaide", "brisbane lions",
    "fremantle", "port adelaide", "west coast", "sydney swans", "gws",
    "gold coast suns", "north melbourne", "brownlow",
    # rugby union
    "wallabies", "all blacks", "queensland reds", "waratahs", "brumbies",
    "western force", "super rugby", "bledisloe", "wallaroos",
    # everything else
    "socceroos", "matildas", "a-league", "cricket australia", "big bash",
    "australia", "australian", "aussie",
)

# Article shapes that carry no betting signal
JUNK_TERMS = (
    "quiz of the week", "crossword", "obituary", "listen:", "podcast",
    "sign up for", "newsletter", "as it happened", "in pictures",
    "gallery:", "watch:", "fantasy download", "your questions answered",
)

# Tipping sites fund themselves through bookmaker affiliate deals and publish
# marketing in the same feed as their tips. This keeps the ads out.
PROMO_TERMS = (
    "promo code", "bonus code", "sign-up offer", "signup offer",
    "welcome bonus", "deposit match", "free bet", "bet back",
    "best betting site", "best betting app", "betting site review",
    "bookmaker review", "new betting site", "refer a friend",
    "exclusive offer", "claim your", "join now", "bonus bet",
    "review:", "vs bet365", "odds boost",
)


def is_relevant(title, excerpt_text, link):
    """Returns (keep, reason) so rejections can be counted and reported."""
    text = (title + " " + excerpt_text).lower()

    for term in PROMO_TERMS:
        if term in text:
            return False, "promo"

    # bookmaker review and promo sections, caught by URL as well as by text
    if any(seg in link for seg in ("/promo-codes/", "/reviews/",
                                   "/betting-sites", "/betting-apps")):
        return False, "promo"

    for term in JUNK_TERMS:
        if term in text:
            return False, "junk"

    for term in BLOCK_TERMS:
        if term in text:
            return False, "overseas"

    if any(dom in link for dom in TRUSTED_AU_DOMAINS):
        return True, "au-source"

    if any(term in text for term in AU_TERMS):
        return True, "au-signal"

    return False, "no-au-context"


REJECTS = {}

MAX_PER_FEED = 14
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

        # some feeds leak non-sport entirely (Guardian files lifestyle pieces
        # under australia-sport), so gate on the URL path first
        if "theguardian.com" in link and not any(
                seg in link for seg in ("/sport/", "/football/", "/sport-", "/afl", "/nrl")):
            REJECTS["off-topic"] = REJECTS.get("off-topic", 0) + 1
            continue

        ex = excerpt(desc)
        keep, reason = is_relevant(title, ex, link)
        if not keep:
            REJECTS[reason] = REJECTS.get(reason, 0) + 1
            continue

        out.append({
            "title": title,
            "link": link,
            "excerpt": ex,
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
        "filtered": REJECTS,
        "items": unique[:MAX_TOTAL],
    }

    with open("feeds.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    print(f"\n{len(payload['items'])} items kept from {len(ok)}/{len(FEEDS)} feeds")
    if REJECTS:
        print("filtered out: " + ", ".join(
            f"{count} {reason}" for reason, count in sorted(REJECTS.items())))
    if failed:
        print(f"feeds unreachable: {', '.join(failed)}")

    # an empty result usually means the filter is too tight, not that the
    # feeds are down - say so rather than failing silently
    if ok and not payload["items"]:
        print("WARNING: every item was filtered out - loosen the filter lists",
              file=sys.stderr)

    # only a total wipeout is worth failing the run over
    if not ok:
        print("ERROR: every feed failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

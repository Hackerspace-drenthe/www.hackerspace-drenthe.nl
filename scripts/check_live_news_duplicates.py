#!/usr/bin/env python3
"""Check for duplicate news cards on a live Grav site.

Usage:
  python3 scripts/check_live_news_duplicates.py
  python3 scripts/check_live_news_duplicates.py https://hackerspace-drenthe.nl

Exit codes:
  0: no duplicates found
  1: duplicates found or request/parse error
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser


class NewsCardHrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return

        attr_map = {k.lower(): (v or "") for k, v in attrs}
        classes = attr_map.get("class", "")
        href = attr_map.get("href", "")

        # Blog cards in this theme use "card-image" links.
        if "card-image" in classes.split() and href:
            self.hrefs.append(href)


def normalize_news_href(href: str) -> str | None:
    href = href.strip()
    if not href:
        return None

    parsed = urllib.parse.urlparse(href)

    # Turn absolute site URLs into path-only values for dedupe.
    if parsed.scheme and parsed.netloc:
        path = parsed.path
    else:
        path = href

    path = path.rstrip("/")

    # Keep only article routes, not the listing page itself.
    if not path.startswith("/nieuws/"):
        return None
    if path == "/nieuws":
        return None
    return path


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "news-dup-check/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://hackerspace-drenthe.nl"
    nieuws_url = base_url.rstrip("/") + "/nieuws"

    try:
        html = fetch_text(nieuws_url)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"ERROR: could not fetch {nieuws_url}: {exc}")
        return 1

    parser = NewsCardHrefParser()
    parser.feed(html)

    normalized: list[str] = []
    for href in parser.hrefs:
        n = normalize_news_href(href)
        if n is not None:
            normalized.append(n)

    if not normalized:
        # Fallback if theme markup ever changes class names.
        fallback = re.findall(r'href=["\'](/nieuws/[^"\'#?]+)["\']', html, flags=re.IGNORECASE)
        for href in fallback:
            n = normalize_news_href(href)
            if n is not None:
                normalized.append(n)

    counts = Counter(normalized)
    duplicates = {href: cnt for href, cnt in counts.items() if cnt > 1}

    print(f"NEWS_TOTAL={len(normalized)}")
    print(f"NEWS_UNIQUE={len(counts)}")
    print(f"NEWS_DUPLICATE_ROUTES={len(duplicates)}")

    if duplicates:
        for href, cnt in sorted(duplicates.items()):
            print(f"DUP={href} x{cnt}")
        return 1

    print("OK: no duplicate news routes found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

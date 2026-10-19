#!/usr/bin/env python3
"""Download referenced wiki media files into migrated Grav pages.

This script scans migrated Markdown pages for local image references like:
- ![...](images/Foo.jpg)

For each referenced filename it queries the MediaWiki API for file metadata and
downloads the file into the expected local images folder.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

API_DEFAULT = "https://wiki.hackerspace-drenthe.nl/api.php"
FILE_PREFIXES = ["File", "Image", "Bestand"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download wiki media files for migrated Grav pages")
    parser.add_argument("--wiki-root", required=True, help="Migrated wiki root, e.g. user/pages/08.wiki")
    parser.add_argument("--api-url", default=API_DEFAULT, help="MediaWiki API endpoint")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files")
    return parser.parse_args()


def collect_missing_image_targets(wiki_root: Path) -> dict[str, list[Path]]:
    pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    targets: dict[str, list[Path]] = {}

    for md_file in wiki_root.rglob("default.md"):
        body = md_file.read_text(encoding="utf-8")
        for match in pattern.finditer(body):
            ref = match.group(1).strip()
            if ref.startswith("http://") or ref.startswith("https://") or ref.startswith("/"):
                continue
            if not ref.startswith("images/"):
                continue

            filename = Path(ref).name
            target = md_file.parent / ref
            if target.exists():
                continue

            targets.setdefault(filename, []).append(target)

    return targets


def fetch_file_url(api_url: str, filename: str) -> str | None:
    for prefix in FILE_PREFIXES:
        title = f"{prefix}:{filename}"
        params = {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
        }
        url = api_url + "?" + urllib.parse.urlencode(params)

        req = urllib.request.Request(url, headers={"User-Agent": "wiki-migration-media/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.load(response)

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            infos = page.get("imageinfo", [])
            if infos:
                file_url = infos[0].get("url")
                if file_url:
                    return file_url

    return None


def download_file(file_url: str, target: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"DRY-RUN: would download {file_url} -> {target}")
        return True

    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(file_url, headers={"User-Agent": "wiki-migration-media/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        content = response.read()
    target.write_bytes(content)
    return True


def main() -> int:
    args = parse_args()
    wiki_root = Path(args.wiki_root)

    if not wiki_root.exists():
        raise SystemExit(f"wiki root not found: {wiki_root}")

    missing_targets = collect_missing_image_targets(wiki_root)
    print(f"MISSING_UNIQUE_FILENAMES={len(missing_targets)}")

    resolved = 0
    downloaded = 0
    unresolved: list[str] = []

    url_cache: dict[str, str | None] = {}

    for filename, targets in sorted(missing_targets.items()):
        file_url = url_cache.get(filename)
        if file_url is None and filename not in url_cache:
            file_url = fetch_file_url(args.api_url, filename)
            url_cache[filename] = file_url

        if not file_url:
            unresolved.append(filename)
            continue

        resolved += 1
        for target in targets:
            if target.exists():
                continue
            if download_file(file_url, target, args.dry_run):
                downloaded += 1

    print(f"RESOLVED_FILENAMES={resolved}")
    print(f"DOWNLOADED_FILES={downloaded}")
    print(f"UNRESOLVED_FILENAMES={len(unresolved)}")

    if unresolved:
        print("Unresolved files:")
        for name in unresolved[:300]:
            print(f"  - {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

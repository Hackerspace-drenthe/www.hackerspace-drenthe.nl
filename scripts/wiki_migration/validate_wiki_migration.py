#!/usr/bin/env python3
"""Validate local Grav wiki migration before opening the big PR.

Checks:
- Broken internal /wiki links
- Missing local image assets
- Presence of excluded namespace pages
- Required frontmatter fields
- Optional: all pages approved

Usage:
  python3 scripts/wiki_migration/validate_wiki_migration.py --wiki-root user/pages/08.wiki
  python3 scripts/wiki_migration/validate_wiki_migration.py --wiki-root user/pages/08.wiki --require-approved
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

EXCLUDED_NAMESPACE_PREFIXES = {
    "special",
    "mediawiki",
    "user",
    "user talk",
    "project",
    "project talk",
    "template",
    "template talk",
    "category",
    "category talk",
    "help",
    "help talk",
    "file",
    "file talk",
    "image",
    "image talk",
    "bestands",
    "bestand",
}


@dataclass
class PageInfo:
    md_file: Path
    route: str
    frontmatter: dict[str, str]
    body: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate migrated wiki pages in Grav")
    parser.add_argument("--wiki-root", required=True, help="Wiki root folder in Grav, e.g. user/pages/08.wiki")
    parser.add_argument(
        "--require-approved",
        action="store_true",
        help="Fail validation if any page status is not approved",
    )
    return parser.parse_args()


def normalize_slug(value: str) -> str:
    value = value.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9\-/]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-/")


def route_base_for_root(wiki_root: Path) -> str:
    name = re.sub(r"^\d+\.", "", wiki_root.name)
    return "/" + normalize_slug(name)


def parse_frontmatter_and_body(md_text: str) -> tuple[dict[str, str], str]:
    if not md_text.startswith("---\n"):
        return {}, md_text

    lines = md_text.splitlines()
    frontmatter: dict[str, str] = {}

    end_index = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index == -1:
        return {}, md_text

    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"')

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return frontmatter, body


def page_route_from_file(md_file: Path, wiki_root: Path, route_base: str) -> str:
    rel = md_file.parent.relative_to(wiki_root)
    if rel.as_posix() == ".":
        return route_base
    return route_base.rstrip("/") + "/" + rel.as_posix().strip("/")


def collect_pages(wiki_root: Path, route_base: str) -> list[PageInfo]:
    pages: list[PageInfo] = []
    for md_file in sorted(wiki_root.rglob("default.md")):
        text = md_file.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter_and_body(text)
        route = page_route_from_file(md_file, wiki_root, route_base)
        pages.append(PageInfo(md_file=md_file, route=route, frontmatter=frontmatter, body=body))
    return pages


def iter_markdown_links(body: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", body)]


def iter_markdown_images(body: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", body)]


def validate(wiki_root: Path, require_approved: bool) -> int:
    route_base = route_base_for_root(wiki_root)
    pages = collect_pages(wiki_root, route_base)
    routes = {page.route for page in pages}

    missing_frontmatter: list[str] = []
    excluded_namespace_hits: list[str] = []
    broken_internal_links: list[str] = []
    missing_images: list[str] = []
    not_approved: list[str] = []

    required_fields = {"title", "status", "source_title", "source_url"}

    for page in pages:
        missing_keys = [key for key in required_fields if not page.frontmatter.get(key)]
        if missing_keys:
            missing_frontmatter.append(f"{page.md_file}: missing {', '.join(missing_keys)}")

        source_title = page.frontmatter.get("source_title", "")
        if ":" in source_title:
            prefix = source_title.split(":", 1)[0].strip().lower()
            if prefix in EXCLUDED_NAMESPACE_PREFIXES:
                excluded_namespace_hits.append(f"{page.md_file}: {source_title}")

        if require_approved and page.frontmatter.get("status", "").strip().lower() != "approved":
            not_approved.append(str(page.md_file))

        for link in iter_markdown_links(page.body):
            if link.startswith("http://") or link.startswith("https://") or link.startswith("mailto:"):
                continue
            if link.startswith("#"):
                continue

            clean_link = link.split("#", 1)[0]
            if not clean_link:
                continue

            if clean_link.startswith(route_base + "/") or clean_link == route_base:
                target = clean_link.rstrip("/") or route_base
                if target not in routes:
                    broken_internal_links.append(f"{page.md_file}: {link}")

        for img in iter_markdown_images(page.body):
            if img.startswith("http://") or img.startswith("https://"):
                continue
            if img.startswith("/"):
                continue
            img_path = (page.md_file.parent / img).resolve()
            if not img_path.exists():
                missing_images.append(f"{page.md_file}: {img}")

    print(f"PAGES={len(pages)}")
    print(f"ROUTES={len(routes)}")
    print(f"MISSING_FRONTMATTER={len(missing_frontmatter)}")
    print(f"EXCLUDED_NAMESPACE_HITS={len(excluded_namespace_hits)}")
    print(f"BROKEN_INTERNAL_LINKS={len(broken_internal_links)}")
    print(f"MISSING_IMAGES={len(missing_images)}")
    print(f"NOT_APPROVED={len(not_approved)}")

    if missing_frontmatter:
        print("\nMissing frontmatter fields:")
        for line in missing_frontmatter[:200]:
            print(f"  - {line}")

    if excluded_namespace_hits:
        print("\nPages from excluded namespaces found:")
        for line in excluded_namespace_hits[:200]:
            print(f"  - {line}")

    if broken_internal_links:
        print("\nBroken internal links:")
        for line in broken_internal_links[:200]:
            print(f"  - {line}")

    if missing_images:
        print("\nMissing local image files:")
        for line in missing_images[:200]:
            print(f"  - {line}")

    if not_approved:
        print("\nPages not approved:")
        for line in not_approved[:200]:
            print(f"  - {line}")

    has_errors = any(
        [
            missing_frontmatter,
            excluded_namespace_hits,
            broken_internal_links,
            missing_images,
            not_approved,
        ]
    )

    if has_errors:
        print("\nVALIDATION_STATUS=FAILED")
        return 1

    print("\nVALIDATION_STATUS=OK")
    return 0


def main() -> int:
    args = parse_args()
    wiki_root = Path(args.wiki_root)

    if not wiki_root.exists():
        raise SystemExit(f"wiki root not found: {wiki_root}")

    return validate(wiki_root=wiki_root, require_approved=args.require_approved)


if __name__ == "__main__":
    raise SystemExit(main())

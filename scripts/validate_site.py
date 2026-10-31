#!/usr/bin/env python3
"""Validate Grav page routes, local Markdown/HTML links, media, and review metadata."""

from __future__ import annotations

import argparse
import html.parser
import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE_ROOT = REPO_ROOT / "user/pages"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_VALUE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$")
NUMERIC_PREFIX = re.compile(r"^\d+\.")
ASSET_SUFFIXES = {
    ".avif",
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".odg",
    ".odp",
    ".ods",
    ".odt",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
    ".woff",
    ".woff2",
}


class HtmlLinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_name = "src" if tag in {"img", "iframe", "source", "video", "audio"} else "href"
        attr_value = dict(attrs).get(attr_name)
        if attr_value:
            self.targets.append(attr_value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate local Grav pages and routes")
    parser.add_argument(
        "--changed-files-file",
        type=Path,
        help="Optional newline-separated changed files; visible pages must be approved",
    )
    return parser.parse_args()


def route_for_page(md_file: Path) -> str:
    parts = list(md_file.parent.relative_to(PAGE_ROOT).parts)
    if not parts:
        return "/"

    original_first = parts[0]
    parts = [NUMERIC_PREFIX.sub("", part) for part in parts]
    if original_first == "01.home":
        parts = ["home", *parts[1:]]
        if len(parts) == 1:
            return "/"

    return "/" + "/".join(parts)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    lines = text.splitlines()
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}, text

    values: dict[str, str] = {}
    for line in lines[1:end]:
        match = FRONTMATTER_VALUE.match(line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip("'\"")
    return values, "\n".join(lines[end + 1 :])


def collect_targets(text: str) -> list[str]:
    targets = MARKDOWN_LINK.findall(text)
    parser = HtmlLinkParser()
    parser.feed(text)
    return targets + parser.targets


def local_file_exists(url_path: str, source_file: Path, route_map: dict[str, Path]) -> bool:
    decoded = unquote(url_path)

    if decoded.startswith("/user/"):
        return (REPO_ROOT / decoded.lstrip("/")).is_file()

    if not decoded.startswith("/"):
        return (source_file.parent / decoded).is_file()

    image_marker = "/images/"
    if image_marker in decoded:
        page_route, asset_path = decoded.split(image_marker, 1)
        page_folder = route_map.get(page_route.rstrip("/"))
        if page_folder:
            return (page_folder / "images" / asset_path).is_file()

    return False


def normalize_local_route(url_path: str, source_file: Path, route_map: dict[str, Path]) -> str:
    path = unquote(url_path)
    if path.startswith("/"):
        return path.rstrip("/") or "/"

    source_route = route_for_page(source_file)
    base = source_route if source_route == "/" else posixpath.dirname(source_route)
    return posixpath.normpath(posixpath.join(base, path)).rstrip("/") or "/"


def validate_changed_pages(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for changed in files:
        path = changed if changed.is_absolute() else REPO_ROOT / changed
        if not path.is_file() or path.suffix.lower() != ".md" or "user/pages" not in path.parts:
            continue

        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        visible = frontmatter.get("visible", "true").lower() == "true"
        if not visible or "source_url" not in frontmatter:
            continue

        relative = path.relative_to(REPO_ROOT)
        if frontmatter.get("status", "").lower() != "approved":
            errors.append(f"{relative}: visible page must have status: approved before merge")
        if not frontmatter.get("reviewed_by"):
            errors.append(f"{relative}: visible page needs reviewed_by metadata")
        if not frontmatter.get("reviewed_at"):
            errors.append(f"{relative}: visible page needs reviewed_at metadata")
    return errors


def main() -> int:
    args = parse_args()
    pages = sorted(PAGE_ROOT.rglob("default.md"))
    routes: dict[str, list[Path]] = {}
    route_map: dict[str, Path] = {}
    for page in pages:
        route = route_for_page(page)
        routes.setdefault(route, []).append(page)
        route_map[route] = page.parent
    route_map["/home"] = PAGE_ROOT / "01.home"

    collisions = {route: paths for route, paths in routes.items() if len(paths) > 1}
    broken: list[str] = []

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = parse_frontmatter(text)
        lead_image = frontmatter.get("lead_image")
        if lead_image and not (page.parent / lead_image).is_file():
            broken.append(f"{page.relative_to(REPO_ROOT)}: missing lead_image {lead_image}")

        redirect = frontmatter.get("redirect", "").strip()
        if redirect:
            redirect_url = urlsplit(redirect)
            if redirect_url.scheme not in {"http", "https"}:
                redirect_route = redirect_url.path.rstrip("/") or "/"
                if redirect_route not in routes and redirect_route != "/home":
                    broken.append(f"{page.relative_to(REPO_ROOT)}: unknown redirect target {redirect}")

        for target in collect_targets(body):
            parsed = urlsplit(target.strip().strip("<>"))
            if parsed.scheme.lower() in {"http", "https", "mailto", "tel", "data"}:
                continue
            path = parsed.path
            if not path or path == "#":
                continue
            if path.lower().endswith(tuple(ASSET_SUFFIXES)):
                if not local_file_exists(path, page, route_map):
                    broken.append(f"{page.relative_to(REPO_ROOT)}: missing local asset {target}")
                continue
            route = normalize_local_route(path, page, route_map)
            if route not in routes and route != "/home":
                broken.append(f"{page.relative_to(REPO_ROOT)}: unknown local route {target}")

    approval_errors: list[str] = []
    if args.changed_files_file:
        changed_files = [
            Path(line.strip())
            for line in args.changed_files_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        approval_errors = validate_changed_pages(changed_files)

    print(f"PAGES={len(pages)}")
    print(f"ROUTE_COLLISIONS={len(collisions)}")
    print(f"BROKEN_LOCAL_REFERENCES={len(broken)}")
    print(f"CHANGED_PAGE_REVIEW_ERRORS={len(approval_errors)}")

    for route, paths in sorted(collisions.items()):
        print(f"COLLISION {route}: {', '.join(str(p.relative_to(REPO_ROOT)) for p in paths)}")
    for error in broken:
        print(f"BROKEN {error}")
    for error in approval_errors:
        print(f"REVIEW {error}")

    if collisions or broken or approval_errors:
        print("SITE_VALIDATION=FAILED")
        return 1

    print("SITE_VALIDATION=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
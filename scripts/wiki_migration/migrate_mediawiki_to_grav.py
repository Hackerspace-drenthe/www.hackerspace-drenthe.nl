#!/usr/bin/env python3
"""Migrate MediaWiki XML content pages into Grav wiki pages.

Scope choices implemented by design:
- Include only main namespace content pages (ns == 0)
- Exclude all known management/system namespaces
- Convert page body to Markdown-ish text suitable for editorial review
- Keep migrated pages in draft state for validation/correction before go-live

Usage example:
  python3 scripts/wiki_migration/migrate_mediawiki_to_grav.py \
    --xml /path/to/wiki-export.xml \
    --out-root user/pages/08.wiki \
    --source-base-url https://wiki.hackerspace-drenthe.nl/wiki \
    --media-dir /path/to/wiki-images
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict
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
    "form",
}

FILE_PREFIXES = {"file", "image", "bestand", "bestands"}


@dataclass
class ExportPage:
    title: str
    namespace: int
    text: str


@dataclass
class MigratedPage:
    source_title: str
    source_url: str
    route: str
    folder: Path
    image_refs: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate MediaWiki XML into Grav wiki pages")
    parser.add_argument("--xml", required=True, help="Path to MediaWiki XML export")
    parser.add_argument("--out-root", required=True, help="Target Grav wiki folder, e.g. user/pages/08.wiki")
    parser.add_argument(
        "--source-base-url",
        default="https://wiki.hackerspace-drenthe.nl/wiki",
        help="Base URL for source links in frontmatter",
    )
    parser.add_argument(
        "--media-dir",
        default="",
        help="Optional directory containing exported wiki media files to copy locally",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without writing files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing default.md files under out-root",
    )
    return parser.parse_args()


def strip_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_slug(value: str) -> str:
    value = value.replace("_", " ").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9\-/ ]+", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    value = value.strip("-/")
    return value or "page"


def title_to_route(title: str, route_base: str) -> str:
    title_part, _, anchor = title.partition("#")
    segments = [normalize_slug(seg) for seg in title_part.split("/") if seg.strip()]
    route = route_base.rstrip("/") + "/" + "/".join(segments)
    if anchor.strip():
        route += "#" + normalize_slug(anchor)
    return route


def source_url_for_title(base_url: str, title: str) -> str:
    title = title.replace(" ", "_")
    return base_url.rstrip("/") + "/" + urllib.parse.quote(title)


def derive_route_base_from_out_root(out_root: Path) -> str:
    name = out_root.name
    route_name = re.sub(r"^\d+\.", "", name)
    route_name = normalize_slug(route_name)
    return "/" + route_name


def parse_export_pages(xml_path: Path) -> list[ExportPage]:
    pages: list[ExportPage] = []
    current_title = ""
    current_ns = 0
    current_text = ""

    context = ET.iterparse(xml_path, events=("start", "end"))
    for event, elem in context:
        tag = strip_tag(elem.tag)

        if event == "end" and tag == "title":
            current_title = elem.text or ""
        elif event == "end" and tag == "ns":
            text = (elem.text or "0").strip()
            current_ns = int(text) if text.isdigit() else 0
        elif event == "end" and tag == "text":
            current_text = elem.text or ""
        elif event == "end" and tag == "page":
            pages.append(ExportPage(title=current_title, namespace=current_ns, text=current_text))
            current_title = ""
            current_ns = 0
            current_text = ""
            elem.clear()

    return pages


def should_include_content_page(page: ExportPage) -> tuple[bool, str]:
    if page.namespace != 0:
        return False, f"ns={page.namespace}"

    if ":" in page.title:
        prefix = page.title.split(":", 1)[0].strip().lower()
        if prefix in EXCLUDED_NAMESPACE_PREFIXES:
            return False, f"namespace-prefix={prefix}"

    return True, ""


def is_wiki_option(part: str) -> bool:
    value = part.strip().lower()
    option_prefixes = (
        "thumb",
        "thumbnail",
        "right",
        "left",
        "center",
        "none",
        "border",
        "frameless",
        "frame",
        "upright",
        "alt=",
        "link=",
        "class=",
        "px",
    )
    return value.startswith(option_prefixes) or value.endswith("px")


def sanitize_filename(filename: str) -> str:
    filename = filename.strip().replace(" ", "_")
    filename = filename.replace("/", "_")
    return filename


def convert_wikitext_to_markdown(text: str, route_base: str) -> tuple[str, list[str]]:
    image_refs: list[str] = []
    local_media_map: dict[str, str] = {}

    text = text.replace("\r\n", "\n")
    text = re.sub(r"__TOC__|__NOTOC__|__FORCETOC__", "", text, flags=re.IGNORECASE)

    # Strip simple templates in repeated passes. Nested templates are simplified, then removed.
    for _ in range(8):
        updated = re.sub(r"\{\{[^{}]*\}\}", "", text)
        if updated == text:
            break
        text = updated

    # Convert syntaxhighlight blocks into fenced code blocks.
    text = re.sub(
        r"<syntaxhighlight\s+lang=[\"']?([a-zA-Z0-9_+-]+)[\"']?\s*>(.*?)</syntaxhighlight>",
        lambda m: f"\n```{m.group(1)}\n{m.group(2).strip()}\n```\n",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def heading_repl(match: re.Match[str]) -> str:
        marker = match.group(1)
        title = match.group(2).strip()
        level = min(6, max(1, len(marker) - 1))
        return "#" * level + " " + title

    text = re.sub(r"^(={2,6})\s*(.*?)\s*\1\s*$", heading_repl, text, flags=re.MULTILINE)

    text = re.sub(r"'''''(.*?)'''''", r"***\1***", text)
    text = re.sub(r"'''(.*?)'''", r"**\1**", text)
    text = re.sub(r"''(.*?)''", r"*\1*", text)

    def internal_link_repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        parts = [p.strip() for p in raw.split("|") if p is not None]
        if not parts:
            return ""

        target = parts[0]
        label = parts[-1] if len(parts) > 1 else target

        if target.startswith("#"):
            return f"[{label}]({target})"

        if ":" in target:
            prefix = target.split(":", 1)[0].strip().lower()
            if prefix in FILE_PREFIXES:
                src_name = sanitize_filename(target.split(":", 1)[1])
                for option in reversed(parts[1:]):
                    if not is_wiki_option(option):
                        label = option.strip()
                        break
                local_name = local_media_map.get(src_name)
                if local_name is None:
                    local_name = src_name
                    local_media_map[src_name] = local_name
                image_refs.append(local_name)
                alt_text = label if label and not is_wiki_option(label) else Path(local_name).stem
                return f"![{alt_text}](images/{local_name})"

            if prefix in EXCLUDED_NAMESPACE_PREFIXES:
                return label

        route = title_to_route(target, route_base)
        label = label.replace("_", " ").strip()
        return f"[{label}]({route})"

    text = re.sub(r"\[\[([^\[\]]+)\]\]", internal_link_repl, text)

    text = re.sub(
        r"\[(https?://[^\s\]]+)\s+([^\]]+)\]",
        lambda m: f"[{m.group(2).strip()}]({m.group(1).strip()})",
        text,
    )

    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<ref[^>]*/\s*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text, image_refs


def ensure_wiki_root_page(out_root: Path, dry_run: bool) -> None:
    root_md = out_root / "default.md"
    if root_md.exists():
        return

    content = """---
title: Wiki
menu: Wiki
visible: true
status: approved
reviewed_by: migration-script
reviewed_at: ""
source_title: Wiki Root
source_url: local
---

# Wiki

Deze sectie bevat gemigreerde wiki-content. Pagina's staan in review totdat ze zijn goedgekeurd voor livegang.
"""

    if dry_run:
        print(f"DRY-RUN: would create {root_md}")
        return

    out_root.mkdir(parents=True, exist_ok=True)
    root_md.write_text(content, encoding="utf-8")


def write_grav_page(
    out_root: Path,
    page: ExportPage,
    markdown: str,
    image_refs: list[str],
    route_base: str,
    source_base_url: str,
    overwrite: bool,
    dry_run: bool,
) -> MigratedPage | None:
    route = title_to_route(page.title, route_base)
    relative_route = route[len(route_base) :].strip("/")
    route_segments = [seg for seg in relative_route.split("/") if seg]
    page_folder = out_root.joinpath(*route_segments)
    default_md = page_folder / "default.md"

    if default_md.exists() and not overwrite:
        print(f"SKIP existing page (use --overwrite): {default_md}")
        return None

    source_url = source_url_for_title(source_base_url, page.title)
    frontmatter = (
        "---\n"
        f"title: \"{page.title.replace('"', '\\"')}\"\n"
        f"menu: \"{page.title.replace('"', '\\"')}\"\n"
        "visible: true\n"
        "status: draft\n"
        "reviewed_by: \"\"\n"
        "reviewed_at: \"\"\n"
        f"source_title: \"{page.title.replace('"', '\\"')}\"\n"
        f"source_url: \"{source_url}\"\n"
        "---\n\n"
    )
    content = frontmatter + markdown

    if dry_run:
        print(f"DRY-RUN: would write {default_md}")
    else:
        page_folder.mkdir(parents=True, exist_ok=True)
        default_md.write_text(content, encoding="utf-8")
        if image_refs:
            (page_folder / "images").mkdir(exist_ok=True)

    return MigratedPage(
        source_title=page.title,
        source_url=source_url,
        route=route,
        folder=page_folder,
        image_refs=image_refs,
    )


def build_media_index(media_dir: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    for path in media_dir.rglob("*"):
        if path.is_file():
            index[path.name.lower()].append(path)
    return index


def copy_page_media(
    migrated_pages: list[MigratedPage],
    media_dir: Path,
    dry_run: bool,
) -> tuple[int, list[str]]:
    media_index = build_media_index(media_dir)
    copied = 0
    missing: list[str] = []

    for page in migrated_pages:
        if not page.image_refs:
            continue

        for image_name in page.image_refs:
            candidates = [
                image_name,
                image_name.replace("_", " "),
                image_name.replace(" ", "_"),
            ]

            source_path = None
            for candidate in candidates:
                matches = media_index.get(candidate.lower())
                if matches:
                    source_path = matches[0]
                    break

            if source_path is None:
                missing.append(f"{page.source_title} -> {image_name}")
                continue

            target = page.folder / "images" / image_name
            if dry_run:
                print(f"DRY-RUN: would copy {source_path} -> {target}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target)
            copied += 1

    return copied, missing


def write_reports(out_root: Path, route_base: str, migrated: list[MigratedPage], excluded: list[dict[str, str]], dry_run: bool) -> None:
    report_dir = out_root / "_migration"
    if dry_run:
        print(f"DRY-RUN: would write report files under {report_dir}")
        return

    report_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "migrated_count": len(migrated),
        "excluded_count": len(excluded),
        "route_base": route_base,
        "migrated_routes": [m.route for m in migrated],
        "excluded": excluded,
    }

    (report_dir / "migration_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    with (report_dir / "redirects.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source_title", "source_url", "target_route"])
        for page in migrated:
            writer.writerow([page.source_title, page.source_url, page.route])


def main() -> int:
    args = parse_args()

    xml_path = Path(args.xml)
    out_root = Path(args.out_root)
    media_dir = Path(args.media_dir) if args.media_dir else None

    if not xml_path.exists():
        raise SystemExit(f"XML export not found: {xml_path}")

    route_base = derive_route_base_from_out_root(out_root)
    pages = parse_export_pages(xml_path)

    included_pages: list[ExportPage] = []
    excluded_pages: list[dict[str, str]] = []

    for page in pages:
        include, reason = should_include_content_page(page)
        if include:
            included_pages.append(page)
        else:
            excluded_pages.append({"title": page.title, "reason": reason})

    ensure_wiki_root_page(out_root, args.dry_run)

    migrated_pages: list[MigratedPage] = []
    for page in included_pages:
        markdown, image_refs = convert_wikitext_to_markdown(page.text or "", route_base)
        migrated = write_grav_page(
            out_root=out_root,
            page=page,
            markdown=markdown,
            image_refs=image_refs,
            route_base=route_base,
            source_base_url=args.source_base_url,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
        if migrated is not None:
            migrated_pages.append(migrated)

    copied_images = 0
    missing_images: list[str] = []

    if media_dir is not None:
        if not media_dir.exists():
            print(f"WARNING: media directory not found: {media_dir}")
        else:
            copied_images, missing_images = copy_page_media(migrated_pages, media_dir, args.dry_run)

    write_reports(out_root, route_base, migrated_pages, excluded_pages, args.dry_run)

    print(f"TOTAL_PAGES_IN_EXPORT={len(pages)}")
    print(f"INCLUDED_CONTENT_PAGES={len(included_pages)}")
    print(f"EXCLUDED_PAGES={len(excluded_pages)}")
    print(f"MIGRATED_PAGES={len(migrated_pages)}")
    print(f"COPIED_IMAGES={copied_images}")
    print(f"MISSING_IMAGES={len(missing_images)}")

    if missing_images:
        print("Missing media references:")
        for item in missing_images[:200]:
            print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Maintain child-page indexes in parent default.md files under wiki root.

Rule implemented:
- If a folder has a default.md and direct child folders contain Markdown files,
  parent default.md receives/updates an auto-generated index block with links.

The generated block is idempotent and bounded by markers:
  <!-- AUTO-INDEX:START -->
  ...
  <!-- AUTO-INDEX:END -->
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

START_MARKER = "<!-- AUTO-INDEX:START -->"
END_MARKER = "<!-- AUTO-INDEX:END -->"
AUTO_INDEX_PATTERN = re.compile(
    re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?",
    flags=re.DOTALL,
)


@dataclass
class MdDoc:
    path: Path
    frontmatter: dict[str, str]
    frontmatter_text: str
    body: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index child markdown pages in parent default.md files")
    parser.add_argument("--wiki-root", required=True, help="Wiki root folder, e.g. user/pages/08.wiki")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    return parser.parse_args()


def normalize_slug(value: str) -> str:
    value = value.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9\-/]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-/")


def derive_route_base(wiki_root: Path) -> str:
    name = re.sub(r"^\d+\.", "", wiki_root.name)
    return "/" + normalize_slug(name)


def split_frontmatter(md_text: str) -> tuple[str, str, dict[str, str]]:
    if not md_text.startswith("---\n"):
        return "", md_text, {}

    lines = md_text.splitlines()
    end_index = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index == -1:
        return "", md_text, {}

    fm_lines = lines[1:end_index]
    body = "\n".join(lines[end_index + 1 :])
    if not body.endswith("\n"):
        body += "\n"

    fm_dict: dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm_dict[key.strip()] = value.strip().strip('"')

    fm_text = "---\n" + "\n".join(fm_lines) + "\n---\n"
    return fm_text, body, fm_dict


def read_doc(md_path: Path) -> MdDoc:
    text = md_path.read_text(encoding="utf-8")
    fm_text, body, fm_dict = split_frontmatter(text)
    return MdDoc(path=md_path, frontmatter=fm_dict, frontmatter_text=fm_text, body=body)


def page_label_for_markdown(md_path: Path) -> str:
    doc = read_doc(md_path)
    label = doc.frontmatter.get("menu") or doc.frontmatter.get("title")
    if label:
        return label.strip()
    stem = md_path.stem
    return stem.replace("-", " ").replace("_", " ").strip() or md_path.parent.name


def route_for_markdown(md_path: Path, wiki_root: Path, route_base: str) -> str:
    rel_dir = md_path.parent.relative_to(wiki_root).as_posix()
    if rel_dir == ".":
        rel_dir = ""

    if md_path.name == "default.md":
        suffix = rel_dir
    else:
        part = normalize_slug(md_path.stem)
        suffix = f"{rel_dir}/{part}" if rel_dir else part

    suffix = suffix.strip("/")
    return route_base if not suffix else f"{route_base}/{suffix}"


def collect_child_links(parent_dir: Path, wiki_root: Path, route_base: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    for child in sorted(parent_dir.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("_"):
            continue

        md_files = sorted(child.glob("*.md"), key=lambda p: (p.name != "default.md", p.name.lower()))
        for md_file in md_files:
            route = route_for_markdown(md_file, wiki_root, route_base)
            if route in seen:
                continue
            seen.add(route)
            label = page_label_for_markdown(md_file)
            links.append((label, route))

    links.sort(key=lambda item: item[0].lower())
    return links


def build_index_block(links: list[tuple[str, str]]) -> str:
    lines = [START_MARKER, "## Subpages", ""]
    for label, route in links:
        lines.append(f"- [{label}]({route})")
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def body_without_auto_index(body: str) -> str:
    cleaned = AUTO_INDEX_PATTERN.sub("", body)
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned


def text_above_auto_index(body: str) -> str:
    marker_pos = body.find(START_MARKER)
    if marker_pos == -1:
        return body
    return body[:marker_pos]


def is_already_mentioned(text: str, label: str, route: str) -> bool:
    text_folded = text.casefold()
    route_folded = route.casefold()

    if route_folded in text_folded:
        return True
    if route_folded.rstrip("/") in text_folded:
        return True

    # Also skip indexing when the page label is already mentioned in prose.
    return label.casefold() in text_folded


def filter_links_not_mentioned(links: list[tuple[str, str]], body: str) -> tuple[list[tuple[str, str]], int]:
    above_text = text_above_auto_index(body)
    filtered: list[tuple[str, str]] = []
    skipped = 0

    for label, route in links:
        if is_already_mentioned(above_text, label, route):
            skipped += 1
            continue
        filtered.append((label, route))

    return filtered, skipped


def upsert_index_block(body: str, new_block: str) -> str:
    pattern = AUTO_INDEX_PATTERN

    if pattern.search(body):
        updated = pattern.sub(new_block, body)
    else:
        body = body.rstrip() + "\n\n" if body.strip() else ""
        updated = body + new_block

    if not updated.endswith("\n"):
        updated += "\n"
    return updated


def write_doc(doc: MdDoc, new_body: str, dry_run: bool) -> bool:
    new_text = doc.frontmatter_text + new_body if doc.frontmatter_text else new_body
    old_text = doc.path.read_text(encoding="utf-8")
    if new_text == old_text:
        return False

    if dry_run:
        print(f"DRY-RUN: would update {doc.path}")
    else:
        doc.path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()
    wiki_root = Path(args.wiki_root)

    if not wiki_root.exists():
        raise SystemExit(f"wiki root not found: {wiki_root}")

    route_base = derive_route_base(wiki_root)
    updated_files = 0
    indexed_parents = 0
    total_links = 0
    skipped_already_mentioned = 0

    for parent_md in sorted(wiki_root.rglob("default.md")):
        parent_dir = parent_md.parent
        all_links = collect_child_links(parent_dir, wiki_root, route_base)
        if not all_links:
            continue

        doc = read_doc(parent_md)
        links, skipped = filter_links_not_mentioned(all_links, doc.body)
        skipped_already_mentioned += skipped
        total_links += len(links)

        clean_body = body_without_auto_index(doc.body)
        if links:
            indexed_parents += 1
            block = build_index_block(links)
            new_body = upsert_index_block(clean_body, block)
        else:
            new_body = clean_body

        if write_doc(doc, new_body, args.dry_run):
            updated_files += 1

    print(f"INDEXED_PARENTS={indexed_parents}")
    print(f"TOTAL_CHILD_LINKS={total_links}")
    print(f"SKIPPED_ALREADY_MENTIONED={skipped_already_mentioned}")
    print(f"UPDATED_FILES={updated_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

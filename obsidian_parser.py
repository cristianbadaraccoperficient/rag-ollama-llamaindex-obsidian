import re
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([\w/\-]+)")


def extract_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}
        return meta, text[match.end():]
    return {}, text


def resolve_wikilinks(text: str) -> str:
    return WIKILINK_RE.sub(lambda m: m.group(2) if m.group(2) else m.group(1), text)


def normalize_tags(text: str) -> str:
    return TAG_RE.sub(lambda m: m.group(1).replace("/", " ").replace("-", " "), text)


def clean_obsidian_text(raw: str) -> tuple[str, dict]:
    meta, body = extract_frontmatter(raw)
    body = resolve_wikilinks(body)
    body = normalize_tags(body)
    return body, meta


def obsidian_file_metadata(filepath: str) -> dict:
    path = Path(filepath)
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"file_name": path.name, "file_path": str(path), "note_title": path.stem, "tags": ""}

    meta, _ = extract_frontmatter(raw)

    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []

    result = {
        "file_name": path.name,
        "file_path": str(path),
        "note_title": path.stem,
        "tags": ", ".join(str(t) for t in tags),
    }
    for k, v in meta.items():
        if k not in result:
            result[k] = str(v)

    return result

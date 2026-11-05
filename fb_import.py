"""Importers that turn Facebook data exports and browser bookmark files into library entries.

Facebook does not publish an API for a user's saved items, and this app never signs in to an
account. Instead it reads files the user can produce themselves:

* Facebook "Download Your Information" (DYI) zip export - saved items JSON plus any media files
  the export contains.
* Browser bookmark exports (Chrome/Edge/Firefox/Safari/DuckDuckGo) in Netscape bookmark HTML.
"""

from __future__ import annotations

import io
import json
import posixpath
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunsplit

FACEBOOK_HOSTS = ("facebook.com", "fb.watch", "fb.com")
IMAGE_TYPES = {"jpg", "jpeg", "png", "gif", "webp", "heic", "bmp"}
VIDEO_TYPES = {"mp4", "mov", "m4v", "webm", "avi", "mkv"}

TIMESTAMP_KEYS = ("timestamp", "creation_timestamp", "add_date", "created_at")
TITLE_KEYS = ("title", "name")
URL_KEYS = ("url", "href", "external_context")

# Subdomains that serve the same page as www.facebook.com.
CANONICAL_HOST_ALIASES = {
    "m.facebook.com": "www.facebook.com",
    "mobile.facebook.com": "www.facebook.com",
    "web.facebook.com": "www.facebook.com",
    "touch.facebook.com": "www.facebook.com",
    "free.facebook.com": "www.facebook.com",
    "facebook.com": "www.facebook.com",
}

# Tracking/attribution params Facebook appends; they never identify the content itself.
TRACKING_QUERY_KEYS = {
    "__cft__",
    "__tn__",
    "__xts__",
    "__xt",
    "_rdr",
    "_rdc",
    "rdid",
    "rdr",
    "rdrr",
    "ref",
    "refsrc",
    "refid",
    "referrer",
    "mibextid",
    "mbid",
    "sfnsn",
    "eav",
    "paipv",
    "hc_ref",
    "fref",
    "locale",
    "acontext",
    "notif_id",
    "notif_t",
    "comment_tracking",
    "extid",
    "share_url",
    "fbclid",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
}


def is_facebook_url(url: str) -> bool:
    """Return True for http(s) links on a Facebook-owned domain."""
    if not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.lower().split(":")[0]
    if not host:
        return False
    return any(host == candidate or host.endswith("." + candidate) for candidate in FACEBOOK_HOSTS)


def media_kind(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension in IMAGE_TYPES:
        return "image"
    if extension in VIDEO_TYPES:
        return "video"
    return "file"


def _is_tracking_key(key: str) -> bool:
    """True for tracking params, including indexed forms like ``__cft__[0]``."""
    lowered = key.lower()
    base = lowered.split("[", 1)[0]
    return base in TRACKING_QUERY_KEYS or base.startswith("utm_") or lowered.startswith("__")


def normalize_facebook_url(url: str) -> str:
    """Return a stable identity for a Facebook link.

    Two links to the same post differ in subdomain (``m.``/``web.``), trailing slashes,
    fragment, and dozens of tracking params that Facebook appends on share. Sync compares
    normalized URLs so a re-import updates an existing entry instead of adding a duplicate.
    """
    if not isinstance(url, str):
        return ""
    raw = url.strip()
    if not is_facebook_url(raw):
        return raw
    parsed = urlparse(raw)
    host = parsed.netloc.lower().split(":")[0]
    host = CANONICAL_HOST_ALIASES.get(host, host)
    if host.endswith(".fb.com") or host == "fb.com":
        host = "www.facebook.com"

    kept = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if not _is_tracking_key(key)
    ]
    kept.sort()
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(kept)
    return urlunsplit(("https", host, path, query, ""))


@dataclass
class ImportedEntry:
    """One saved Facebook item recovered from an export."""

    url: str
    title: str
    category: str
    timestamp: int | None = None
    media_members: list[str] = field(default_factory=list)
    source_member: str = ""
    media: list[dict] = field(default_factory=list)

    @property
    def needs_media(self) -> bool:
        return not self.media

    @property
    def url_key(self) -> str:
        """Normalized identity used to match this entry against the existing library."""
        return normalize_facebook_url(self.url)


@dataclass
class ImportResult:
    entries: list[ImportedEntry] = field(default_factory=list)
    media_copied: int = 0
    missing_media: int = 0
    json_files_read: int = 0

    @property
    def with_media(self) -> int:
        return sum(1 for entry in self.entries if entry.media)


def sync_into_library(
    items: list[dict],
    entries: list[ImportedEntry],
    fallback_category: str,
    now: str | None = None,
) -> tuple[int, int]:
    """Merge imported entries into ``items`` in place, returning ``(added, updated)``.

    Entries are matched on the normalized Facebook URL, so re-running an import against a newer
    export behaves like a sync: existing rows are updated rather than duplicated. Import-owned
    fields (title, category, media) refresh; user-owned fields (notes) are preserved, and media
    already stored is not re-copied.
    """
    stamp = now or datetime.now(timezone.utc).isoformat()

    by_key: dict[str, dict] = {}
    for item in items:
        by_key.setdefault(normalize_facebook_url(item.get("url", "")), item)

    added = 0
    updated = 0
    for entry in entries:
        key = entry.url_key
        existing = by_key.get(key)
        category = entry.category or fallback_category

        if existing is None:
            new_item = {
                "id": uuid.uuid4().hex,
                "title": entry.title or entry.url,
                "url": entry.url,
                "category": category,
                "notes": "",
                "media": list(entry.media),
                "created_at": _created_at_from_timestamp(entry.timestamp),
                "synced_at": stamp,
            }
            items.insert(0, new_item)
            by_key[key] = new_item
            added += 1
            continue

        changed = False
        if entry.title and entry.title != existing.get("title"):
            existing["title"] = entry.title
            changed = True
        if category and category != existing.get("category"):
            existing["category"] = category
            changed = True
        if entry.media:
            known = {media.get("original_name") for media in existing.get("media", [])}
            fresh = [media for media in entry.media if media.get("original_name") not in known]
            if fresh:
                existing.setdefault("media", []).extend(fresh)
                changed = True
        if changed:
            updated += 1
        existing["synced_at"] = stamp

    return added, updated


def _created_at_from_timestamp(timestamp: int | None) -> str:
    if timestamp:
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _string_title(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        inner = value.get("title")
        if isinstance(inner, str) and inner.strip():
            return inner.strip()
    return None


def _record_title(record: dict) -> str | None:
    for key in TITLE_KEYS:
        title = _string_title(record.get(key))
        if title:
            return title
    return None


def _record_timestamp(record: dict) -> int | None:
    for key in TIMESTAMP_KEYS:
        value = record.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def _first_facebook_url(node: object, depth: int = 0) -> str | None:
    if depth > 12:
        return None
    if isinstance(node, str):
        return node.strip() if is_facebook_url(node) else None
    if isinstance(node, dict):
        for key in URL_KEYS:
            if key in node:
                found = _first_facebook_url(node[key], depth + 1)
                if found:
                    return found
        for value in node.values():
            found = _first_facebook_url(value, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _first_facebook_url(value, depth + 1)
            if found:
                return found
    return None


def _collect_media_refs(node: object, refs: list[str], depth: int = 0) -> None:
    if depth > 12:
        return
    if isinstance(node, dict):
        uri = node.get("uri")
        if isinstance(uri, str) and uri and not uri.startswith(("http://", "https://", "data:")):
            refs.append(uri)
        for value in node.values():
            _collect_media_refs(value, refs, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _collect_media_refs(value, refs, depth + 1)


def _looks_like_record(node: dict) -> bool:
    has_timestamp = any(key in node for key in TIMESTAMP_KEYS)
    has_payload = any(key in node for key in ("attachments", "url", "href", "title", "name"))
    return has_timestamp and has_payload


def _walk_records(node: object, out: list[dict], depth: int = 0) -> None:
    if depth > 16:
        return
    if isinstance(node, dict):
        if _looks_like_record(node):
            out.append(node)
            return
        for value in node.values():
            _walk_records(value, out, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _walk_records(value, out, depth + 1)


def _fallback_urls(node: object, out: list[str], depth: int = 0) -> None:
    """Last resort: collect every Facebook URL in the file when no records are recognised."""
    if depth > 16:
        return
    if isinstance(node, str):
        if is_facebook_url(node):
            out.append(node.strip())
    elif isinstance(node, dict):
        for value in node.values():
            _fallback_urls(value, out, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _fallback_urls(value, out, depth + 1)


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if path:
        return path.split("/")[-1].replace("-", " ").replace("_", " ")[:80] or parsed.netloc
    return parsed.netloc or url


def parse_saved_items_json(text: str, category: str = "Imported from Facebook") -> list[ImportedEntry]:
    """Parse one saved-items JSON file from a Facebook export.

    Handles the common shapes (``saved_items_and_collections.json``, ``your_saved_items.json``)
    and falls back to sweeping every Facebook URL so unusual export versions still import.
    """
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []

    records: list[dict] = []
    _walk_records(data, records)

    entries: list[ImportedEntry] = []
    seen: set[str] = set()
    for record in records:
        payload = record.get("attachments") or record.get("external_context") or record
        url = _first_facebook_url(payload) or _first_facebook_url(record)
        if not url:
            continue
        key = normalize_facebook_url(url)
        if key in seen:
            continue
        seen.add(key)
        refs: list[str] = []
        _collect_media_refs(payload, refs)
        entries.append(
            ImportedEntry(
                url=url,
                title=_record_title(record) or _title_from_url(url),
                category=category,
                timestamp=_record_timestamp(record),
                media_members=refs,
            )
        )
    if not entries:
        urls: list[str] = []
        _fallback_urls(data, urls)
        for url in urls:
            key = normalize_facebook_url(url)
            if key in seen:
                continue
            seen.add(key)
            entries.append(ImportedEntry(url=url, title=_title_from_url(url), category=category))

    return entries


def _collect_collections(node: object, out: dict[str, str], depth: int = 0) -> None:
    """Map normalized saved-item URL -> collection name when the export carries collections."""
    if depth > 12:
        return
    if isinstance(node, dict):
        name = _string_title(node.get("name")) or _string_title(node.get("title"))
        if name and any(key in node for key in ("items", "saved_items", "entries")):
            for key in ("items", "saved_items", "entries"):
                children = node.get(key)
                if isinstance(children, list):
                    for child in children:
                        url = _first_facebook_url(child)
                        if url:
                            out.setdefault(normalize_facebook_url(url), name)
        for value in node.values():
            _collect_collections(value, out, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _collect_collections(value, out, depth + 1)


def _saved_json_members(names: Iterable[str]) -> list[str]:
    json_names = [name for name in names if name.lower().endswith(".json")]
    matched = [name for name in json_names if "saved" in posixpath.basename(name).lower()]
    if matched:
        return matched
    return [name for name in json_names if "bookmark" in name.lower()]


def _resolve_member(names: set[str], json_member: str, ref: str) -> str | None:
    base = posixpath.dirname(json_member)
    for candidate in (
        posixpath.normpath(posixpath.join(base, ref)),
        posixpath.normpath(ref),
        posixpath.normpath(posixpath.join(base, unquote(ref))),
        posixpath.normpath(unquote(ref)),
    ):
        if candidate in names:
            return candidate
    return None


def import_facebook_export(zip_bytes: bytes, media_dir: Path, app_dir: Path) -> ImportResult:
    """Read a Facebook DYI zip export and copy referenced media into ``media_dir``."""
    result = ImportResult()
    media_dir.mkdir(parents=True, exist_ok=True)

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return result

    with archive:
        names = set(archive.namelist())
        members = _saved_json_members(names)
        if not members:
            return result

        collections: dict[str, str] = {}
        parsed: list[ImportedEntry] = []

        for member in members:
            try:
                text = archive.read(member).decode("utf-8", "replace")
            except KeyError:
                continue
            result.json_files_read += 1
            try:
                _collect_collections(json.loads(text), collections)
            except json.JSONDecodeError:
                pass
            for entry in parse_saved_items_json(text):
                entry.source_member = member
                collection = collections.get(normalize_facebook_url(entry.url))
                if collection:
                    entry.category = collection
                parsed.append(entry)

        deduped: dict[str, ImportedEntry] = {}
        for entry in parsed:
            deduped.setdefault(entry.url_key, entry)

        for entry in deduped.values():
            media: list[dict] = []
            for ref in entry.media_members:
                member_name = _resolve_member(names, entry.source_member, ref)
                if member_name is None:
                    result.missing_media += 1
                    continue
                try:
                    data = archive.read(member_name)
                except KeyError:
                    result.missing_media += 1
                    continue
                suffix = Path(member_name).suffix.lower()
                destination = media_dir / f"{uuid.uuid4().hex}{suffix}"
                destination.write_bytes(data)
                result.media_copied += 1
                media.append(
                    {
                        "original_name": posixpath.basename(member_name),
                        "path": str(destination.relative_to(app_dir)),
                        "kind": media_kind(member_name),
                        "size": len(data),
                    }
                )
            entry.media_members = []
            entry.media = media
            result.entries.append(entry)

    return result


class _BookmarkHTMLParser(HTMLParser):
    """Parse Netscape bookmark HTML, tracking folder names for categories."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.folders: list[str] = []
        self._pending_folder: str | None = None
        self._dl_pushed: list[bool] = []
        self._capturing: str | None = None
        self._buffer: list[str] = []
        self._href: str | None = None
        self._add_date: str | None = None
        self.entries: list[tuple[str, str, str, int | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value for key, value in attrs}
        if tag == "h3":
            self._capturing = "folder"
            self._buffer = []
        elif tag == "a":
            self._capturing = "link"
            self._buffer = []
            self._href = attributes.get("href")
            self._add_date = attributes.get("add_date")
        elif tag == "dl":
            pushed = self._pending_folder is not None
            if pushed:
                self.folders.append(self._pending_folder or "Unsorted")
                self._pending_folder = None
            self._dl_pushed.append(pushed)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._capturing == "folder":
            self._pending_folder = "".join(self._buffer).strip() or "Unsorted"
            self._capturing = None
            self._buffer = []
        elif tag == "a" and self._capturing == "link":
            title = "".join(self._buffer).strip()
            add_date = int(self._add_date) if (self._add_date or "").isdigit() else None
            if self._href:
                self.entries.append((self._href, title, self.folders[-1] if self.folders else "", add_date))
            self._capturing = None
            self._buffer = []
        elif tag == "dl":
            pushed = self._dl_pushed.pop() if self._dl_pushed else False
            if pushed and self.folders:
                self.folders.pop()

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._buffer.append(data)


def parse_bookmarks_html(html_text: str, default_category: str = "Bookmarks") -> list[ImportedEntry]:
    """Return Facebook bookmark entries from a browser bookmark HTML export."""
    parser = _BookmarkHTMLParser()
    try:
        parser.feed(html_text)
    except Exception:  # malformed HTML should not crash the app
        pass

    entries: list[ImportedEntry] = []
    seen: set[str] = set()
    for href, title, folder, add_date in parser.entries:
        if not is_facebook_url(href):
            continue
        key = normalize_facebook_url(href)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            ImportedEntry(
                url=href.strip(),
                title=title or _title_from_url(href),
                category=folder or default_category,
                timestamp=add_date,
            )
        )
    return entries

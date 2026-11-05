import io
import json
import zipfile
from pathlib import Path

import pytest

from fb_import import (
    import_facebook_export,
    is_facebook_url,
    media_kind,
    parse_bookmarks_html,
    parse_saved_items_json,
)


def test_is_facebook_url_accepts_facebook_domains_only():
    assert is_facebook_url("https://www.facebook.com/some.post/123")
    assert is_facebook_url("https://fb.watch/abc123/")
    assert is_facebook_url("http://fb.com/groups/1")
    assert is_facebook_url("https://m.facebook.com/story.php?id=1")

    assert not is_facebook_url("https://evilfacebook.com/post")
    assert not is_facebook_url("https://facebook.com.evil.example/post")
    assert not is_facebook_url("javascript:alert(1)")
    assert not is_facebook_url("ftp://facebook.com/file")


def test_media_kind_classifies_images_videos_and_other_files():
    assert media_kind("photo.JPG") == "image"
    assert media_kind("clip.mov") == "video"
    assert media_kind("notes.txt") == "file"
    assert media_kind("noextension") == "file"


def test_parse_saved_items_json_reads_records_with_media_refs():
    payload = {
        "saved_saved_items": [
            {
                "timestamp": 1700000000,
                "title": "Great recipe",
                "attachments": [
                    {
                        "data": [
                            {
                                "external_context": {"url": "https://www.facebook.com/reel/12345"},
                                "media": {
                                    "uri": "your_activity_across_facebook/saved/photo_1.jpg",
                                    "creation_timestamp": 1700000000,
                                },
                            }
                        ]
                    }
                ],
            },
            {
                "timestamp": 1600000000,
                "title": 12345,
                "attachments": [
                    {"data": [{"external_context": {"url": "https://example.com/not-facebook"}}]}
                ],
            },
        ]
    }

    entries = parse_saved_items_json(json.dumps(payload))

    assert len(entries) == 1
    entry = entries[0]
    assert entry.url == "https://www.facebook.com/reel/12345"
    assert entry.title == "Great recipe"
    assert entry.timestamp == 1700000000
    assert entry.media_members == ["your_activity_across_facebook/saved/photo_1.jpg"]


def test_parse_saved_items_json_falls_back_to_url_sweep():
    payload = {"export": {"nested": ["https://www.facebook.com/watch/?v=999", "https://example.com"]}}

    entries = parse_saved_items_json(json.dumps(payload))

    assert [entry.url for entry in entries] == ["https://www.facebook.com/watch/?v=999"]


def test_parse_saved_items_json_ignores_invalid_json():
    assert parse_saved_items_json("not json at all") == []


def test_parse_bookmarks_html_uses_folders_as_categories():
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
  <DT><H3>Social</H3>
  <DL><p>
    <DT><A HREF="https://www.facebook.com/groups/42" ADD_DATE="1650000000">Group post</A>
    <DT><A HREF="https://example.com" ADD_DATE="1650000001">Not facebook</A>
    <DT><H3>Recipes</H3>
    <DL><p>
      <DT><A HREF="https://www.facebook.com/reel/77" ADD_DATE="1650000002">Reel</A>
    </DL><p>
  </DL><p>
  <DT><A HREF="https://fb.watch/top-level" ADD_DATE="1650000003">Top level</A>
</DL><p>
"""

    entries = parse_bookmarks_html(html)

    by_url = {entry.url: entry for entry in entries}
    assert set(by_url) == {
        "https://www.facebook.com/groups/42",
        "https://www.facebook.com/reel/77",
        "https://fb.watch/top-level",
    }
    assert by_url["https://www.facebook.com/groups/42"].category == "Social"
    assert by_url["https://www.facebook.com/reel/77"].category == "Recipes"
    assert by_url["https://www.facebook.com/groups/42"].title == "Group post"
    assert by_url["https://www.facebook.com/groups/42"].timestamp == 1650000000
    assert by_url["https://fb.watch/top-level"].category == "Bookmarks"


def test_import_facebook_export_copies_media_and_maps_collections(tmp_path):
    export_json = {
        "saved_saved_items": [
            {
                "timestamp": 1700000000,
                "title": "Trip",
                "attachments": [
                    {
                        "data": [
                            {
                                "external_context": {"url": "https://www.facebook.com/post/1"},
                                "media": {"uri": "media/photo_1.jpg"},
                            }
                        ]
                    }
                ],
            }
        ],
        "collections": [
            {
                "name": "Travel",
                "items": [{"attachments": [{"data": [{"external_context": {"url": "https://www.facebook.com/post/1"}}]}]}],
            }
        ],
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("saved_items_and_collections.json", json.dumps(export_json))
        archive.writestr("media/photo_1.jpg", b"\xff\xd8\xff\xe0fake-jpeg")
    buffer.seek(0)

    media_dir = tmp_path / "media"
    result = import_facebook_export(buffer.getvalue(), media_dir, tmp_path)

    assert result.json_files_read == 1
    assert result.media_copied == 1
    assert result.missing_media == 0
    assert len(result.entries) == 1

    entry = result.entries[0]
    assert entry.url == "https://www.facebook.com/post/1"
    assert entry.category == "Travel"
    assert len(entry.media) == 1
    assert entry.media[0]["original_name"] == "photo_1.jpg"
    assert entry.media[0]["kind"] == "image"

    stored = tmp_path / entry.media[0]["path"]
    assert stored.read_bytes() == b"\xff\xd8\xff\xe0fake-jpeg"
    assert stored.parent == media_dir


def test_import_facebook_export_counts_missing_media(tmp_path):
    export_json = {
        "saved_saved_items": [
            {
                "timestamp": 1700000000,
                "title": "Missing media",
                "attachments": [
                    {
                        "data": [
                            {
                                "external_context": {"url": "https://www.facebook.com/post/2"},
                                "media": {"uri": "media/absent.mp4"},
                            }
                        ]
                    }
                ],
            }
        ]
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("your_saved_items.json", json.dumps(export_json))
    buffer.seek(0)

    result = import_facebook_export(buffer.getvalue(), tmp_path / "media", tmp_path)

    assert result.media_copied == 0
    assert result.missing_media == 1
    assert result.entries[0].media == []


def test_import_facebook_export_rejects_non_zip(tmp_path):
    result = import_facebook_export(b"not a zip", tmp_path / "media", tmp_path)
    assert result.entries == []


def test_import_facebook_export_zip_without_saved_json(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("friends.json", json.dumps({"friends": []}))
    buffer.seek(0)

    result = import_facebook_export(buffer.getvalue(), tmp_path / "media", tmp_path)
    assert result.entries == []
    assert result.json_files_read == 0

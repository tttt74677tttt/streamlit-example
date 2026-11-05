from fb_import import ImportedEntry, normalize_facebook_url, sync_into_library

STAMP = "2026-01-01T00:00:00+00:00"


def entry(url: str, title: str = "Title", category: str = "Saved", media=None) -> ImportedEntry:
    return ImportedEntry(
        url=url,
        title=title,
        category=category,
        timestamp=1700000000,
        media=media or [],
    )


def test_normalize_strips_tracking_params_and_share_variants():
    noisy = (
        "https://m.facebook.com/story.php?story_fbid=123&id=456"
        "&__cft__[0]=AZabc&__tn__=%2C%3B&mibextid=abc123&rdid=XYZ#fragment"
    )
    clean = "https://www.facebook.com/story.php?story_fbid=123&id=456"

    assert normalize_facebook_url(noisy) == normalize_facebook_url(clean)


def test_normalize_keeps_identifying_params_only():
    normalized = normalize_facebook_url(
        "https://www.facebook.com/watch/?v=555&utm_source=share&fbclid=zzz&ref=bookmarks"
    )
    assert normalized == "https://www.facebook.com/watch?v=555"


def test_normalize_treats_trailing_slash_and_case_of_host_as_same():
    assert normalize_facebook_url("https://www.facebook.com/reel/42/") == normalize_facebook_url(
        "https://www.facebook.com/reel/42"
    )
    assert normalize_facebook_url("https://WWW.Facebook.com/reel/42") == normalize_facebook_url(
        "https://www.facebook.com/reel/42"
    )


def test_normalize_maps_mobile_and_web_subdomains_to_www():
    for variant in ("m.facebook.com", "web.facebook.com", "mobile.facebook.com", "facebook.com"):
        assert normalize_facebook_url(f"https://{variant}/groups/9") == (
            "https://www.facebook.com/groups/9"
        )


def test_normalize_passes_through_non_facebook_urls():
    assert normalize_facebook_url("https://example.com/a?b=1") == "https://example.com/a?b=1"
    assert normalize_facebook_url("") == ""


def test_sync_adds_new_entries_once():
    items: list[dict] = []
    entries = [entry("https://www.facebook.com/reel/1"), entry("https://www.facebook.com/reel/2")]

    added, updated = sync_into_library(items, entries, "Fallback", now=STAMP)

    assert (added, updated) == (2, 0)
    assert len(items) == 2
    assert {item["category"] for item in items} == {"Saved"}
    assert all(item["synced_at"] == STAMP for item in items)


def test_sync_matches_across_variants_and_does_not_duplicate():
    items = [
        {
            "id": "existing",
            "title": "Old title",
            "url": "https://m.facebook.com/story.php?story_fbid=9&id=1&__tn__=%2C%3B",
            "category": "Old",
            "notes": "my own note",
            "media": [],
            "created_at": STAMP,
        }
    ]

    added, updated = sync_into_library(
        items,
        [entry("https://www.facebook.com/story.php?story_fbid=9&id=1", title="New title", category="Fresh")],
        "Fallback",
        now=STAMP,
    )

    assert (added, updated) == (0, 1)
    assert len(items) == 1
    row = items[0]
    assert row["id"] == "existing"
    assert row["title"] == "New title"
    assert row["category"] == "Fresh"
    # user-owned notes survive a sync
    assert row["notes"] == "my own note"


def test_sync_reports_no_update_when_nothing_changed():
    items = [
        {
            "id": "e1",
            "title": "Same",
            "url": "https://www.facebook.com/reel/7",
            "category": "Saved",
            "notes": "",
            "media": [{"original_name": "a.jpg", "path": "data/media/a.jpg", "kind": "image", "size": 1}],
            "created_at": STAMP,
        }
    ]
    entries = [
        entry(
            "https://www.facebook.com/reel/7",
            title="Same",
            media=[{"original_name": "a.jpg", "path": "data/media/a.jpg", "kind": "image", "size": 1}],
        )
    ]

    added, updated = sync_into_library(items, entries, "Saved", now=STAMP)

    assert (added, updated) == (0, 0)
    assert len(items[0]["media"]) == 1


def test_sync_appends_only_genuinely_new_media():
    items = [
        {
            "id": "e1",
            "title": "Same",
            "url": "https://www.facebook.com/reel/8",
            "category": "Saved",
            "notes": "",
            "media": [{"original_name": "a.jpg", "path": "p/a.jpg", "kind": "image", "size": 1}],
            "created_at": STAMP,
        }
    ]
    entries = [
        entry(
            "https://www.facebook.com/reel/8",
            media=[
                {"original_name": "a.jpg", "path": "p/a.jpg", "kind": "image", "size": 1},
                {"original_name": "b.mp4", "path": "p/b.mp4", "kind": "video", "size": 2},
            ],
        )
    ]

    added, updated = sync_into_library(items, entries, "Saved", now=STAMP)

    assert (added, updated) == (0, 1)
    names = [media["original_name"] for media in items[0]["media"]]
    assert names == ["a.jpg", "b.mp4"]


def test_sync_uses_fallback_category_when_entry_has_none():
    items: list[dict] = []
    added, _ = sync_into_library(
        items, [entry("https://www.facebook.com/reel/10", category="")], "Imported", now=STAMP
    )

    assert added == 1
    assert items[0]["category"] == "Imported"


def test_sync_is_idempotent_across_repeated_imports():
    items: list[dict] = []
    entries = [entry("https://www.facebook.com/reel/11")]

    sync_into_library(items, entries, "Saved", now=STAMP)
    snapshot = list(items)
    added_again, updated_again = sync_into_library(items, entries, "Saved", now=STAMP)

    assert (added_again, updated_again) == (0, 0)
    assert len(items) == 1
    assert items[0]["id"] == snapshot[0]["id"]

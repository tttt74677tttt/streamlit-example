from preview_capture import (
    chunk_targets,
    is_login_wall,
    preview_filename,
    preview_record,
    select_capture_targets,
    PreviewResult,
)


def item(url, media=None, preview=None, id="i"):
    return {"id": id, "url": url, "media": media or [], "preview": preview or {}}


def test_is_login_wall_matches_facebook_gate_text():
    assert is_login_wall("Log in to continue")
    assert is_login_wall("You must log in to see this")
    assert is_login_wall("SEE MORE OF FACEBOOK ON FACEBOOK")
    assert is_login_wall("This content isn't available right now")


def test_is_login_wall_ignores_normal_page_text():
    assert not is_login_wall("A public video about cooking")
    assert not is_login_wall("")


def test_select_targets_skips_items_with_media():
    items = [
        item("https://www.facebook.com/reel/1", media=[{"original_name": "a.jpg"}], id="a"),
        item("https://www.facebook.com/reel/2", id="b"),
    ]
    targets = select_capture_targets(items, only_missing=True)
    assert [t["id"] for t in targets] == ["b"]


def test_select_targets_skips_items_with_existing_preview():
    items = [
        item("https://www.facebook.com/reel/3", preview={"path": "data/media/p.png"}, id="a"),
        item("https://www.facebook.com/reel/4", id="b"),
    ]
    targets = select_capture_targets(items, only_missing=True)
    assert [t["id"] for t in targets] == ["b"]


def test_select_targets_includes_everything_when_only_missing_false():
    items = [
        item("https://www.facebook.com/reel/5", media=[{"original_name": "a.jpg"}], id="a"),
        item("https://www.facebook.com/reel/6", id="b"),
    ]
    targets = select_capture_targets(items, only_missing=False)
    assert {t["id"] for t in targets} == {"a", "b"}


def test_select_targets_dedupes_url_variants():
    items = [
        item("https://www.facebook.com/reel/7", id="a"),
        item("https://m.facebook.com/reel/7?__tn__=x", id="b"),
    ]
    targets = select_capture_targets(items, only_missing=True)
    assert len(targets) == 1


def test_select_targets_ignores_items_without_url():
    assert select_capture_targets([{"id": "x", "url": ""}]) == []


def test_chunk_targets_splits_evenly_and_keeps_remainder():
    targets = [{"id": str(i)} for i in range(7)]
    batches = chunk_targets(targets, 3)
    assert [len(b) for b in batches] == [3, 3, 1]


def test_chunk_targets_handles_non_positive_size():
    targets = [{"id": "a"}, {"id": "b"}]
    assert chunk_targets(targets, 0) == [targets]
    assert chunk_targets([], 5) == []


def test_preview_filename_is_png_and_unique():
    a = preview_filename("https://www.facebook.com/reel/8")
    b = preview_filename("https://www.facebook.com/reel/8")
    assert a.startswith("preview-") and a.endswith(".png")
    assert a != b


def test_preview_record_shapes_result():
    result = PreviewResult(url="u", path="data/media/p.png", login_wall=True, title="T")
    record = preview_record(result)
    assert record == {"path": "data/media/p.png", "login_wall": True, "title": "T", "error": None}


def test_preview_result_ok_requires_path():
    assert PreviewResult(url="u", path="p.png").ok
    assert not PreviewResult(url="u", error="boom").ok

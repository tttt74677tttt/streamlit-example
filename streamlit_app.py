import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from fb_import import (
    IMAGE_TYPES,
    ImportedEntry,
    import_facebook_export,
    is_facebook_url,
    media_kind,
    parse_bookmarks_html,
)

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
LIBRARY_FILE = DATA_DIR / "facebook_library.json"

UPLOAD_TYPES = sorted(IMAGE_TYPES | {"mp4", "mov", "m4v", "webm", "avi", "mkv"})


def ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(exist_ok=True)
    if not LIBRARY_FILE.exists():
        save_items([])


def load_items() -> list[dict]:
    ensure_storage()
    try:
        with LIBRARY_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_items(items: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with LIBRARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(items, file, indent=2)


def save_uploaded_files(files, prefix: str = "") -> list[dict]:
    saved_files = []
    for uploaded_file in files:
        suffix = Path(uploaded_file.name).suffix.lower()
        safe_name = f"{prefix}{uuid.uuid4().hex}{suffix}"
        destination = MEDIA_DIR / safe_name
        with destination.open("wb") as file:
            shutil.copyfileobj(uploaded_file, file)
        saved_files.append(
            {
                "original_name": uploaded_file.name,
                "path": str(destination.relative_to(APP_DIR)),
                "kind": media_kind(uploaded_file.name),
                "size": uploaded_file.size,
            }
        )
    return saved_files


def known_categories(items: list[dict]) -> list[str]:
    categories = {item["category"] for item in items if item.get("category")}
    return sorted(categories)


def created_at_from_timestamp(timestamp: int | None) -> str:
    if timestamp:
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            pass
    return datetime.now(timezone.utc).isoformat()


def merge_entries(items: list[dict], entries: list[ImportedEntry], fallback_category: str) -> int:
    """Add imported entries, skipping any Facebook URL already in the library."""
    existing_urls = {item["url"] for item in items}
    added = 0
    for entry in entries:
        if entry.url in existing_urls:
            continue
        existing_urls.add(entry.url)
        items.insert(
            0,
            {
                "id": uuid.uuid4().hex,
                "title": entry.title or entry.url,
                "url": entry.url,
                "category": entry.category or fallback_category,
                "notes": "",
                "media": entry.media,
                "created_at": created_at_from_timestamp(entry.timestamp),
            },
        )
        added += 1
    if added:
        save_items(items)
    return added


def delete_item(item_id: str) -> None:
    items = load_items()
    item_to_delete = next((item for item in items if item["id"] == item_id), None)
    remaining_items = [item for item in items if item["id"] != item_id]
    if item_to_delete:
        for media in item_to_delete.get("media", []):
            media_path = APP_DIR / media["path"]
            if media_path.exists():
                media_path.unlink()
    save_items(remaining_items)


def attach_media(item_id: str, files) -> int:
    items = load_items()
    new_media = save_uploaded_files(files, prefix=f"{item_id}-")
    for item in items:
        if item["id"] == item_id:
            item.setdefault("media", []).extend(new_media)
            break
    save_items(items)
    return len(new_media)


def render_media(media: dict) -> None:
    media_path = APP_DIR / media["path"]
    if not media_path.exists():
        st.warning(f"Missing offline file: {media['original_name']}")
        return

    caption = media["original_name"]
    if media["kind"] == "image":
        st.image(str(media_path), caption=caption, use_container_width=True)
    elif media["kind"] == "video":
        st.video(str(media_path))
        st.caption(caption)
    else:
        st.download_button(
            label=f"Download {caption}",
            data=media_path.read_bytes(),
            file_name=caption,
            key=f"download-{media['path']}",
        )


def render_import_section(items: list[dict]) -> None:
    st.markdown(
        "Facebook has no public API for your saved items and this app never signs in to your "
        "account. Instead, import a file you own: **Settings & privacy → Settings → "
        "Your Facebook information → Download your information**. Choose **JSON** format and "
        "include **Saved items and collections** (plus photos and videos if you want media)."
    )

    export_tab, bookmarks_tab = st.tabs(["Facebook data export (.zip)", "Browser bookmarks (.html)"])

    with export_tab:
        default_category = st.text_input(
            "Category for items without a collection",
            value="Imported from Facebook",
            key="export-category",
        )
        export_zip = st.file_uploader(
            "Upload the Download Your Information zip",
            type=["zip"],
            key="export-zip",
        )
        if export_zip is not None and st.button("Import export", type="primary", key="import-export"):
            with st.spinner("Reading export and copying media..."):
                result = import_facebook_export(export_zip.getvalue(), MEDIA_DIR, APP_DIR)
            if not result.entries:
                st.error(
                    "No saved items found. Make sure the export includes "
                    "“Saved items and collections” and uses JSON format."
                )
            else:
                added = merge_entries(items, result.entries, default_category or "Imported from Facebook")
                st.success(
                    f"Imported {added} new item(s) from {result.json_files_read} saved-items file(s)."
                )
                st.info(
                    f"{result.media_copied} media file(s) copied offline, "
                    f"{result.missing_media} reference(s) had no file in the export, "
                    f"{result.with_media}/{len(result.entries)} item(s) have offline media."
                )
                if result.missing_media:
                    st.caption(
                        "Media the export does not bundle stays online-only. Use "
                        "“Add offline pictures or videos” on an item to attach your own copies."
                    )
                st.rerun()

    with bookmarks_tab:
        default_folder = st.text_input(
            "Category for bookmarks outside a folder",
            value="Bookmarks",
            key="bookmarks-category",
        )
        bookmarks_html = st.file_uploader(
            "Upload a bookmarks HTML file (Chrome, Edge, Firefox, Safari)",
            type=["html", "htm"],
            key="bookmarks-html",
        )
        if bookmarks_html is not None and st.button("Import bookmarks", key="import-bookmarks"):
            entries = parse_bookmarks_html(
                bookmarks_html.getvalue().decode("utf-8", "replace"),
                default_category=default_folder or "Bookmarks",
            )
            if not entries:
                st.error("No Facebook links found in that bookmarks file.")
            else:
                added = merge_entries(items, entries, default_folder or "Bookmarks")
                st.success(f"Imported {added} new bookmark(s).")
                st.caption(
                    "Bookmarks carry links and folder names only. Download the media you care about "
                    "from Facebook, then attach it on each item."
                )
                st.rerun()


st.set_page_config(page_title="Facebook Save Library", page_icon="📌", layout="wide")
ensure_storage()

items = load_items()
categories = known_categories(items)

st.title("Facebook Save Library")
st.caption("Save Facebook links with offline pictures or videos, organized by category.")

with st.sidebar:
    st.header("Filters")
    search = st.text_input("Search", placeholder="Search title, link, notes, category")
    selected_category = st.selectbox("Category", ["All categories"] + categories)
    st.metric("Saved items", len(items))
    st.metric("Categories", len(categories))
    offline_items = sum(1 for item in items if item.get("media"))
    st.metric("With offline media", offline_items)

library_tab, import_tab = st.tabs(["Library", "Import from Facebook"])

with import_tab:
    render_import_section(items)
    items = load_items()
    categories = known_categories(items)

with library_tab:
    st.subheader("Add a saved Facebook item")
    with st.form("save-facebook-item", clear_on_submit=True):
        title = st.text_input("Title", placeholder="Example: Product demo post")
        facebook_url = st.text_input("Facebook link", placeholder="https://www.facebook.com/...")

        category_choice = st.selectbox("Choose existing category", [""] + categories)
        new_category = st.text_input("Or create a new category", placeholder="Family, Work, Ideas")

        notes = st.text_area("Notes", placeholder="Why did you save this?")
        uploaded_files = st.file_uploader(
            "Offline pictures or videos",
            type=UPLOAD_TYPES,
            accept_multiple_files=True,
            help="Upload images/videos from your device so the item still has media offline.",
        )

        submitted = st.form_submit_button("Save item", use_container_width=True)

    if submitted:
        normalized_url = facebook_url.strip()
        category = (new_category or category_choice).strip()

        if not title.strip():
            st.error("Please add a title.")
        elif not is_facebook_url(normalized_url):
            st.error("Please enter a valid Facebook link.")
        elif not category:
            st.error("Please choose or create a category.")
        else:
            items.insert(
                0,
                {
                    "id": uuid.uuid4().hex,
                    "title": title.strip(),
                    "url": normalized_url,
                    "category": category,
                    "notes": notes.strip(),
                    "media": save_uploaded_files(uploaded_files or []),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            save_items(items)
            st.success("Saved successfully.")
            st.rerun()

    st.divider()
    st.subheader("Saved library")

    filtered_items = items
    if selected_category != "All categories":
        filtered_items = [item for item in filtered_items if item["category"] == selected_category]

    if search:
        query = search.lower()
        filtered_items = [
            item
            for item in filtered_items
            if query
            in " ".join(
                [
                    item.get("title", ""),
                    item.get("url", ""),
                    item.get("category", ""),
                    item.get("notes", ""),
                ]
            ).lower()
        ]

    if not filtered_items:
        st.info("No saved items match the current filters.")

    for item in filtered_items:
        with st.container(border=True):
            header_col, action_col = st.columns([4, 1])
            with header_col:
                st.markdown(f"### {item['title']}")
                st.markdown(f"[Open Facebook link]({item['url']})")
                media_count = len(item.get("media", []))
                st.caption(f"Category: {item['category']} · Offline files: {media_count}")
            with action_col:
                if st.button("Delete", key=f"delete-{item['id']}", use_container_width=True):
                    delete_item(item["id"])
                    st.rerun()

            if item.get("notes"):
                st.write(item["notes"])

            media_columns = st.columns(min(3, max(1, len(item.get("media", [])))))
            for index, media in enumerate(item.get("media", [])):
                with media_columns[index % len(media_columns)]:
                    render_media(media)

            with st.expander("Add offline pictures or videos"):
                extra_files = st.file_uploader(
                    "Attach files to this item",
                    type=UPLOAD_TYPES,
                    accept_multiple_files=True,
                    key=f"attach-{item['id']}",
                    label_visibility="collapsed",
                )
                if extra_files and st.button("Attach", key=f"attach-btn-{item['id']}"):
                    count = attach_media(item["id"], extra_files)
                    st.success(f"Attached {count} file(s).")
                    st.rerun()

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
LIBRARY_FILE = DATA_DIR / "facebook_library.json"

IMAGE_TYPES = {"jpg", "jpeg", "png", "gif", "webp"}
VIDEO_TYPES = {"mp4", "mov", "m4v", "webm", "avi", "mkv"}


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


def is_facebook_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    return parsed.scheme in {"http", "https"} and (
        host == "facebook.com"
        or host.endswith(".facebook.com")
        or host == "fb.watch"
        or host.endswith(".fb.watch")
        or host == "fb.com"
        or host.endswith(".fb.com")
    )


def media_kind(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension in IMAGE_TYPES:
        return "image"
    if extension in VIDEO_TYPES:
        return "video"
    return "file"


def save_uploaded_files(files) -> list[dict]:
    saved_files = []
    for uploaded_file in files:
        suffix = Path(uploaded_file.name).suffix.lower()
        safe_name = f"{uuid.uuid4().hex}{suffix}"
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

st.subheader("Add a saved Facebook item")
with st.form("save-facebook-item", clear_on_submit=True):
    title = st.text_input("Title", placeholder="Example: Product demo post")
    facebook_url = st.text_input("Facebook link", placeholder="https://www.facebook.com/...")

    category_options = [""] + categories
    category_choice = st.selectbox("Choose existing category", category_options)
    new_category = st.text_input("Or create a new category", placeholder="Family, Work, Ideas")

    notes = st.text_area("Notes", placeholder="Why did you save this?")
    uploaded_files = st.file_uploader(
        "Offline pictures or videos",
        type=sorted(IMAGE_TYPES | VIDEO_TYPES),
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
    elif not uploaded_files:
        st.error("Please upload at least one picture or video for offline use.")
    else:
        saved_media = save_uploaded_files(uploaded_files)
        items.insert(
            0,
            {
                "id": uuid.uuid4().hex,
                "title": title.strip(),
                "url": normalized_url,
                "category": category,
                "notes": notes.strip(),
                "media": saved_media,
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
            st.caption(f"Category: {item['category']}")
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

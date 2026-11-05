# Facebook Save Library

A Streamlit web app for saving Facebook links with offline pictures or videos and organizing them by category.

## Features

- Save a Facebook link with a title and notes.
- Upload local pictures or videos so the media is available offline.
- Choose an existing category or create a new one while saving.
- Search and filter saved items by category.
- Delete saved items and their stored offline media.
- Attach extra offline media to an existing item at any time.

## Importing your saved Facebook content

Facebook has no public API for a user's saved items, and this app never signs in to a
Facebook account. Instead it imports files you own and export yourself.

### Option 1 — Facebook "Download Your Information" (recommended)

1. In Facebook: **Settings & privacy → Settings → Your Facebook information → Download your information**.
2. Select **JSON** as the format.
3. Include **Saved items and collections**, and the photos/videos you want kept offline.
4. Request the download, wait for Facebook's notification, then download the `.zip`.
5. In the app open the **Import from Facebook** tab, upload the `.zip`, and click **Import export**.

Saved items become library entries. Their categories come from your Facebook collections when the
export includes them. Media files bundled in the export are copied into `data/media/` so they
render offline.

Some saved posts point at media that Facebook does not bundle in the export. Those entries still
import as links and are counted as "missing media" in the import summary; use **Add offline
pictures or videos** on the item to attach copies you downloaded yourself.

### Option 2 — Browser bookmarks

Export bookmarks to HTML from your browser (Chrome/Edge: Bookmark manager → Export bookmarks,
Firefox: Library → Import and Backup → Export Bookmarks to HTML). Upload that `.html` in the
**Browser bookmarks (.html)** sub-tab. Bookmark folders become categories.

Bookmarks carry links only, so attach media manually afterwards.

## Run locally

```bash
streamlit run streamlit_app.py
```

Saved data is stored under `data/` in this project directory.

## Tests

```bash
python3 -m pytest tests -q
```

"""Capture offline page previews for saved Facebook links with Chrome/chromedriver.

Facebook shows a login wall to signed-out visitors for much of its content, and this module
never authenticates. What it can still do is render the public view of a link and screenshot it,
which for many posts is enough to recognise the item later without going online.

This is a best-effort enrichment, not an archiver: a preview proves *which* page a link points at,
it does not reproduce the post. Items whose page needs a login are marked so the UI can say so
instead of showing a misleading picture.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from fb_import import normalize_facebook_url

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800
DEFAULT_TIMEOUT = 25

# Text that appears only when Facebook is blocking a signed-out visitor.
LOGIN_WALL_MARKERS = (
    "log in to continue",
    "you must log in",
    "log into facebook",
    "see more of",
    "create new account",
    "log in or sign up",
    "this content isn't available",
    "this page isn't available",
)

# Overlays that obscure the actual page content in a screenshot.
OVERLAY_SELECTORS = (
    '[data-testid="cookie-policy-manage-dialog"]',
    '[aria-label="Close"]',
    '[aria-label="Allow all"]',
    'div[role="dialog"]',
)


@dataclass
class PreviewResult:
    """Outcome of attempting a preview for a single URL."""

    url: str
    path: str | None = None
    error: str | None = None
    login_wall: bool = False
    title: str = ""

    @property
    def ok(self) -> bool:
        return self.path is not None


def preview_filename(url: str) -> str:
    """Deterministic-ish unique filename for a preview image."""
    return f"preview-{uuid.uuid4().hex}.png"


def is_login_wall(page_text: str) -> bool:
    """Detect Facebook's signed-out gate from rendered page text."""
    haystack = (page_text or "").lower()
    return any(marker in haystack for marker in LOGIN_WALL_MARKERS)


def select_capture_targets(items: list[dict], only_missing: bool = True) -> list[dict]:
    """Pick library items worth previewing, de-duplicated by normalized URL.

    By default this skips items that already have offline media, so a capture run only spends
    time on links that would otherwise show nothing.
    """
    seen: set[str] = set()
    targets: list[dict] = []
    for item in items:
        url = item.get("url", "")
        if not url:
            continue
        key = normalize_facebook_url(url)
        if key in seen:
            continue
        if only_missing and item.get("media"):
            continue
        if item.get("preview", {}).get("path") and only_missing:
            continue
        seen.add(key)
        targets.append(item)
    return targets


def chunk_targets(targets: list[dict], size: int) -> list[list[dict]]:
    """Split a target list into batches so long runs report progress incrementally."""
    if size <= 0:
        return [targets] if targets else []
    return [targets[index : index + size] for index in range(0, len(targets), size)]


def _build_driver(headless: bool = True, user_data_dir: str | None = None):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument(f"--window-size={VIEWPORT_WIDTH},{VIEWPORT_HEIGHT}")
    options.add_argument("--hide-scrollbars")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
    )
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
    return webdriver.Chrome(options=options)


def _dismiss_overlays(driver) -> None:
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.common.by import By

    for selector in OVERLAY_SELECTORS:
        try:
            for element in driver.find_elements(By.CSS_SELECTOR, selector)[:3]:
                if element.is_displayed():
                    driver.execute_script("arguments[0].remove();", element)
        except WebDriverException:
            continue


def capture_preview(url: str, media_dir: Path, app_dir: Path, timeout: int = DEFAULT_TIMEOUT) -> PreviewResult:
    """Render ``url`` in headless Chrome and save a PNG screenshot into ``media_dir``."""
    result = PreviewResult(url=url)
    media_dir.mkdir(parents=True, exist_ok=True)

    driver = None
    try:
        driver = _build_driver()
        driver.set_page_load_timeout(timeout)
        try:
            driver.get(url)
        except Exception as exc:  # page-load timeouts still leave a usable render
            result.error = f"load: {type(exc).__name__}"

        _dismiss_overlays(driver)
        try:
            driver.set_window_size(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        except Exception:
            pass

        body_text = driver.find_element("tag name", "body").text or ""
        result.login_wall = is_login_wall(body_text)
        result.title = (driver.title or "").strip()[:200]

        filename = preview_filename(url)
        destination = media_dir / filename
        ok = driver.save_screenshot(str(destination))
        if ok and destination.exists() and destination.stat().st_size > 0:
            result.path = str(destination.relative_to(app_dir))
        else:
            result.error = result.error or "screenshot failed"
    except Exception as exc:
        result.error = f"{type(exc).__name__}: {str(exc)[:200]}"
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    return result


def preview_record(result: PreviewResult) -> dict:
    """Shape a PreviewResult into the dict stored on a library item."""
    return {
        "path": result.path,
        "login_wall": result.login_wall,
        "title": result.title,
        "error": result.error,
    }

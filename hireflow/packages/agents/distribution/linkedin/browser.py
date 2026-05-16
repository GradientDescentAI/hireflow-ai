"""
LinkedIn Playwright session — LI-001, AR-001 to AR-003.

Design principles:
  - Credentials never logged, always fetched from vault at call time.
  - Cookies persisted in vault (not in env) to survive restarts.
  - Human-like timing on every interaction.
  - Zero automated engagement (AR-002): no likes, comments, DMs.
  - Single session per account — no parallel tabs.
  - Proxy is mandatory in production (AR-003).

MFA (LI-004) and CAPTCHA (LI-005) raise dedicated exceptions so the
caller (LinkedIn agent) can freeze the account and alert the operator.
"""

import json
import random
import time
import uuid
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, BrowserContext, Page


# ── Exceptions ────────────────────────────────────────────────────────────────

class MFARequiredException(Exception):
    """LinkedIn security challenge detected — operator must complete MFA."""


class CAPTCHADetectedException(Exception):
    """LinkedIn CAPTCHA detected — account frozen, failover initiated."""


class LoginFailedException(Exception):
    """Could not log in with the provided credentials."""


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class PostResult:
    post_url: str | None
    post_id: str | None
    screenshot_bytes: bytes
    updated_cookies: list[dict]   # save back to vault after posting


# ── Internal helpers ──────────────────────────────────────────────────────────

def _human_delay(lo: float = 0.8, hi: float = 2.5) -> None:
    time.sleep(random.uniform(lo, hi))


def _type_humanly(page: Page, selector: str, text: str) -> None:
    element = page.locator(selector).first
    element.click()
    _human_delay(0.3, 0.8)
    for char in text:
        element.type(char, delay=random.randint(40, 120))


def _detect_mfa(page: Page) -> bool:
    url = page.url
    if "checkpoint" in url or "challenge" in url:
        return True
    if page.locator("input[name='pin']").count() > 0:
        return True
    if page.get_by_text("verification", exact=False).count() > 0:
        return True
    return False


def _detect_captcha(page: Page) -> bool:
    content = page.content().lower()
    return "captcha" in content or page.locator("#captcha-internal").count() > 0


_LOGGED_IN_SELECTORS = (
    ".global-nav__me-photo",
    "[data-control-name='nav.settings']",
    "img.global-nav__me-photo",
    ".feed-identity-module",            # left-rail profile card on /feed/
    "button[aria-label*='View profile']",
    ".share-box-feed-entry__trigger",   # "Start a post" button — proves we're on the feed
)


def _is_logged_in(page: Page, timeout_ms: int = 12000) -> bool:
    """True if the page shows any of several logged-in markers, or if URL is /feed/."""
    # URL check first — /login auto-redirects to /feed/ when authenticated
    if "/feed" in page.url and "login" not in page.url:
        return True
    selector = ", ".join(_LOGGED_IN_SELECTORS)
    try:
        page.wait_for_selector(selector, timeout=timeout_ms)
        return True
    except Exception:
        return False


# ── Main session class ────────────────────────────────────────────────────────

class LinkedInBrowser:
    """Context manager for a single LinkedIn posting session."""

    def __init__(self, credentials: dict) -> None:
        """
        credentials dict (from vault):
          username: str
          password: str
          proxy_url: str | None  — e.g. http://user:pass@host:port
          cookies: list[dict] | None  — saved Playwright cookies
        """
        self._username: str = credentials["username"]
        self._password: str = credentials["password"]
        self._proxy_url: str | None = credentials.get("proxy_url")
        self._cookies: list[dict] = credentials.get("cookies") or []

        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None

    def __enter__(self) -> "LinkedInBrowser":
        self._playwright = sync_playwright().start()
        launch_args = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        }
        self._browser = self._playwright.chromium.launch(**launch_args)

        ctx_args: dict = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1280, "height": 800},
            "locale": "en-IN",
            "timezone_id": "Asia/Kolkata",
        }
        if self._proxy_url:
            ctx_args["proxy"] = {"server": self._proxy_url}

        self._context = self._browser.new_context(**ctx_args)

        # Stealth: patch navigator.webdriver + ~20 other fingerprint vectors via playwright-stealth.
        # Without this LinkedIn serves an empty body for headless Chromium.
        try:
            from playwright_stealth import stealth_sync  # type: ignore[import]
            stealth_sync(self._context)
        except Exception:
            # Fallback to manual minimal patch if the library import fails
            self._context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        if self._cookies:
            self._context.add_cookies(self._cookies)

        return self

    def __exit__(self, *_) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def post(self, post_body: str) -> PostResult:
        """Create a LinkedIn post.  Returns PostResult with URL and screenshot."""
        page = self._context.new_page()
        try:
            return self._do_post(page, post_body)
        finally:
            page.close()

    def _do_post(self, page: Page, post_body: str) -> PostResult:
        import structlog as _sl
        log = _sl.get_logger()

        # Navigate to feed and check session state
        # Use "load" instead of "domcontentloaded" — SPA needs JS to execute before any UI exists
        page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        _human_delay(2, 4)

        # Snapshot what we actually got — body length & a sample of body text
        try:
            body_html = page.evaluate("document.body ? document.body.innerHTML.length : 0")
            body_text = (page.evaluate("document.body ? document.body.innerText : ''") or "")[:300]
        except Exception:
            body_html, body_text = 0, ""
        log.info(
            "linkedin_post_navigate",
            url=page.url,
            title=(page.title() or "")[:120],
            cookies_loaded=len(self._cookies),
            body_html_len=body_html,
            body_text_preview=body_text,
        )

        # Always save an early screenshot for diagnostics, regardless of outcome
        try:
            from packages.storage import client as storage
            import uuid as _uuid, datetime as _dt
            shot_bytes = page.screenshot(full_page=False)
            shot_key = f"diag/linkedin-after-nav-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{_uuid.uuid4().hex[:6]}.png"
            storage.upload(shot_key, shot_bytes, "image/png")
            log.info("linkedin_diag_screenshot_after_nav", key=shot_key)
        except Exception as _exc:
            log.warning("linkedin_diag_screenshot_failed", error=str(_exc))

        if not _is_logged_in(page):
            log.warning("linkedin_not_logged_in_via_cookies", url=page.url)
            # Save diagnostic screenshot before attempting password login
            try:
                from packages.storage import client as storage
                import uuid as _uuid, datetime as _dt
                shot_bytes = page.screenshot(full_page=False)
                shot_key = f"diag/linkedin-precookie-fail-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{_uuid.uuid4().hex[:6]}.png"
                storage.upload(shot_key, shot_bytes, "image/png")
                log.info("linkedin_diag_screenshot", key=shot_key, url=page.url)
            except Exception as _exc:
                log.warning("linkedin_diag_screenshot_failed", error=str(_exc))
            self._login(page)

        if _detect_mfa(page):
            raise MFARequiredException("LinkedIn MFA / security challenge detected after login")

        if _detect_captcha(page):
            raise CAPTCHADetectedException("LinkedIn CAPTCHA detected")

        # Wait for feed to fully render — LinkedIn's share box is JS-rendered
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass  # not fatal; the explicit selector wait below is the real gate
        _human_delay(1.5, 3)

        # Open the post composer — selectors cover legacy + 2024+ LinkedIn DOM
        share_trigger_selectors = [
            "button.share-box-feed-entry__trigger",
            "button[aria-label='Start a post']",
            "button[aria-label*='Start a post']",
            "div.share-box-feed-entry__trigger",
            ".share-box-feed-entry__trigger",
            "button.artdeco-button[aria-label*='post']",
        ]
        composer_opened = False
        for sel in share_trigger_selectors:
            try:
                page.locator(sel).first.click(timeout=4000)
                composer_opened = True
                log.info("linkedin_composer_opened", selector=sel)
                break
            except Exception:
                continue
        if not composer_opened:
            # One last fallback: click button whose accessible name matches "Start a post"
            try:
                import re as _re
                page.get_by_role("button", name=_re.compile(r"start a post", _re.IGNORECASE)).first.click(timeout=5000)
                composer_opened = True
                log.info("linkedin_composer_opened", selector="get_by_role:start a post")
            except Exception:
                # Save diagnostic screenshot for the post-feed state
                try:
                    from packages.storage import client as storage
                    import uuid as _uuid, datetime as _dt
                    shot_bytes = page.screenshot(full_page=False)
                    shot_key = f"diag/linkedin-no-composer-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{_uuid.uuid4().hex[:6]}.png"
                    storage.upload(shot_key, shot_bytes, "image/png")
                    log.warning("linkedin_composer_not_found", url=page.url, screenshot=shot_key)
                except Exception:
                    log.warning("linkedin_composer_not_found", url=page.url)
                raise

        _human_delay(1.5, 3)

        # Type post content in the editor
        editor = page.locator(".ql-editor, [contenteditable='true']").first
        editor.click()
        _human_delay(0.5, 1)

        # Type with human-like speed
        for char in post_body:
            editor.type(char, delay=random.randint(30, 90))
            # Occasional longer pause simulating thought
            if random.random() < 0.02:
                _human_delay(0.5, 1.5)

        _human_delay(1, 2)

        # Screenshot the draft before posting
        screenshot = page.screenshot(full_page=False)

        # Click Post button — selectors cover legacy + 2024+ LinkedIn DOM
        post_button_selectors = [
            "button.share-actions__primary-action",
            "button[data-control-name='share.post']",
            "button.artdeco-button--primary:has-text('Post')",
            "button[aria-label*='Post']",
        ]
        post_clicked = False
        for sel in post_button_selectors:
            try:
                page.locator(sel).first.click(timeout=4000)
                post_clicked = True
                log.info("linkedin_post_button_clicked", selector=sel)
                break
            except Exception:
                continue
        if not post_clicked:
            raise RuntimeError(f"Could not find Post button on share modal; url={page.url}")
        _human_delay(3, 6)

        # Try to extract post URL from the feed
        post_url = self._extract_post_url(page)

        updated_cookies = self._context.cookies()

        return PostResult(
            post_url=post_url,
            post_id=_extract_post_id(post_url) if post_url else None,
            screenshot_bytes=screenshot,
            updated_cookies=updated_cookies,
        )

    def _login(self, page: Page) -> None:
        import structlog as _sl
        log = _sl.get_logger()

        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        _human_delay(1, 2)
        log.info("linkedin_login_navigate", url=page.url, title=(page.title() or "")[:120])

        # Cookies may have authenticated us — /login auto-redirects to /feed/ in that case
        if "/feed" in page.url and "login" not in page.url:
            log.info("linkedin_already_authenticated_via_cookies")
            return

        # If we can't see the username field, the page is showing a challenge instead of the form
        try:
            page.wait_for_selector("#username", timeout=10000)
        except Exception:
            if _detect_mfa(page):
                raise MFARequiredException(f"MFA challenge on login page; url={page.url}")
            if _detect_captcha(page):
                raise CAPTCHADetectedException(f"CAPTCHA on login page; url={page.url}")
            raise LoginFailedException(
                f"Login form not present (no #username); url={page.url} title={(page.title() or '')[:80]}"
            )

        _type_humanly(page, "#username", self._username)
        _human_delay(0.5, 1.2)
        _type_humanly(page, "#password", self._password)
        _human_delay(0.5, 1)

        page.click("button[data-litms-control-urn='login-submit'], button[type='submit']")
        _human_delay(3, 5)

        if not _is_logged_in(page):
            if _detect_mfa(page):
                raise MFARequiredException("MFA required after login")
            raise LoginFailedException(f"Login failed for {self._username}")

    def _extract_post_url(self, page: Page) -> str | None:
        """Try to find the URL of the just-published post in the feed."""
        try:
            # Most recently published post appears first in the feed
            post_link = page.locator("a[href*='/posts/']").first
            href = post_link.get_attribute("href", timeout=5000)
            if href and "/posts/" in href:
                return href if href.startswith("http") else f"https://www.linkedin.com{href}"
        except Exception:
            pass
        return None


def _extract_post_id(post_url: str) -> str | None:
    """Extract the numeric post ID from a LinkedIn post URL."""
    import re
    match = re.search(r"activity-(\d+)", post_url)
    return match.group(1) if match else None

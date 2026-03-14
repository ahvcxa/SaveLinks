"""
Async metadata scraper adapter.

Extracts OpenGraph, Twitter Card, and generic meta tags from URLs.
Uses httpx for async HTTP and BeautifulSoup for HTML parsing.
Initially called via FastAPI BackgroundTasks (Celery deferred to FAZA 1).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("SaveLinks.scraper")

# Default timeout for HTTP requests (seconds)
_REQUEST_TIMEOUT = 10.0

# Default user-agent to avoid bot blocks
_USER_AGENT = (
    "Mozilla/5.0 (compatible; SaveLinksBot/1.0; +https://github.com/savelinks)"
)


async def extract_metadata(url: str) -> dict[str, Any]:
    """
    Fetch a URL and extract metadata.

    Returns a dict with keys:
        - title: str | None
        - description: str | None
        - image: str | None
        - favicon: str | None
        - og: dict (all OpenGraph tags)
        - twitter: dict (all Twitter Card tags)

    Never raises — returns partial results on failure.
    """
    result: dict[str, Any] = {
        "title": None,
        "description": None,
        "image": None,
        "favicon": None,
        "og": {},
        "twitter": {},
    }

    try:
        async with httpx.AsyncClient(
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # <title> tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            result["title"] = title_tag.string.strip()

        # Meta description
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            result["description"] = desc_tag["content"].strip()

        # OpenGraph tags
        for tag in soup.find_all("meta", attrs={"property": True}):
            prop = tag.get("property", "")
            content = tag.get("content", "")
            if prop.startswith("og:") and content:
                key = prop[3:]  # strip "og:" prefix
                result["og"][key] = content
                if key == "title" and not result["title"]:
                    result["title"] = content
                elif key == "description" and not result["description"]:
                    result["description"] = content
                elif key == "image" and not result["image"]:
                    result["image"] = content

        # Twitter Card tags
        for tag in soup.find_all("meta", attrs={"name": True}):
            name = tag.get("name", "")
            content = tag.get("content", "")
            if name.startswith("twitter:") and content:
                key = name[8:]  # strip "twitter:" prefix
                result["twitter"][key] = content
                if key == "title" and not result["title"]:
                    result["title"] = content
                elif key == "description" and not result["description"]:
                    result["description"] = content
                elif key == "image" and not result["image"]:
                    result["image"] = content

        # Favicon
        icon_link = soup.find("link", rel=lambda r: r and "icon" in r)
        if icon_link and icon_link.get("href"):
            favicon_href = icon_link["href"]
            # Make relative URLs absolute
            if favicon_href.startswith("/"):
                from urllib.parse import urlparse

                parsed = urlparse(url)
                favicon_href = f"{parsed.scheme}://{parsed.netloc}{favicon_href}"
            result["favicon"] = favicon_href

    except httpx.TimeoutException:
        logger.warning(f"Timeout scraping metadata from: {url}")
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error scraping {url}: {e.response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to scrape metadata from {url}: {e}")

    return result

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from markdownify import markdownify
from collections import deque
from typing import Optional

from besser.agent.exceptions.logger import logger


def normalize_url(url: str) -> str:
    """Normalize a URL by removing fragments and normalizing trailing slashes.

    Args:
        url: URL to normalize.

    Returns:
        The normalized URL string.
    """
    parsed = urlparse(url)

    # remove fragment (#section)
    parsed = parsed._replace(fragment="")

    path = parsed.path

    # normalize root path
    if path in ("", "/"):
        path = ""

    # remove trailing slash for non-root paths
    elif path.endswith("/"):
        path = path[:-1]

    parsed = parsed._replace(path=path)

    return urlunparse(parsed)


def crawl_website(
    initial_url: str,
    max_depth: int = 2,
    max_pages: int = 20,
    format: str = "markdown",
    base_url_prefix: Optional[str] = None,
) -> dict[str, str]:
    """
    BFS crawler that collects URLs starting with base_url_prefix (if provided).

    Arguments:
        initial_url: str, starting point of crawl
        max_depth: int, maximum link depth
        max_pages: int, maximum number of pages to crawl
        format: 'html' or 'markdown'
        base_url_prefix: str, optional, only URLs starting with this prefix are included

    Returns:
        A dictionary mapping each crawled URL to its content in the requested format
        (`html` or `markdown`).
    """
    assert format in ["html", "markdown"]

    initial_url = normalize_url(initial_url)
    if base_url_prefix:
        base_url_prefix = normalize_url(base_url_prefix)

    base_domain = urlparse(initial_url).netloc
    visited = set()
    results = {}
    queue = deque([(initial_url, 0)])

    def fetch_html(url: str) -> Optional[str]:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.text
        except Exception:
            return None

    while queue and len(results) < max_pages:
        url, depth = queue.popleft()

        if depth > max_depth or url in visited:
            continue

        visited.add(url)
        html = fetch_html(url)
        if not html:
            continue

        logger.debug(f'[Depth {depth}] Crawling {url}')

        # store content
        if format == "markdown":
            results[url] = markdownify(html)
        else:
            results[url] = html

        if depth == max_depth:
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"]).split("#")[0]
            link = normalize_url(link)

            parsed = urlparse(link)

            # only crawl same domain
            if parsed.netloc != base_domain:
                continue

            # only crawl URLs starting with base_url_prefix (if set)
            if base_url_prefix and not link.startswith(base_url_prefix):
                continue

            if link not in visited:
                queue.append((link, depth + 1))

    return results

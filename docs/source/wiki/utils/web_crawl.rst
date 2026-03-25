Web Crawl
=========

The ``web_crawl`` utility provides a simple breadth-first crawler to collect
web pages from a given domain. It can return either raw HTML or Markdown content,
which is useful for grounding LLM prompts with website knowledge.

Basic usage
-----------

.. code:: python

    from baf.utils.web_crawl import crawl_website

    pages = crawl_website(
        initial_url="https://besser-pearl.org/",
        max_depth=2,
        max_pages=20,
        format="markdown",
        base_url_prefix="https://besser-pearl.org/",
    )

    # pages is a dict[str, str]: {url: content}

How it works
------------

- URLs are normalized with :func:`baf.utils.web_crawl.normalize_url`.
- Crawling is breadth-first up to ``max_depth`` and ``max_pages``.
- Links are restricted to the same domain as ``initial_url``.
- If ``base_url_prefix`` is provided, only matching URLs are included.

API References
--------------

- normalize_url(): :func:`baf.utils.web_crawl.normalize_url`
- crawl_website(): :func:`baf.utils.web_crawl.crawl_website`

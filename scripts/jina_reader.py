#!/usr/bin/env python
"""Fetch a URL through Jina Reader and print readable Markdown."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request


DEFAULT_TIMEOUT = 45
DIRECT_PREFIX = "https://r.jina.ai/http://"


def reader_url(url: str) -> str:
    normalized = url.strip()
    if not normalized.startswith(("http://", "https://")):
        raise SystemExit("URL must start with http:// or https://")
    if normalized.startswith("https://r.jina.ai/http://") or normalized.startswith("https://r.jina.ai/http://r.jina.ai/http://"):
        return normalized
    return f"{DIRECT_PREFIX}{normalized}"


def fetch(url: str, timeout: int) -> str:
    request = urllib.request.Request(
        reader_url(url),
        headers={
            "User-Agent": "bedtime-news-jina-reader/1.0",
            "Accept": "text/plain, text/markdown, */*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Jina Reader HTTP {error.code}: {body[:1000]}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Jina Reader request failed: {error}") from error


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Read a webpage via Jina Reader.")
    parser.add_argument("url", help="Original http(s) URL.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-chars", type=int, default=0, help="Truncate output to this many chars.")
    parser.add_argument("--show-reader-url", action="store_true", help="Print the generated r.jina.ai URL.")
    args = parser.parse_args()

    if args.show_reader_url:
        print(reader_url(args.url))
        return

    text = fetch(args.url, max(5, args.timeout))
    if args.max_chars and len(text) > args.max_chars:
        text = text[: args.max_chars].rstrip() + "\n\n[truncated]"
    sys.stdout.write(text)


if __name__ == "__main__":
    main()

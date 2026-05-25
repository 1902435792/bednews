#!/usr/bin/env python
"""Small AnySearch JSON-RPC helper for Codex/Antigravity skill runs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_ENDPOINT = "https://api.anysearch.com/mcp"
SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, ""))
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def call_anysearch(command: str, arguments: dict) -> dict:
    endpoint = os.environ.get("ANYSEARCH_ENDPOINT", DEFAULT_ENDPOINT).strip() or DEFAULT_ENDPOINT
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": command, "arguments": arguments},
        },
        ensure_ascii=False,
    ).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("ANYSEARCH_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    timeout = env_int("ANYSEARCH_TIMEOUT_MS", 30_000, 1_000, 120_000) / 1000

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"AnySearch HTTP {error.code}: {body}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"AnySearch request failed: {error}") from error

    if "error" in data:
        raise SystemExit(f"AnySearch error: {json.dumps(data['error'], ensure_ascii=False)}")
    return data.get("result", data)


def extract_text(result: dict) -> str:
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return str(item.get("text", "")).strip()
    return json.dumps(result, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call AnySearch from a local skill script.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Run realtime search.")
    search.add_argument("query")
    search.add_argument("--domain")
    search.add_argument("--sub-domain")
    search.add_argument("--content-types", default="news,doc,academic")
    search.add_argument("--freshness", choices=["day", "week", "month", "year"])
    search.add_argument("--zone", choices=["cn", "intl"])
    search.add_argument("--max-results", type=int, default=8)
    search.add_argument("--json", action="store_true", help="Print raw JSON-RPC result JSON.")

    domains = subparsers.add_parser("list_domains", help="List AnySearch vertical domains.")
    domains.add_argument("--domain")
    domains.add_argument("--json", action="store_true", help="Print raw JSON-RPC result JSON.")

    batch = subparsers.add_parser("batch_search", help="Run 1-5 searches in one call.")
    batch.add_argument("queries", nargs="+")
    batch.add_argument("--content-types", default="news,doc,academic")
    batch.add_argument("--freshness", choices=["day", "week", "month", "year"])
    batch.add_argument("--zone", choices=["cn", "intl"])
    batch.add_argument("--max-results", type=int, default=6)
    batch.add_argument("--json", action="store_true", help="Print raw JSON-RPC result JSON.")

    extract = subparsers.add_parser("extract", help="Extract readable text from a URL.")
    extract.add_argument("url")
    extract.add_argument("--json", action="store_true", help="Print raw JSON-RPC result JSON.")
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv(SKILL_ROOT / ".env")
    args = build_parser().parse_args()

    if args.command == "search":
        arguments = {
            "query": args.query,
            "content_types": split_csv(args.content_types),
            "max_results": args.max_results,
        }
        for key in ("domain", "freshness", "zone"):
            value = getattr(args, key, None)
            if value:
                arguments[key] = value
        if args.sub_domain:
            arguments["sub_domain"] = args.sub_domain
    elif args.command == "list_domains":
        arguments = {"domain": args.domain} if args.domain else {}
    elif args.command == "batch_search":
        arguments = {
            "queries": [
                {
                    "query": query,
                    "content_types": split_csv(args.content_types),
                    "freshness": args.freshness,
                    "zone": args.zone,
                    "max_results": args.max_results,
                }
                for query in args.queries[:5]
            ]
        }
    elif args.command == "extract":
        arguments = {"url": args.url}
    else:
        raise SystemExit(f"Unsupported command: {args.command}")

    result = call_anysearch(args.command, arguments)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(extract_text(result))


if __name__ == "__main__":
    main()

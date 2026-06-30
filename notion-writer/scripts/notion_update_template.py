#!/usr/bin/env python3
"""Template for replacing or appending structured blocks on a Notion page.

Copy this script into a task workspace and customize PAGE_ID, properties, and
build_blocks(). Keep secrets in NOTION_TOKEN or a local token file.
"""

import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


NOTION_VERSION = "2022-06-28"
PAGE_ID = "replace-with-page-id"
TOKEN_FILE = Path(os.environ["NOTION_TOKEN_FILE"]) if os.environ.get("NOTION_TOKEN_FILE") else None


def get_token():
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    if TOKEN_FILE and TOKEN_FILE.exists() and TOKEN_FILE.is_file():
        text = TOKEN_FILE.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"(ntn_[A-Za-z0-9_-]+|secret_[A-Za-z0-9_-]+)", text)
        if match:
            return match.group(1)
    raise SystemExit("Set NOTION_TOKEN or NOTION_TOKEN_FILE before running")


def notion_request(method, url, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_error = None
    for attempt in range(1, 4):
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {get_token()}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            if exc.code == 429 and attempt < 3:
                time.sleep(1.5 * attempt)
                continue
            raise SystemExit(f"Notion API error {exc.code}: {body[:1200]}")
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(1.5 * attempt)
                continue
    raise SystemExit(f"Notion request failed after retries: {last_error}")


def rich_text(text):
    chunks = []
    while text:
        part, text = text[:1900], text[1900:]
        chunks.append({"type": "text", "text": {"content": part}})
    return chunks or [{"type": "text", "text": {"content": ""}}]


def text_block(block_type, text):
    return {"object": "block", "type": block_type, block_type: {"rich_text": rich_text(text)}}


def paragraph(text):
    return text_block("paragraph", text)


def h1(text):
    return text_block("heading_1", text)


def h2(text):
    return text_block("heading_2", text)


def h3(text):
    return text_block("heading_3", text)


def bullet(text):
    return text_block("bulleted_list_item", text)


def numbered(text):
    return text_block("numbered_list_item", text)


def quote(text):
    return text_block("quote", text)


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def callout(text, icon="💡"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {"rich_text": rich_text(text), "icon": {"type": "emoji", "emoji": icon}},
    }


def code(text, language="plain text"):
    return {"object": "block", "type": "code", "code": {"rich_text": rich_text(text), "language": language}}


def title_prop(title):
    return {"title": rich_text(title)}


def multi_select_prop(names):
    return {"multi_select": [{"name": name} for name in names]}


def fetch_children(block_id):
    results = []
    cursor = None
    while True:
        params = {"page_size": "100"}
        if cursor:
            params["start_cursor"] = cursor
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?{urllib.parse.urlencode(params)}"
        data = notion_request("GET", url)
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            return results
        cursor = data.get("next_cursor")


def archive_existing_children(page_id):
    children = fetch_children(page_id)
    print(f"Archiving {len(children)} old blocks...", flush=True)
    for index, child in enumerate(children, start=1):
        notion_request("PATCH", f"https://api.notion.com/v1/blocks/{child['id']}", {"archived": True})
        if index % 25 == 0 or index == len(children):
            print(f"Archived {index}/{len(children)}", flush=True)


def append_children(page_id, blocks):
    print(f"Appending {len(blocks)} blocks...", flush=True)
    for index in range(0, len(blocks), 100):
        notion_request(
            "PATCH",
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            {"children": blocks[index : index + 100]},
        )
        print(f"Appended {min(index + 100, len(blocks))}/{len(blocks)}", flush=True)


def build_blocks():
    return [
        h1("Replace with document title"),
        quote("Replace with document positioning or summary."),
        divider(),
        h2("Context"),
        bullet("Replace with the first point."),
    ]


def update_page(replace=False):
    title = "Replace with document title"
    notion_request(
        "PATCH",
        f"https://api.notion.com/v1/pages/{PAGE_ID}",
        {
            "properties": {"Doc name": title_prop(title)},
            "icon": {"type": "emoji", "emoji": "📘"},
        },
    )
    if replace:
        archive_existing_children(PAGE_ID)
    append_children(PAGE_ID, build_blocks())
    data = notion_request("GET", f"https://api.notion.com/v1/pages/{PAGE_ID}")
    print(data.get("url", "updated"))


if __name__ == "__main__":
    update_page(replace=False)

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts" / "group"
API_BASE = "http://127.0.0.1:6808"
NOTEBOOK_ID = "20250702222801-kitbre8"
AUTH_HEADER = "Basic cm9vdDoxMjM0NTY="
TZ = timezone(timedelta(hours=8))

TARGET_TITLES = [
    "BlindSpot-Ahiz",
    "ecbw-Ahiz",
    "meltdown2",
    "Local",
    "Acfun",
    "Show",
    "SDL",
    "group",
]


def api_request(path: str, payload: dict | None = None, *, method: str = "POST") -> dict:
    body = None
    headers = {"Authorization": AUTH_HEADER}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(f"{API_BASE}{path}", data=body, headers=headers, method=method)
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def download_asset(name: str, destination: Path) -> None:
    request = Request(
        f"{API_BASE}/assets/{quote(name)}",
        headers={"Authorization": AUTH_HEADER},
        method="GET",
    )
    with urlopen(request) as response:
        destination.write_bytes(response.read())


def slugify_title(title: str) -> str:
    return title.replace("/", "-").replace("\\", "-").strip()


def format_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, TZ).isoformat()


def sql_value(value: str) -> str:
    return value.replace("'", "''")


def query_single_value(statement: str) -> str | None:
    result = api_request("/api/query/sql", {"stmt": statement})
    rows = result.get("data") or []
    if not rows:
        return None
    return rows[0].get("id")


def get_doc_html(doc_id: str) -> str:
    start_id = query_single_value(
        f"select id from blocks where root_id = '{sql_value(doc_id)}' and id != '{sql_value(doc_id)}' order by sort asc limit 1"
    )
    end_id = query_single_value(
        f"select id from blocks where root_id = '{sql_value(doc_id)}' and id != '{sql_value(doc_id)}' order by sort desc limit 1"
    )
    payload = {
        "id": doc_id,
        "startID": start_id or doc_id,
        "endID": end_id or doc_id,
        "highlight": False,
    }
    result = api_request("/api/filetree/getDoc", payload)
    return (result.get("data") or {}).get("content", "")


def clean_text(value: str) -> str:
    return value.replace("\u200b", "").replace("\xa0", " ").strip()


def escape_inline_code(text: str) -> str:
    return text.replace("`", "\\`")


def render_children(node: Tag, assets: set[str]) -> str:
    parts: list[str] = []
    for child in node.children:
        parts.append(render_inline(child, assets))
    return "".join(parts).replace("\u200b", "")


def render_inline(node: NavigableString | Tag, assets: set[str]) -> str:
    if isinstance(node, NavigableString):
        return str(node)

    if not isinstance(node, Tag):
        return ""

    if node.name == "br":
        return "\n"

    if node.name == "img":
        src = node.get("data-src") or node.get("src") or ""
        alt = clean_text(node.get("alt") or "image")
        if src.startswith("assets/"):
            asset_name = src.split("/", 1)[1]
            assets.add(asset_name)
            return f"![{alt}](assets/{asset_name})"
        return f"![{alt}]({src})"

    if node.name == "code":
        return f"`{escape_inline_code(clean_text(node.get_text()))}`"

    if node.name in {"strong", "b"}:
        text = clean_text(render_children(node, assets))
        return f"**{text}**" if text else ""

    if node.name in {"em", "i"}:
        text = clean_text(render_children(node, assets))
        return f"*{text}*" if text else ""

    if node.name == "a":
        href = node.get("href") or ""
        text = clean_text(render_children(node, assets)) or href
        return f"[{text}]({href})" if href else text

    return render_children(node, assets)


def render_block(block: Tag, assets: set[str]) -> str:
    block_type = block.get("data-type", "")
    if block_type == "NodeHeading":
        level = int((block.get("data-subtype") or "h1")[1:])
        text_node = block.find("div", attrs={"contenteditable": "true"})
        text = clean_text(render_children(text_node, assets)) if text_node else ""
        return f"{'#' * level} {text}".rstrip()

    if block_type == "NodeCodeBlock":
        language_node = block.select_one(".protyle-action__language")
        content_node = block.select_one(".hljs div[contenteditable='true']")
        language = clean_text(language_node.get_text()) if language_node else ""
        code = ""
        if content_node:
            code = content_node.get_text("", strip=False).replace("\r\n", "\n").strip("\n")
        fence = f"```{language}".rstrip()
        return f"{fence}\n{code}\n```".rstrip()

    if block_type == "NodeParagraph":
        text_node = block.find("div", attrs={"contenteditable": "true"})
        if not text_node:
            return ""
        content = render_children(text_node, assets).replace("\r\n", "\n").replace("\u200b", "")
        lines = [line.rstrip() for line in content.splitlines()]
        content = "\n".join(lines).strip()
        content = re.sub(r"^\s*!\[", "![", content)
        content = re.sub(r"\)\s*$", ")", content)
        return content

    if block_type in {"NodeList", "NodeListItem", "NodeBlockquote"}:
        text_node = block.find("div", attrs={"contenteditable": "true"})
        return clean_text(render_children(text_node, assets)) if text_node else ""

    return ""


def render_markdown(html_content: str) -> tuple[str, set[str]]:
    soup = BeautifulSoup(html_content, "html.parser")
    assets: set[str] = set()
    chunks: list[str] = []

    for block in soup.find_all("div", recursive=False):
        rendered = render_block(block, assets)
        if rendered:
            chunks.append(rendered)

    markdown = "\n\n".join(chunk for chunk in chunks if chunk.strip())
    markdown = markdown.replace("\u200b", "")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    return markdown, assets


def ensure_assets(asset_names: Iterable[str], assets_dir: Path) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)
    for asset_name in asset_names:
        destination = assets_dir / asset_name
        if destination.exists():
            continue
        download_asset(asset_name, destination)


def main() -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    response = api_request("/api/filetree/listDocsByPath", {"notebook": NOTEBOOK_ID, "path": "/"})
    files = (response.get("data") or {}).get("files") or []
    selected = [item for item in files if item.get("name", "").removesuffix(".sy") in TARGET_TITLES]
    selected.sort(key=lambda item: TARGET_TITLES.index(item["name"].removesuffix(".sy")))

    for item in selected:
        title = item["name"].removesuffix(".sy")
        slug = slugify_title(title)
        doc_id = item["id"]
        doc_dir = POSTS_DIR / slug
        assets_dir = doc_dir / "assets"
        markdown_path = doc_dir / f"{slug}.md"
        doc_dir.mkdir(parents=True, exist_ok=True)

        html_content = get_doc_html(doc_id)
        markdown_body, assets = render_markdown(html_content)
        ensure_assets(assets, assets_dir)

        frontmatter = "\n".join(
            [
                "---",
                f"title: {title}",
                f"date: {format_timestamp(item['ctime'])}",
                f"lastmod: {format_timestamp(item['mtime'])}",
                "---",
                "",
            ]
        )
        markdown_path.write_text(frontmatter + markdown_body, encoding="utf-8")


if __name__ == "__main__":
    main()

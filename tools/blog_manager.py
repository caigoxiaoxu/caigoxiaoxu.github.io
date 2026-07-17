from __future__ import annotations

import html
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
THEME_PATH = ROOT / "theme-custom.css"
INDEX_PATH = ROOT / "index.html"
APP_PATH = ROOT / "app.js"
FRIENDS_ASSET_DIRNAME = "assets/friends"
CACHE_VERSION_PATTERN = re.compile(r"202\d{5}-\d+")
ASSET_LINK_PATTERN = re.compile(r"!\[[^\]]*]\(([^)]+)\)|<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
HOME_KICKER_PATTERN = re.compile(
    r'(<span\s+class=["\']home-footer-kicker["\']\s*>)([\s\S]*?)(</span>)',
    re.IGNORECASE,
)
HOME_TITLE_PATTERN = re.compile(
    r'(<p\s+class=["\']home-footer-title["\']\s*>)([\s\S]*?)(</p>)',
    re.IGNORECASE,
)
FRIEND_CARD_PATTERN = re.compile(
    r'<a\s+href=["\'](?P<link>[^"\']+)["\']\s+class=["\']friend-card["\'][^>]*>'
    r'[\s\S]*?<img\s+src=["\'](?P<avatar>[^"\']*)["\'][^>]*>'
    r'[\s\S]*?<strong\s+class=["\']friend-name["\']>(?P<name>[\s\S]*?)</strong>'
    r'[\s\S]*?<span\s+class=["\']friend-meta["\']>(?P<description>[\s\S]*?)</span>'
    r'[\s\S]*?</a>',
    re.IGNORECASE,
)
CATEGORY_ALIASES = {
    "mazesec记录": "mazesec",
}
LOCAL_PROXY_PATTERN = re.compile(r"^(?:https?://)?(?:127\.0\.0\.1|localhost):(\d+)", re.IGNORECASE)

THEME_PRESETS = {
    "紫粉默认": {
        "accent": "#a855f7",
        "accent_strong": "#7e22ce",
        "accent_soft": "rgba(168, 85, 247, 0.14)",
        "warning": "#ec4899",
        "code": "#22d3ee",
        "dark_accent": "#c084fc",
        "dark_strong": "#f0abfc",
        "dark_soft": "rgba(192, 132, 252, 0.16)",
        "dark_warning": "#f472b6",
        "dark_code": "#2dd4bf",
    },
    "青绿冷调": {
        "accent": "#0f766e",
        "accent_strong": "#115e59",
        "accent_soft": "rgba(15, 118, 110, 0.14)",
        "warning": "#2563eb",
        "code": "#06b6d4",
        "dark_accent": "#2dd4bf",
        "dark_strong": "#99f6e4",
        "dark_soft": "rgba(45, 212, 191, 0.16)",
        "dark_warning": "#60a5fa",
        "dark_code": "#22d3ee",
    },
    "赤橙醒目": {
        "accent": "#dc2626",
        "accent_strong": "#b91c1c",
        "accent_soft": "rgba(220, 38, 38, 0.12)",
        "warning": "#f97316",
        "code": "#14b8a6",
        "dark_accent": "#fb7185",
        "dark_strong": "#fecdd3",
        "dark_soft": "rgba(251, 113, 133, 0.15)",
        "dark_warning": "#fdba74",
        "dark_code": "#5eead4",
    },
    "蓝灰克制": {
        "extra_root": {
            "page-glow": "rgba(37, 99, 235, 0.08)",
            "page-overlay-top": "rgba(241, 245, 249, 0.54)",
            "page-overlay-bottom": "rgba(248, 250, 252, 0.86)",
            "page-image-tint": "rgba(37, 99, 235, 0.14)",
            "sidebar-bg": "#f8fafc",
            "sidebar-panel": "#ffffff",
            "sidebar-muted": "#64748b",
            "sidebar-border": "#dbe4f0",
            "sidebar-hover": "#eff6ff",
            "sidebar-active": "linear-gradient(90deg, rgba(37, 99, 235, 0.18), rgba(8, 145, 178, 0.1))",
            "sidebar-input-border": "#cbd5e1",
            "sidebar-chip-bg": "#e0f2fe",
            "sidebar-mark-border": "#bfdbfe",
            "border-color": "#dbe4f0",
            "strong-border": "#b6c7dc",
        },
        "extra_dark": {
            "page-glow": "rgba(96, 165, 250, 0.11)",
            "page-overlay-top": "rgba(15, 23, 42, 0.3)",
            "page-overlay-bottom": "rgba(15, 23, 42, 0.7)",
            "page-image-tint": "rgba(96, 165, 250, 0.18)",
            "sidebar-bg": "#0f172a",
            "sidebar-panel": "#111827",
            "sidebar-muted": "#94a3b8",
            "sidebar-border": "rgba(148, 163, 184, 0.18)",
            "sidebar-hover": "rgba(96, 165, 250, 0.12)",
            "sidebar-active": "linear-gradient(90deg, rgba(96, 165, 250, 0.26), rgba(34, 211, 238, 0.1))",
            "sidebar-input-border": "rgba(148, 163, 184, 0.2)",
            "sidebar-chip-bg": "rgba(96, 165, 250, 0.12)",
            "sidebar-mark-border": "rgba(125, 211, 252, 0.22)",
            "border-color": "#263548",
            "strong-border": "#3f5874",
        },
        "accent": "#2563eb",
        "accent_strong": "#1d4ed8",
        "accent_soft": "rgba(37, 99, 235, 0.13)",
        "warning": "#64748b",
        "code": "#0891b2",
        "dark_accent": "#60a5fa",
        "dark_strong": "#bfdbfe",
        "dark_soft": "rgba(96, 165, 250, 0.15)",
        "dark_warning": "#94a3b8",
        "dark_code": "#67e8f9",
    },
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def safe_name(value: str) -> str:
    value = value.strip()
    value = value.removesuffix(".md")
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value)
    value = re.sub(r"\s+", "-", value)
    value = value.strip(" .-")
    return value or "untitled"


def normalize_category(value: str) -> str:
    category = value.strip() or "其他靶场"
    return CATEGORY_ALIASES.get(category, category)


def guess_article_name(path: Path) -> str:
    name = path.stem
    return name.removesuffix(".md")


def ensure_within(base: Path, target: Path) -> Path:
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    if target_resolved != base_resolved and base_resolved not in target_resolved.parents:
        raise ValueError(f"路径越界：{target}")
    return target_resolved


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def home_index_path() -> Path:
    return POSTS_DIR / "LEA" / "index.md"


def friends_path() -> Path:
    return POSTS_DIR / "LEA" / "Friends.md"


def remove_frontmatter(markdown: str) -> str:
    text = markdown.lstrip("\ufeff\r\n")
    match = re.match(r"^---\r?\n[\s\S]*?\r?\n---\r?\n?", text)
    return text[match.end() :] if match else text


def with_frontmatter(markdown: str, title: str, date_value: str) -> str:
    body = remove_frontmatter(markdown).lstrip("\n")
    frontmatter = textwrap.dedent(
        f"""\
        ---
        title: {title}
        date: {date_value}
        lastmod: {date_value}
        ---

        """
    )
    return frontmatter + body


def find_markdown_file(root: Path) -> Path:
    candidates = [
        path
        for path in root.rglob("*.md")
        if "__MACOSX" not in path.parts and not path.name.startswith(".")
    ]
    if not candidates:
        raise FileNotFoundError("压缩包里没有找到 Markdown 文件")
    candidates.sort(key=lambda path: (len(path.parts), path.name.lower()))
    return candidates[0]


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = ensure_within(destination, destination / member.filename)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source_file, target.open("wb") as target_file:
                shutil.copyfileobj(source_file, target_file)


def referenced_asset_paths(markdown: str) -> set[str]:
    assets: set[str] = set()
    for match in ASSET_LINK_PATTERN.finditer(markdown):
        raw = match.group(1) or match.group(2) or ""
        raw = raw.strip().split()[0].strip("<>\"'")
        if not raw or raw.startswith(("#", "/", "http://", "https://", "data:", "mailto:")):
            continue
        assets.add(raw.replace("\\", "/"))
    return assets


def copy_asset_path(source_parent: Path, destination_dir: Path, relative_path: str) -> None:
    source = (source_parent / relative_path).resolve()
    if not source.exists():
        return
    ensure_within(source_parent, source)

    target = ensure_within(destination_dir, destination_dir / relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def copy_article_assets(source_md: Path, destination_dir: Path, markdown: str) -> None:
    source_parent = source_md.parent
    referenced = referenced_asset_paths(markdown)

    for relative_path in sorted(referenced):
        copy_asset_path(source_parent, destination_dir, relative_path)

    assets_dir = source_parent / "assets"
    if assets_dir.exists():
        copy_asset_path(source_parent, destination_dir, "assets")


def run_main_py() -> str:
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(output or "main.py 运行失败")
    return output.strip() or "nav.json 和时间线已更新"


def current_cache_version() -> str:
    app_text = APP_PATH.read_text(encoding="utf-8")
    match = re.search(r"assetVersion\s*=\s*['\"]([^'\"]+)['\"]", app_text)
    if match:
        return match.group(1)

    index_text = INDEX_PATH.read_text(encoding="utf-8")
    match = CACHE_VERSION_PATTERN.search(index_text)
    return match.group(0) if match else f"{datetime.now():%Y%m%d}-0"


def next_cache_version() -> str:
    current = current_cache_version()
    today = datetime.now().strftime("%Y%m%d")
    match = re.match(r"^(\d{8})-(\d+)$", current)
    if not match or match.group(1) != today:
        return f"{today}-1"
    return f"{today}-{int(match.group(2)) + 1}"


def bump_asset_version() -> str:
    old_version = current_cache_version()
    new_version = next_cache_version()

    for path in (INDEX_PATH, APP_PATH):
        text = path.read_text(encoding="utf-8")
        text = text.replace(old_version, new_version)
        write_text(path, text)

    return new_version


def get_home_footer_text() -> tuple[str, str]:
    path = home_index_path()
    if not path.exists():
        return "", ""

    text = path.read_text(encoding="utf-8")
    kicker_match = HOME_KICKER_PATTERN.search(text)
    title_match = HOME_TITLE_PATTERN.search(text)
    kicker = html.unescape(kicker_match.group(2).strip()) if kicker_match else ""
    title = html.unescape(title_match.group(2).strip()) if title_match else ""
    return kicker, title


def update_home_footer_text(
    *,
    kicker: str,
    title: str,
    mode: str,
    separator: str = " · ",
) -> str:
    path = home_index_path()
    if not path.exists():
        raise FileNotFoundError(f"首页文件不存在：{path}")

    text = path.read_text(encoding="utf-8")
    if not HOME_TITLE_PATTERN.search(text):
        raise ValueError("没有找到 home-footer-title，无法更新首页文案")

    current_kicker, current_title = get_home_footer_text()
    next_title = title.strip()
    if not next_title:
        raise ValueError("请输入首页文案")

    normalized_mode = mode.strip().lower()
    if normalized_mode in {"添加", "add", "append"}:
        if current_title and next_title in current_title:
            final_title = current_title
        elif current_title:
            final_title = f"{current_title}{separator}{next_title}"
        else:
            final_title = next_title
    else:
        final_title = next_title

    final_kicker = kicker.strip() or current_kicker
    escaped_title = html.escape(final_title, quote=False)
    escaped_kicker = html.escape(final_kicker, quote=False)

    if final_kicker and HOME_KICKER_PATTERN.search(text):
        text = HOME_KICKER_PATTERN.sub(rf"\1{escaped_kicker}\3", text, count=1)
    text = HOME_TITLE_PATTERN.sub(rf"\1{escaped_title}\3", text, count=1)
    write_text(path, text)
    return bump_asset_version()


def split_markdown_frontmatter(markdown: str) -> tuple[str, str]:
    text = markdown.lstrip("\ufeff\r\n")
    match = re.match(r"^---\r?\n[\s\S]*?\r?\n---\r?\n?", text)
    if not match:
        return "", text
    return match.group(0).rstrip() + "\n", text[match.end() :].lstrip("\n")


def normalize_avatar_path(avatar: str) -> str:
    value = avatar.strip()
    if not value:
        return ""
    if re.match(r"^(?:https?:)?//", value, re.IGNORECASE) or value.startswith(("data:", "/")):
        return value

    source = Path(value)
    if not source.exists():
        return value.replace("\\", "/")

    target_dir = friends_path().parent / FRIENDS_ASSET_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe_name(source.name)
    shutil.copy2(source, target)
    return f"{FRIENDS_ASSET_DIRNAME}/{target.name}".replace("\\", "/")


def parse_friends() -> list[dict[str, str]]:
    path = friends_path()
    if not path.exists():
        return []
    _frontmatter, body = split_markdown_frontmatter(path.read_text(encoding="utf-8"))
    friends = []
    for match in FRIEND_CARD_PATTERN.finditer(body):
        friends.append(
            {
                "name": html.unescape(match.group("name").strip()),
                "link": html.unescape(match.group("link").strip()),
                "description": html.unescape(match.group("description").strip()),
                "avatar": html.unescape(match.group("avatar").strip()),
            }
        )
    return friends


def render_friends_markdown(friends: list[dict[str, str]]) -> str:
    frontmatter = textwrap.dedent(
        """\
        ---
        title: Friends
        date: 2026-04-24T14:05:00+08:00
        lastmod: 2026-04-24T14:05:00+08:00
        ---
        """
    )
    lines = [
        frontmatter.rstrip(),
        "",
        "# Friends",
        "",
        '<p class="friends-page-intro">记录一些朋友和常看的博客。</p>',
        "",
        '<div class="friends-grid">',
    ]
    for friend in friends:
        name = html.escape(friend["name"], quote=True)
        link = html.escape(friend["link"], quote=True)
        description = html.escape(friend["description"], quote=False)
        avatar = html.escape(friend["avatar"], quote=True)
        lines.extend(
            [
                f'  <a href="{link}" class="friend-card" target="_blank" rel="noreferrer">',
                f'    <img src="{avatar}" alt="{name}" class="friend-avatar">',
                '    <div class="friend-card-body">',
                f'      <strong class="friend-name">{name}</strong>',
                f'      <span class="friend-meta">{description}</span>',
                '    </div>',
                '  </a>',
                "",
            ]
        )
    lines.append("</div>")
    lines.append("")
    return "\n".join(lines)


def upsert_friend(
    *,
    name: str,
    link: str,
    description: str,
    avatar: str,
    overwrite: bool,
) -> str:
    clean_name = name.strip()
    clean_link = link.strip()
    if not clean_name:
        raise ValueError("请输入友链名称")
    if not clean_link:
        raise ValueError("请输入友链链接")

    clean_friend = {
        "name": clean_name,
        "link": clean_link,
        "description": description.strip(),
        "avatar": normalize_avatar_path(avatar),
    }
    friends = parse_friends()
    match_index = next(
        (
            index
            for index, friend in enumerate(friends)
            if friend["name"].casefold() == clean_name.casefold()
            or friend["link"].rstrip("/") == clean_link.rstrip("/")
        ),
        None,
    )
    if match_index is not None:
        if not overwrite:
            raise FileExistsError("已存在同名或同链接友链，请勾选覆盖")
        friends[match_index] = clean_friend
    else:
        friends.append(clean_friend)

    write_text(friends_path(), render_friends_markdown(friends))
    return bump_asset_version()


def import_article(
    source: Path,
    category: str,
    title: str,
    slug: str,
    date_value: str,
    overwrite: bool,
) -> Path:
    category_name = safe_name(normalize_category(category))
    slug_name = safe_name(slug or title or guess_article_name(source))
    destination_dir = POSTS_DIR / category_name / slug_name
    destination_md = destination_dir / f"{slug_name}.md"

    if destination_dir.exists() and not overwrite:
        raise FileExistsError(f"文章目录已存在：{destination_dir}")

    if destination_dir.exists() and overwrite:
        ensure_within(POSTS_DIR, destination_dir)
        shutil.rmtree(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory(prefix="blog-import-") as temp_dir:
            temp_root = Path(temp_dir)
            safe_extract_zip(source, temp_root)
            source_md = find_markdown_file(temp_root)
            markdown = read_text(source_md)
            copy_article_assets(source_md, destination_dir, markdown)
    elif source.suffix.lower() == ".md":
        source_md = source
        markdown = read_text(source_md)
        copy_article_assets(source_md, destination_dir, markdown)
    else:
        raise ValueError("请选择 .zip 或 .md 文件")

    final_title = title.strip() or source_md.stem
    write_text(destination_md, with_frontmatter(markdown, final_title, date_value))
    run_main_py()
    bump_asset_version()
    return destination_md


def write_theme_preset(name: str) -> str:
    preset = THEME_PRESETS[name]
    root_vars = {
        **preset.get("extra_root", {}),
        "accent-color": preset["accent"],
        "accent-strong": preset["accent_strong"],
        "accent-soft": preset["accent_soft"],
        "warning-color": preset["warning"],
        "code-accent": preset["code"],
    }
    dark_vars = {
        **preset.get("extra_dark", {}),
        "accent-color": preset["dark_accent"],
        "accent-strong": preset["dark_strong"],
        "accent-soft": preset["dark_soft"],
        "warning-color": preset["dark_warning"],
        "code-accent": preset["dark_code"],
    }
    root_lines = "\n".join(f"    --{key}: {value};" for key, value in root_vars.items())
    dark_lines = "\n".join(f"    --{key}: {value};" for key, value in dark_vars.items())
    css = (
        "/* Generated by tools/blog_manager.py. Edit with the blog manager UI. */\n"
        ":root {\n"
        f"{root_lines}\n"
        "}\n\n"
        "[data-theme=\"dark\"] {\n"
        f"{dark_lines}\n"
        "}\n"
    )
    write_text(THEME_PATH, css)
    return bump_asset_version()


def existing_categories() -> list[str]:
    categories = []
    if POSTS_DIR.exists():
        categories = sorted(
            path.name for path in POSTS_DIR.iterdir() if path.is_dir() and path.name != "LEA"
        )
    defaults = ["其他靶场", "mazesec"]
    return list(dict.fromkeys([*defaults, *categories]))


def git_config_value(name: str) -> str:
    result = subprocess.run(
        ["git", "config", "--get", name],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def local_proxy_is_down(proxy: str) -> bool:
    match = LOCAL_PROXY_PATTERN.match(proxy.strip())
    if not match:
        return False
    port = int(match.group(1))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.6)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def git_push_command() -> tuple[list[str], str | None]:
    proxies = [
        git_config_value("https.proxy"),
        git_config_value("http.proxy"),
    ]
    if any(proxy and local_proxy_is_down(proxy) for proxy in proxies):
        return (
            ["git", "-c", "http.proxy=", "-c", "https.proxy=", "push", "origin", "main"],
            "检测到本地 Git 代理端口不可用，本次 push 将临时绕过代理。",
        )
    return ["git", "push", "origin", "main"], None


def push_failed_because_proxy(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stdout or ''}\n{result.stderr or ''}".lower()
    proxy_markers = [
        "127.0.0.1",
        "localhost",
        "proxy",
        "could not connect to server",
        "failed to connect",
    ]
    return result.returncode != 0 and any(marker in output for marker in proxy_markers)


class BlogManager(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Ahiz2 Blog Manager")
        self.geometry("760x560")
        self.minsize(720, 520)

        self.source_var = StringVar()
        self.category_var = StringVar(value="其他靶场")
        self.title_var = StringVar()
        self.slug_var = StringVar()
        self.date_var = StringVar(value=now_iso())
        self.overwrite_var = BooleanVar(value=False)
        self.theme_var = StringVar(value="蓝灰克制")
        home_kicker, home_title = get_home_footer_text()
        self.home_kicker_var = StringVar(value=home_kicker or "持续更新中")
        self.home_text_var = StringVar(value=home_title)
        self.home_mode_var = StringVar(value="overwrite")
        self.home_separator_var = StringVar(value=" · ")
        self.friend_name_var = StringVar()
        self.friend_link_var = StringVar()
        self.friend_description_var = StringVar()
        self.friend_avatar_var = StringVar()
        self.friend_overwrite_var = BooleanVar(value=True)
        self.commit_var = StringVar(value="update blog")

        self.output = None
        self.build_ui()

    def build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=BOTH, expand=True, padx=12, pady=12)

        import_tab = ttk.Frame(notebook, padding=14)
        theme_tab = ttk.Frame(notebook, padding=14)
        home_tab = ttk.Frame(notebook, padding=14)
        friends_tab = ttk.Frame(notebook, padding=14)
        git_tab = ttk.Frame(notebook, padding=14)
        notebook.add(import_tab, text="文章导入")
        notebook.add(theme_tab, text="外观设置")
        notebook.add(home_tab, text="首页文案")
        notebook.add(friends_tab, text="友链管理")
        notebook.add(git_tab, text="Git 上传")

        self.build_import_tab(import_tab)
        self.build_theme_tab(theme_tab)
        self.build_home_tab(home_tab)
        self.build_friends_tab(friends_tab)
        self.build_git_tab(git_tab)
        self.output = self.add_output(self)

    def add_labeled_entry(self, parent: ttk.Frame, label: str, variable: StringVar) -> ttk.Entry:
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=6)
        ttk.Label(row, text=label, width=12).pack(side=LEFT)
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side=LEFT, fill=X, expand=True)
        return entry

    def build_import_tab(self, parent: ttk.Frame) -> None:
        source_row = ttk.Frame(parent)
        source_row.pack(fill=X, pady=6)
        ttk.Label(source_row, text="文章文件", width=12).pack(side=LEFT)
        ttk.Entry(source_row, textvariable=self.source_var).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(source_row, text="选择", command=self.browse_source).pack(side=RIGHT, padx=(8, 0))

        category_row = ttk.Frame(parent)
        category_row.pack(fill=X, pady=6)
        ttk.Label(category_row, text="分类", width=12).pack(side=LEFT)
        ttk.Combobox(category_row, textvariable=self.category_var, values=existing_categories()).pack(
            side=LEFT,
            fill=X,
            expand=True,
        )
        self.add_labeled_entry(parent, "标题", self.title_var)
        self.add_labeled_entry(parent, "目录名", self.slug_var)
        self.add_labeled_entry(parent, "发布时间", self.date_var)
        ttk.Checkbutton(parent, text="覆盖已存在的同名文章目录", variable=self.overwrite_var).pack(anchor="w", pady=8)

        hint = (
            "支持选择思源导出的 .md.zip 或单个 .md。工具会复制 assets、补 frontmatter、"
            "放入 _posts/<分类>/<目录名>/，并自动运行 main.py。"
        )
        ttk.Label(parent, text=hint, wraplength=660, foreground="#64748b").pack(fill=X, pady=(4, 12))
        ttk.Button(parent, text="导入文章并更新导航", command=self.import_current_article).pack(anchor="w")

    def build_theme_tab(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=6)
        ttk.Label(row, text="主题预设", width=12).pack(side=LEFT)
        combo = ttk.Combobox(row, textvariable=self.theme_var, values=list(THEME_PRESETS), state="readonly")
        combo.pack(side=LEFT, fill=X, expand=True)

        ttk.Label(
            parent,
            text="这里会写入 theme-custom.css，并自动更新缓存版本。",
            wraplength=660,
            foreground="#64748b",
        ).pack(fill=X, pady=(4, 12))
        ttk.Button(parent, text="应用外观设置", command=self.apply_theme).pack(anchor="w")

    def build_home_tab(self, parent: ttk.Frame) -> None:
        self.add_labeled_entry(parent, "小标题", self.home_kicker_var)
        self.add_labeled_entry(parent, "文案", self.home_text_var)

        mode_row = ttk.Frame(parent)
        mode_row.pack(fill=X, pady=6)
        ttk.Label(mode_row, text="模式", width=12).pack(side=LEFT)
        ttk.Radiobutton(mode_row, text="覆盖", variable=self.home_mode_var, value="overwrite").pack(side=LEFT)
        ttk.Radiobutton(mode_row, text="添加", variable=self.home_mode_var, value="append").pack(side=LEFT, padx=12)

        self.add_labeled_entry(parent, "分隔符", self.home_separator_var)
        ttk.Label(
            parent,
            text="覆盖会替换首页底部大字；添加会把新文案追加到现有文案后面，并自动更新缓存版本。",
            wraplength=660,
            foreground="#64748b",
        ).pack(fill=X, pady=(4, 12))
        buttons = ttk.Frame(parent)
        buttons.pack(fill=X, pady=6)
        ttk.Button(buttons, text="刷新当前文案", command=self.refresh_home_text).pack(side=LEFT)
        ttk.Button(buttons, text="应用首页文案", command=self.apply_home_text).pack(side=LEFT, padx=8)

    def build_friends_tab(self, parent: ttk.Frame) -> None:
        self.add_labeled_entry(parent, "名称", self.friend_name_var)
        self.add_labeled_entry(parent, "链接", self.friend_link_var)
        self.add_labeled_entry(parent, "描述", self.friend_description_var)

        avatar_row = ttk.Frame(parent)
        avatar_row.pack(fill=X, pady=6)
        ttk.Label(avatar_row, text="头像", width=12).pack(side=LEFT)
        ttk.Entry(avatar_row, textvariable=self.friend_avatar_var).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(avatar_row, text="本地头像", command=self.browse_friend_avatar).pack(side=RIGHT, padx=(8, 0))

        ttk.Checkbutton(parent, text="存在同名/同链接时覆盖", variable=self.friend_overwrite_var).pack(anchor="w", pady=8)
        ttk.Label(
            parent,
            text="头像可以填远程 URL，也可以选择本地图片；本地图片会复制到 _posts/LEA/assets/friends/。",
            wraplength=660,
            foreground="#64748b",
        ).pack(fill=X, pady=(4, 12))

        buttons = ttk.Frame(parent)
        buttons.pack(fill=X, pady=6)
        ttk.Button(buttons, text="添加/更新友链", command=self.apply_friend).pack(side=LEFT)

    def build_git_tab(self, parent: ttk.Frame) -> None:
        self.add_labeled_entry(parent, "提交信息", self.commit_var)
        buttons = ttk.Frame(parent)
        buttons.pack(fill=X, pady=8)
        ttk.Button(buttons, text="查看状态", command=self.show_git_status).pack(side=LEFT)
        ttk.Button(buttons, text="提交并推送", command=self.commit_and_push).pack(side=LEFT, padx=8)
        ttk.Label(
            parent,
            text="提交并推送会执行 git add .、git commit、git push origin main。",
            wraplength=660,
            foreground="#64748b",
        ).pack(fill=X, pady=(4, 0))

    def add_output(self, parent: ttk.Frame):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=False, padx=12, pady=(0, 12))
        ttk.Label(frame, text="运行日志").pack(anchor="w")
        text = self.create_text(frame)
        return text

    def create_text(self, parent: ttk.Frame):
        import tkinter as tk

        text = tk.Text(parent, height=8, wrap="word")
        text.pack(fill=BOTH, expand=True)
        return text

    def log(self, message: str) -> None:
        if self.output is None:
            return
        self.output.insert(END, message.rstrip() + "\n")
        self.output.see(END)

    def browse_source(self) -> None:
        path = filedialog.askopenfilename(
            title="选择文章文件",
            filetypes=[("Markdown or zip", "*.md *.zip"), ("All files", "*.*")],
        )
        if not path:
            return
        source = Path(path)
        self.source_var.set(str(source))
        guessed = guess_article_name(source)
        if not self.title_var.get().strip():
            self.title_var.set(guessed)
        if not self.slug_var.get().strip():
            self.slug_var.set(safe_name(guessed))
        try:
            timestamp = datetime.fromtimestamp(source.stat().st_mtime).astimezone().isoformat(timespec="seconds")
            self.date_var.set(timestamp)
        except OSError:
            pass

    def browse_friend_avatar(self) -> None:
        path = filedialog.askopenfilename(
            title="选择头像图片",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.webp *.svg"), ("All files", "*.*")],
        )
        if path:
            self.friend_avatar_var.set(path)

    def import_current_article(self) -> None:
        try:
            source = Path(self.source_var.get().strip())
            if not source.exists():
                raise FileNotFoundError("请选择存在的文章文件")
            imported = import_article(
                source=source,
                category=self.category_var.get(),
                title=self.title_var.get(),
                slug=self.slug_var.get(),
                date_value=self.date_var.get().strip() or now_iso(),
                overwrite=self.overwrite_var.get(),
            )
            self.log(f"导入成功：{imported}")
            self.log(f"资源版本已更新为：{current_cache_version()}")
            messagebox.showinfo("完成", "文章已导入，导航和缓存版本已更新")
        except Exception as exc:
            self.log(f"导入失败：{exc}")
            messagebox.showerror("导入失败", str(exc))

    def apply_theme(self) -> None:
        try:
            version = write_theme_preset(self.theme_var.get())
            self.log(f"已应用主题：{self.theme_var.get()}")
            self.log(f"资源版本已更新为：{version}")
            messagebox.showinfo("完成", "外观设置已写入，缓存版本也已更新")
        except Exception as exc:
            self.log(f"应用主题失败：{exc}")
            messagebox.showerror("应用主题失败", str(exc))

    def refresh_home_text(self) -> None:
        kicker, title = get_home_footer_text()
        self.home_kicker_var.set(kicker)
        self.home_text_var.set(title)
        self.log("已刷新首页文案。")

    def apply_home_text(self) -> None:
        try:
            version = update_home_footer_text(
                kicker=self.home_kicker_var.get(),
                title=self.home_text_var.get(),
                mode=self.home_mode_var.get(),
                separator=self.home_separator_var.get() or " · ",
            )
            _kicker, title = get_home_footer_text()
            self.home_text_var.set(title)
            self.log(f"已更新首页文案：{title}")
            self.log(f"资源版本已更新为：{version}")
            messagebox.showinfo("完成", "首页文案已更新，缓存版本也已更新")
        except Exception as exc:
            self.log(f"更新首页文案失败：{exc}")
            messagebox.showerror("更新首页文案失败", str(exc))

    def apply_friend(self) -> None:
        try:
            version = upsert_friend(
                name=self.friend_name_var.get(),
                link=self.friend_link_var.get(),
                description=self.friend_description_var.get(),
                avatar=self.friend_avatar_var.get(),
                overwrite=self.friend_overwrite_var.get(),
            )
            self.log(f"已添加/更新友链：{self.friend_name_var.get().strip()}")
            self.log(f"资源版本已更新为：{version}")
            messagebox.showinfo("完成", "友链已更新，缓存版本也已更新")
        except Exception as exc:
            self.log(f"更新友链失败：{exc}")
            messagebox.showerror("更新友链失败", str(exc))

    def run_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        output = (result.stdout or "") + (result.stderr or "")
        if output.strip():
            self.log(output)
        return result

    def show_git_status(self) -> None:
        self.log("$ git status --short --branch")
        self.run_command(["git", "status", "--short", "--branch"])

    def commit_and_push(self) -> None:
        try:
            message = self.commit_var.get().strip() or "update blog"
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            status_text = status.stdout.strip()
            if not status_text:
                messagebox.showinfo("没有改动", "当前没有需要提交的改动。")
                return

            confirmed = messagebox.askyesno(
                "确认提交",
                f"将提交并推送以下改动：\n\n{status_text}\n\n继续吗？",
            )
            if not confirmed:
                self.log("已取消提交。")
                return

            self.log("$ git add .")
            add_result = self.run_command(["git", "add", "."])
            if add_result.returncode != 0:
                raise RuntimeError("git add 失败")

            self.log(f"$ git commit -m {message!r}")
            commit_result = self.run_command(["git", "commit", "-m", message])
            if commit_result.returncode != 0:
                if "nothing to commit" in ((commit_result.stdout or "") + (commit_result.stderr or "")):
                    self.log("没有需要提交的改动。")
                else:
                    raise RuntimeError("git commit 失败")

            push_command, proxy_note = git_push_command()
            if proxy_note:
                self.log(proxy_note)
            self.log("$ " + " ".join(push_command))
            push_result = self.run_command(push_command)
            if push_failed_because_proxy(push_result) and push_command[1:5] != ["-c", "http.proxy=", "-c", "https.proxy="]:
                retry_command = ["git", "-c", "http.proxy=", "-c", "https.proxy=", "push", "origin", "main"]
                self.log("检测到代理连接失败，正在临时绕过代理重试 push。")
                self.log("$ " + " ".join(retry_command))
                push_result = self.run_command(retry_command)
            if push_result.returncode != 0:
                raise RuntimeError("git push 失败")
            messagebox.showinfo("完成", "已推送到 GitHub，GitHub Pages 会自动部署。")
        except Exception as exc:
            self.log(f"上传失败：{exc}")
            messagebox.showerror("上传失败", str(exc))


def main() -> None:
    app = BlogManager()
    app.mainloop()


if __name__ == "__main__":
    main()

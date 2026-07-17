from __future__ import annotations

import re
import shutil
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
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value)
    value = re.sub(r"\s+", "-", value)
    value = value.strip(" .-")
    return value or "untitled"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


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


def copy_article_assets(source_md: Path, destination_dir: Path) -> None:
    source_parent = source_md.parent
    for item in source_parent.iterdir():
        if item == source_md:
            continue
        target = destination_dir / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        elif item.is_file():
            shutil.copy2(item, target)


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


def import_article(
    source: Path,
    category: str,
    title: str,
    slug: str,
    date_value: str,
    overwrite: bool,
) -> Path:
    category_name = safe_name(category)
    slug_name = safe_name(slug or title or source.stem)
    destination_dir = POSTS_DIR / category_name / slug_name
    destination_md = destination_dir / f"{slug_name}.md"

    if destination_dir.exists() and not overwrite:
        raise FileExistsError(f"文章目录已存在：{destination_dir}")

    destination_dir.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory(prefix="blog-import-") as temp_dir:
            temp_root = Path(temp_dir)
            with zipfile.ZipFile(source) as archive:
                archive.extractall(temp_root)
            source_md = find_markdown_file(temp_root)
            markdown = read_text(source_md)
            copy_article_assets(source_md, destination_dir)
    elif source.suffix.lower() == ".md":
        source_md = source
        markdown = read_text(source_md)
        copy_article_assets(source_md, destination_dir)
    else:
        raise ValueError("请选择 .zip 或 .md 文件")

    final_title = title.strip() or source_md.stem
    write_text(destination_md, with_frontmatter(markdown, final_title, date_value))
    run_main_py()
    return destination_md


def write_theme_preset(name: str) -> None:
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
        self.theme_var = StringVar(value="紫粉默认")
        self.commit_var = StringVar(value="update blog")

        self.output = None
        self.build_ui()

    def build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=BOTH, expand=True, padx=12, pady=12)

        import_tab = ttk.Frame(notebook, padding=14)
        theme_tab = ttk.Frame(notebook, padding=14)
        git_tab = ttk.Frame(notebook, padding=14)
        notebook.add(import_tab, text="文章导入")
        notebook.add(theme_tab, text="外观设置")
        notebook.add(git_tab, text="Git 上传")

        self.build_import_tab(import_tab)
        self.build_theme_tab(theme_tab)
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

        self.add_labeled_entry(parent, "分类", self.category_var)
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
            text="这里会写入 theme-custom.css，只覆盖主题色，不会改坏主体布局。",
            wraplength=660,
            foreground="#64748b",
        ).pack(fill=X, pady=(4, 12))
        ttk.Button(parent, text="应用外观设置", command=self.apply_theme).pack(anchor="w")

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
        guessed = source.stem.removesuffix(".md")
        if not self.title_var.get().strip():
            self.title_var.set(guessed)
        if not self.slug_var.get().strip():
            self.slug_var.set(safe_name(guessed))
        try:
            timestamp = datetime.fromtimestamp(source.stat().st_mtime).astimezone().isoformat(timespec="seconds")
            self.date_var.set(timestamp)
        except OSError:
            pass

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
            messagebox.showinfo("完成", "文章已导入，并已更新 nav.json / Timeline.md")
        except Exception as exc:
            self.log(f"导入失败：{exc}")
            messagebox.showerror("导入失败", str(exc))

    def apply_theme(self) -> None:
        try:
            write_theme_preset(self.theme_var.get())
            self.log(f"已应用主题：{self.theme_var.get()}")
            messagebox.showinfo("完成", "外观设置已写入 theme-custom.css")
        except Exception as exc:
            self.log(f"应用主题失败：{exc}")
            messagebox.showerror("应用主题失败", str(exc))

    def run_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
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

            self.log("$ git push origin main")
            push_result = self.run_command(["git", "push", "origin", "main"])
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

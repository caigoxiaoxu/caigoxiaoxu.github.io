# Ahiz2's Blog

一个轻量的静态 Markdown 技术博客，主要用于记录 CTF、Pwn、二进制安全、渗透测试和日常折腾笔记。

![Blog preview](assets/nl1.gif)

## 特性

- 纯静态部署，适合直接托管到 GitHub Pages
- Markdown 文章渲染，支持代码高亮和目录大纲
- 左侧分类导航、搜索、阅读进度和暗色模式
- 自动扫描 `_posts` 目录生成 `nav.json`
- 自动生成 `Timeline.md` 时间线页面
- 支持两种文章组织方式：带独立资源目录、直接放在分类目录下

## 项目结构

```text
.
├── index.html              # 页面入口
├── app.js                  # 前端路由、Markdown 渲染、导航交互
├── styles.css              # 站点样式
├── main.py                 # 生成 nav.json 和 Timeline.md
├── nav.json                # 自动生成的导航数据
├── _posts/                 # 页面和文章
│   ├── LEA/                # 首页、时间线等站点页面
│   ├── 2025-writeups/      # 示例分类
│   └── pwn_note1/          # 示例分类
├── assets/                 # 公共资源
├── imgs/                   # 背景、头像等图片
└── prism*.js / marked*.js / purify*.js
```

## 写文章

文章放在 `_posts` 下，一级目录会被识别为分类。

推荐的文章目录结构：

```text
_posts/<category>/<post-slug>/<post-slug>.md
_posts/<category>/<post-slug>/assets/image.png
```

如果文章不需要独立 `assets` 目录，也可以直接放在分类目录里：

```text
_posts/<category>/<post-slug>.md
```

可选 frontmatter：

```markdown
---
title: 文章标题
date: 2026-05-09T00:00:00+08:00
lastmod: 2026-05-09T00:00:00+08:00
---
```

如果没有 `title`，会使用文件名或目录名作为标题；如果文件名以 `YYYY-MM-DD` 开头，会自动推断日期。

## 生成导航

新增、删除或移动文章后，运行：

```bash
python main.py
```

脚本会自动更新：

- `nav.json`
- `_posts/LEA/Timeline.md`

## 本地预览

由于页面会通过 `fetch` 加载 Markdown 和 JSON，建议使用本地 HTTP 服务预览：

```bash
python -m http.server 8000
```

然后打开：

```text
http://127.0.0.1:8000/#/overview
```

## 部署到 GitHub Pages

推荐使用 GitHub Actions 自动部署：

1. 新建 GitHub 仓库，个人主页建议使用 `caigoxiaoxu.github.io`
2. 把当前项目推送到仓库的 `main` 分支
3. 仓库中已经包含 `.github/workflows/deploy-pages.yml`
4. 在 GitHub 打开 `Settings -> Pages`
5. `Source` 选择 `GitHub Actions`
6. 推送后等待 `Actions` 里的 `Deploy GitHub Pages` 工作流完成

以后更新文章时只需要：

```bash
python main.py
git add .
git commit -m "update blog"
git push
```

仓库里包含 `.nojekyll`，GitHub Pages 会按普通静态文件托管，不走 Jekyll 构建。

## 技术栈

- Vanilla JavaScript
- Marked.js
- DOMPurify
- Prism.js
- Python 3

## License

代码按 [MIT License](LICENSE) 开源。博客文章和图片资源如无特别说明，版权归作者所有。

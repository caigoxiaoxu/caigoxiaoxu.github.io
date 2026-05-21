// 思源风格博客 - 拖拽调整侧边栏宽度
class Resizer {
    constructor() {
        this.isResizing = false;
        this.currentResizer = null;
        this.startX = 0;
        this.startLeftWidth = 0;
        this.startRightWidth = 0;
        
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const leftResizer = document.getElementById('resizer-left');
        const rightResizer = document.getElementById('resizer-right');

        if (!leftResizer || !rightResizer) return;
        
        // 左侧分隔条事件
        leftResizer.addEventListener('mousedown', (e) => {
            this.startResizing(e, 'left');
        });
        
        // 右侧分隔条事件
        rightResizer.addEventListener('mousedown', (e) => {
            this.startResizing(e, 'right');
        });

        // 鼠标移动和释放事件
        document.addEventListener('mousemove', (e) => {
            this.handleMouseMove(e);
        });

        document.addEventListener('mouseup', () => {
            this.stopResizing();
        });

        // 触摸事件支持
        leftResizer.addEventListener('touchstart', (e) => {
            this.startResizing(e, 'left');
        });
        
        rightResizer.addEventListener('touchstart', (e) => {
            this.startResizing(e, 'right');
        });

        document.addEventListener('touchmove', (e) => {
            this.handleMouseMove(e);
        });

        document.addEventListener('touchend', () => {
            this.stopResizing();
        });
    }

    startResizing(e, type) {
        this.isResizing = true;
        this.currentResizer = type;
        this.startX = this.getClientX(e);
        
        const leftSidebar = document.getElementById('sidebar-left');
        const rightSidebar = document.getElementById('sidebar-right');
        
        this.startLeftWidth = leftSidebar.offsetWidth;
        this.startRightWidth = rightSidebar.offsetWidth;
        
        // 添加拖拽样式
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        if (type === 'left') {
            document.getElementById('resizer-left').classList.add('dragging');
        } else {
            document.getElementById('resizer-right').classList.add('dragging');
        }
    }

    handleMouseMove(e) {
        if (!this.isResizing) return;
        
        e.preventDefault();
        const currentX = this.getClientX(e);
        const deltaX = currentX - this.startX;
        
        const leftSidebar = document.getElementById('sidebar-left');
        const rightSidebar = document.getElementById('sidebar-right');
        
        if (this.currentResizer === 'left') {
            // 调整左侧边栏宽度
            const newWidth = this.startLeftWidth + deltaX;
            const minWidth = 200;
            const maxWidth = 500;
            
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                leftSidebar.style.width = `${newWidth}px`;
            }
        } else {
            // 调整右侧边栏宽度
            const newWidth = this.startRightWidth - deltaX;
            const minWidth = 200;
            const maxWidth = 400;
            
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                rightSidebar.style.width = `${newWidth}px`;
            }
        }
    }

    stopResizing() {
        if (!this.isResizing) return;
        
        this.isResizing = false;
        this.currentResizer = null;
        
        // 移除拖拽样式
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        document.getElementById('resizer-left')?.classList.remove('dragging');
        document.getElementById('resizer-right')?.classList.remove('dragging');
        
        // 保存布局到localStorage
        this.saveLayout();
    }

    getClientX(e) {
        return e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    }

    saveLayout() {
        const leftSidebar = document.getElementById('sidebar-left');
        const rightSidebar = document.getElementById('sidebar-right');
        
        const layout = {
            leftWidth: leftSidebar.style.width || leftSidebar.offsetWidth,
            rightWidth: rightSidebar.style.width || rightSidebar.offsetWidth
        };
        
        localStorage.setItem('blogLayout', JSON.stringify(layout));
    }

    loadLayout() {
        const savedLayout = localStorage.getItem('blogLayout');
        if (savedLayout) {
            const layout = JSON.parse(savedLayout);
            const leftSidebar = document.getElementById('sidebar-left');
            const rightSidebar = document.getElementById('sidebar-right');
            
            if (layout.leftWidth) {
                leftSidebar.style.width = typeof layout.leftWidth === 'number' 
                    ? `${layout.leftWidth}px` 
                    : layout.leftWidth;
            }
            
            if (layout.rightWidth) {
                rightSidebar.style.width = typeof layout.rightWidth === 'number'
                    ? `${layout.rightWidth}px`
                    : layout.rightWidth;
            }
        }
    }
}

// 暗色模式切换
class ThemeManager {
    constructor() {
        const savedTheme = localStorage.getItem('darkMode');
        this.isDarkMode = savedTheme === null
            ? window.matchMedia('(prefers-color-scheme: dark)').matches
            : savedTheme === 'true';
        this.init();
    }

    init() {
        this.applyTheme();
        this.bindEvents();
        this.updateButtonText();
    }

    applyTheme() {
        if (this.isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        this.updateButtonText();
    }

    bindEvents() {
        // 绑定暗色模式切换按钮事件
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', () => this.toggle());
        }
    }

    toggle() {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', this.isDarkMode.toString());
        this.applyTheme();
    }

    updateButtonText() {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            if (this.isDarkMode) {
                darkModeToggle.textContent = '亮色';
                darkModeToggle.title = '切换到亮色模式';
                darkModeToggle.classList.add('active');
                darkModeToggle.setAttribute('aria-pressed', 'true');
            } else {
                darkModeToggle.textContent = '暗色';
                darkModeToggle.title = '切换到暗色模式';
                darkModeToggle.classList.remove('active');
                darkModeToggle.setAttribute('aria-pressed', 'false');
            }
        }
    }
}

// 导航加载和文件管理
class NavManager {
    constructor() {
        this.navData = { pages: [], notes: {} };
        this.entryMapBySrc = new Map();
        this.pageMap = new Map();
        this.currentHeadings = [];
        this.outlineScrollHandler = null;
        this.init();
    }

    async init() {
        await this.loadNavData();
        this.renderSitePages();
        this.renderFileTree();
        this.bindEvents();
        
        // 延迟处理hash变化，确保DOM完全渲染
        setTimeout(() => {
            this.handleHashChange();
        }, 100);
        
        // 监听hash变化
        window.addEventListener('hashchange', () => {
            this.handleHashChange();
        });
    }

    async loadNavData() {
        try {
            const response = await fetch('nav.json');
            const data = await response.json();
            this.navData = this.normalizeNavData(data);
        } catch (error) {
            console.error('加载导航数据失败:', error);
            this.navData = { pages: [], notes: {} };
        }
        this.buildIndexes();
    }

    normalizeNavData(data) {
        return {
            pages: Array.isArray(data?.pages) ? data.pages : [],
            notes: data?.notes && typeof data.notes === 'object' ? data.notes : {},
        };
    }

    buildIndexes() {
        this.entryMapBySrc = new Map();
        this.pageMap = new Map();

        this.navData.pages = this.navData.pages.map((page) => {
            const normalized = {
                ...page,
                ...this.derivePageMeta(page.note_src),
                type: 'page',
                kicker: 'Site',
            };
            this.pageMap.set(normalized.slug, normalized);
            this.entryMapBySrc.set(normalized.note_src, normalized);
            return normalized;
        });

        for (const [category, notes] of Object.entries(this.navData.notes)) {
            this.navData.notes[category] = notes.map((note) => {
                const slug = note.slug || this.deriveNoteSlug(note.note_src, category);
                const normalized = {
                    ...note,
                    type: 'note',
                    category,
                    kicker: category,
                    slug,
                    title: note.title || slug,
                };
                this.entryMapBySrc.set(normalized.note_src, normalized);
                return normalized;
            });
        }
    }

    derivePageMeta(noteSrc) {
        const normalized = String(noteSrc || '').replace(/\\/g, '/');
        if (normalized.endsWith('/LEA/index.md')) {
            return { slug: 'overview' };
        }
        if (normalized.endsWith('/LEA/Timeline.md')) {
            return { slug: 'timeline' };
        }
        if (normalized.endsWith('/LEA/Friends.md')) {
            return { slug: 'friends' };
        }

        const stem = normalized.split('/').pop()?.replace(/\.md$/i, '') || 'page';
        return { slug: stem.toLowerCase() };
    }

    deriveNoteSlug(noteSrc, category = '') {
        const normalized = String(noteSrc || '').replace(/\\/g, '/');
        const parts = normalized.split('/').filter(Boolean);
        const postsIndex = parts.indexOf('_posts');
        if (postsIndex !== -1) {
            const postParts = parts.slice(postsIndex + 1);
            if (postParts.length === 2) {
                return postParts[1].replace(/\.md$/i, '');
            }
            if (postParts.length >= 3) {
                return postParts[1] === category
                    ? postParts[2]
                    : postParts[postParts.length - 2];
            }
        }
        return normalized.split('/').pop()?.replace(/\.md$/i, '') || 'note';
    }

    renderSitePages() {
        const sitePagesNav = document.getElementById('site-pages-nav');
        if (!sitePagesNav) return;

        sitePagesNav.innerHTML = '';

        if (!this.navData.pages.length) {
            sitePagesNav.innerHTML = '<div class="empty-message">暂无页面</div>';
            return;
        }

        this.navData.pages.forEach((page) => {
            sitePagesNav.appendChild(this.createPageItem(page));
        });
    }

    createPageItem(page) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'site-page-link';
        button.tabIndex = 0;
        button.dataset.slug = page.slug;
        button.dataset.src = page.note_src;

        const label = document.createElement('span');
        label.className = 'site-page-name';
        label.textContent = page.title;

        button.appendChild(label);
        return button;
    }

    renderFileTree() {
        const fileTree = document.querySelector('.file-tree');
        fileTree.innerHTML = '';
        const noteCount = document.getElementById('note-count');

        const notesEntries = Object.entries(this.navData.notes);
        const totalNotes = notesEntries.reduce((sum, [, notes]) => sum + notes.length, 0);
        if (noteCount) noteCount.textContent = String(totalNotes);

        if (notesEntries.length === 0) {
            fileTree.innerHTML = '<div class="empty-message">暂无笔记</div>';
            return;
        }

        notesEntries.forEach(([category, notes]) => {
            fileTree.appendChild(this.createCategoryItem(category, notes));
        });
    }

    createCategoryItem(category, notes) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-item';
        categoryDiv.dataset.category = category;

        const categoryHeader = document.createElement('div');
        categoryHeader.className = 'category-header';
        categoryHeader.tabIndex = 0;

        const categoryIcon = document.createElement('div');
        categoryIcon.className = 'category-icon';

        const categoryName = document.createElement('span');
        categoryName.className = 'category-name';
        categoryName.textContent = this.getCategoryDisplayName(category);

        const categoryCount = document.createElement('span');
        categoryCount.className = 'category-count';
        categoryCount.textContent = notes.length;

        const expandIcon = document.createElement('div');
        expandIcon.className = 'expand-icon';
        expandIcon.setAttribute('aria-hidden', 'true');

        categoryHeader.appendChild(categoryIcon);
        categoryHeader.appendChild(categoryName);
        categoryHeader.appendChild(categoryCount);
        categoryHeader.appendChild(expandIcon);

        const notesContainer = document.createElement('div');
        notesContainer.className = 'notes-container';

        notes.forEach((note) => {
            notesContainer.appendChild(this.createNoteItem(category, note));
        });

        categoryDiv.appendChild(categoryHeader);
        categoryDiv.appendChild(notesContainer);
        return categoryDiv;
    }

    createNoteItem(category, note) {
        const noteItem = document.createElement('div');
        noteItem.className = 'note-item';
        noteItem.tabIndex = 0;
        noteItem.dataset.src = note.note_src;
        noteItem.dataset.root = note.note_root;
        noteItem.dataset.slug = note.slug;
        noteItem.dataset.category = category;
        noteItem.dataset.search = `${this.getCategoryDisplayName(category)} ${note.title} ${note.slug}`.toLowerCase();

        const noteIcon = document.createElement('div');
        noteIcon.className = 'note-icon';

        const noteName = document.createElement('span');
        noteName.className = 'note-name';
        noteName.textContent = note.title;

        noteItem.appendChild(noteIcon);
        noteItem.appendChild(noteName);
        return noteItem;
    }

    getCategoryDisplayName(category) {
        if (category === 'group') {
            return 'mazesec记录';
        }

        if (category.includes('mazesec')) {
            return 'mazesec记录';
        }

        return category;
    }

    bindEvents() {
        const searchInput = document.getElementById('note-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this.filterNotes(searchInput.value);
            });
        }

        // 目录展开/收起事件
        document.addEventListener('click', (e) => {
            if (e.target.closest('.site-page-link')) {
                const pageLink = e.target.closest('.site-page-link');
                const page = this.findPageBySlug(pageLink.dataset.slug);
                if (page) {
                    this.activateEntry(page, true);
                    window.dispatchEvent(new CustomEvent('note-selected'));
                }
                return;
            }

            if (e.target.closest('.category-header')) {
                const categoryHeader = e.target.closest('.category-header');
                this.toggleCategory(categoryHeader.parentElement);
            }

            // 笔记项点击事件
            if (e.target.closest('.note-item')) {
                const noteItem = e.target.closest('.note-item');
                const note = this.findNoteByPath(noteItem.dataset.category, noteItem.dataset.slug);
                if (note) {
                    this.activateEntry(note, true);
                }
                window.dispatchEvent(new CustomEvent('note-selected'));
            }
        });

        document.addEventListener('keydown', (e) => {
            const target = e.target instanceof Element ? e.target : null;
            if (!target) return;

            if (e.key === 'Enter' && target.closest('.category-header')) {
                this.toggleCategory(target.closest('.category-item'));
            }

            if (e.key === 'Enter' && target.closest('.site-page-link')) {
                target.closest('.site-page-link').click();
            }

            if (e.key === 'Enter' && target.closest('.note-item')) {
                target.closest('.note-item').click();
            }
        });
    }

    toggleCategory(categoryItem, forceExpanded = null) {
        if (!categoryItem) return;

        const shouldExpand = forceExpanded === null
            ? !categoryItem.classList.contains('expanded')
            : forceExpanded;

        categoryItem.classList.toggle('expanded', shouldExpand);
    }

    filterNotes(query) {
        const normalizedQuery = query.trim().toLowerCase();
        const categoryItems = document.querySelectorAll('.category-item');
        const fileTree = document.querySelector('.file-tree');
        let visibleNotes = 0;

        categoryItems.forEach(categoryItem => {
            const categoryName = categoryItem.dataset.category.toLowerCase();
            const categoryMatches = normalizedQuery && categoryName.includes(normalizedQuery);
            const noteItems = categoryItem.querySelectorAll('.note-item');
            let categoryHasMatch = false;

            noteItems.forEach(noteItem => {
                const noteMatches = !normalizedQuery
                    || categoryMatches
                    || noteItem.dataset.search.includes(normalizedQuery);

                noteItem.hidden = !noteMatches;
                categoryHasMatch = categoryHasMatch || noteMatches;
                if (noteMatches) visibleNotes += 1;
            });

            categoryItem.hidden = !categoryHasMatch;
            if (normalizedQuery && categoryHasMatch) {
                this.toggleCategory(categoryItem, true);
            }
        });

        let noResults = fileTree.querySelector('.no-results-message');
        if (!noResults) {
            noResults = document.createElement('div');
            noResults.className = 'no-results-message';
            noResults.textContent = '没有匹配的笔记';
            fileTree.appendChild(noResults);
        }

        noResults.hidden = visibleNotes !== 0;
    }

    activateEntry(entry, updateURL = false) {
        this.setActiveEntry(entry);
        this.loadEntry(entry, updateURL);
    }

    setActiveEntry(entry) {
        document.querySelectorAll('.note-item.active, .site-page-link.active').forEach((item) => {
            item.classList.remove('active');
        });

        if (entry.type === 'page') {
            const pageLink = Array.from(document.querySelectorAll('.site-page-link')).find(
                (item) => item.dataset.slug === entry.slug,
            );
            pageLink?.classList.add('active');
            return;
        }

        this.expandCategory(entry.category);
        const noteItem = Array.from(document.querySelectorAll('.note-item')).find(
            (item) => item.dataset.category === entry.category && item.dataset.slug === entry.slug,
        );
        noteItem?.classList.add('active');
    }

    async loadEntry(entry, updateURL = false) {
        try {
            const response = await fetch(entry.note_src);
            if (!response.ok) throw new Error('文件不存在');

            const markdownContent = await response.text();

            this.renderMarkdown(markdownContent, entry);

            // 如果需要更新URL，则更新hash
            if (updateURL) {
                this.updateURLForEntry(entry);
            }
        } catch (error) {
            console.error('加载笔记内容失败:', error);
            this.renderError('无法加载笔记内容');
        }
    }

    renderMarkdown(content, entry) {
        const contentArea = document.querySelector('.markdown-body');
        const noteTitle = document.querySelector('.content-header h1');
        const noteKicker = document.getElementById('content-kicker');

        noteTitle.textContent = entry.title;
        document.title = `${entry.title} | Ahiz2 的博客`;
        document.querySelector('.app-container')?.classList.toggle(
            'home-layout',
            entry.type === 'page' && entry.slug === 'overview',
        );
        if (noteKicker) {
            noteKicker.textContent = entry.kicker || '笔记';
        }

        // 使用marked.js解析Markdown，并处理资源路径
        const htmlContent = this.parseMarkdownWithMarked(content, entry.note_root);
        contentArea.innerHTML = htmlContent;

        this.enhanceRenderedContent(contentArea);
        
        // 手动触发Prism.js代码高亮
        this.highlightCodeBlocks(contentArea);
        
        // 更新大纲导航
        this.updateOutline(contentArea);

        const scrollContainer = document.querySelector('.content-area');
        if (scrollContainer) {
            scrollContainer.scrollTop = 0;
        }
        this.scrollToRequestedSection();
        window.dispatchEvent(new CustomEvent('note-rendered'));
    }

    enhanceRenderedContent(container) {
        this.decorateHeadings(container);
        this.decorateImages(container);
    }

    decorateHeadings(container) {
        const headingCounts = new Map();
        const headings = container.querySelectorAll('h1, h2, h3, h4');

        headings.forEach((heading, index) => {
            const text = heading.textContent.trim();
            if (!heading.id) {
                heading.id = this.buildHeadingId(text, index, headingCounts);
            }

            if (!heading.matches('h2, h3, h4') || heading.querySelector('.heading-anchor')) {
                return;
            }

            const anchorButton = document.createElement('button');
            anchorButton.type = 'button';
            anchorButton.className = 'heading-anchor';
            anchorButton.title = '复制段落链接';
            anchorButton.setAttribute('aria-label', '复制段落链接');
            anchorButton.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.copyHeadingLink(heading, anchorButton);
            });

            heading.appendChild(anchorButton);
        });
    }

    decorateImages(container) {
        const images = container.querySelectorAll('img');

        images.forEach((img) => {
            img.loading = 'lazy';
            img.decoding = 'async';

            const parent = img.parentElement;
            const shouldWrap = parent
                && parent.tagName === 'P'
                && parent.children.length === 1
                && parent.textContent.trim() === '';

            if (!shouldWrap) {
                return;
            }

            const figure = document.createElement('figure');
            figure.className = 'markdown-media';

            const captionText = this.getImageCaption(img);
            parent.parentElement.insertBefore(figure, parent);
            figure.appendChild(img);

            if (captionText) {
                const figcaption = document.createElement('figcaption');
                figcaption.className = 'image-caption';
                figcaption.textContent = captionText;
                figure.appendChild(figcaption);
            }

            parent.remove();
        });
    }

    getImageCaption(image) {
        const alt = (image.getAttribute('alt') || '').trim();
        if (!alt) return '';

        const normalized = alt.toLowerCase();
        if (
            normalized === 'image'
            || normalized === 'img'
            || normalized === 'screenshot'
            || normalized.startsWith('pasted image')
            || /^image[-_\s]?\d*$/i.test(alt)
            || /^[a-f0-9]{20,}$/i.test(alt)
        ) {
            return '';
        }

        return alt;
    }

    buildHeadingId(text, index, counts) {
        const base = this.slugifyHeading(text) || `section-${index + 1}`;
        const currentCount = counts.get(base) || 0;
        counts.set(base, currentCount + 1);
        return currentCount === 0 ? base : `${base}-${currentCount + 1}`;
    }

    slugifyHeading(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^\p{Letter}\p{Number}\u4e00-\u9fff]+/gu, '-')
            .replace(/^-+|-+$/g, '');
    }

    copyHeadingLink(heading, anchorButton) {
        if (!heading.id) return;

        const url = new URL(window.location.href);
        url.searchParams.set('section', heading.id);
        window.history.replaceState(null, '', url.toString());

        const shareUrl = url.toString();
        const finalize = () => this.flashHeadingAnchor(anchorButton);

        if (!navigator.clipboard || !navigator.clipboard.writeText) {
            this.copyCodeFallback(shareUrl);
            finalize();
            return;
        }

        navigator.clipboard.writeText(shareUrl).then(finalize).catch(() => {
            this.copyCodeFallback(shareUrl);
            finalize();
        });
    }

    flashHeadingAnchor(anchorButton) {
        anchorButton.classList.add('copied');
        anchorButton.title = '链接已复制';
        anchorButton.setAttribute('aria-label', '链接已复制');

        clearTimeout(anchorButton._copiedTimer);
        anchorButton._copiedTimer = setTimeout(() => {
            anchorButton.classList.remove('copied');
            anchorButton.title = '复制段落链接';
            anchorButton.setAttribute('aria-label', '复制段落链接');
        }, 1400);
    }

    scrollToRequestedSection() {
        const sectionId = new URLSearchParams(window.location.search).get('section');
        if (!sectionId) return;

        const target = document.getElementById(sectionId);
        if (!target) return;

        requestAnimationFrame(() => {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.updateActiveOutline();
        });
    }

    highlightCodeBlocks(container) {
        // 手动调用Prism.js高亮所有代码块
        if (typeof Prism !== 'undefined') {
            // 查找所有代码块并手动高亮
            const codeBlocks = container.querySelectorAll('code[class*="language-"], pre code');
            codeBlocks.forEach(code => {
                const parent = code.parentElement;
                if (parent && parent.nodeName === 'PRE') {
                    // 确保有正确的类名
                    if (!parent.classList.contains('language-none')) {
                        const langMatch = code.className.match(/language-([a-zA-Z0-9_-]+)/);
                        const lang = langMatch ? langMatch[1] : 'plain';
                        parent.dataset.lang = lang;
                        const grammar = Prism.languages[lang] || Prism.languages.plain || Prism.languages.plaintext;
                        if (grammar) {
                            code.innerHTML = Prism.highlight(code.textContent, grammar, lang);
                        }
                    }
                    
                    // 为代码块添加复制按钮
                    this.addCopyButton(parent);
                }
            });
        }
    }

    addCopyButton(preElement) {
        // 检查是否已经添加了复制按钮
        if (preElement.querySelector('.code-copy-btn')) {
            return;
        }
        
        const copyButton = document.createElement('button');
        copyButton.className = 'code-copy-btn';
        copyButton.textContent = '复制';
        copyButton.title = '复制代码';
        
        copyButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.copyCode(preElement);
        });
        
        preElement.appendChild(copyButton);
    }

    copyCode(preElement) {
        const codeElement = preElement.querySelector('code');
        if (!codeElement) return;
        
        const codeText = codeElement.textContent || codeElement.innerText;
        
        if (!navigator.clipboard || !navigator.clipboard.writeText) {
            this.copyCodeFallback(codeText);
            this.showCopySuccess(preElement);
            return;
        }

        navigator.clipboard.writeText(codeText).then(() => {
            // 显示复制成功提示
            this.showCopySuccess(preElement);
        }).catch(err => {
            this.copyCodeFallback(codeText);
            // 显示复制成功提示
            this.showCopySuccess(preElement);
        });
    }

    copyCodeFallback(codeText) {
        const textArea = document.createElement('textarea');
        textArea.value = codeText;
        textArea.setAttribute('readonly', '');
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }

    showCopySuccess(preElement) {
        // 移除可能存在的旧提示
        const existingSuccess = preElement.querySelector('.copy-success');
        if (existingSuccess) {
            existingSuccess.remove();
        }
        
        // 创建成功提示
        const successElement = document.createElement('div');
        successElement.className = 'copy-success';
        successElement.textContent = '已复制!';
        
        preElement.appendChild(successElement);
        
        // 2秒后自动移除提示
        setTimeout(() => {
            if (successElement.parentElement === preElement) {
                successElement.remove();
            }
        }, 2000);
    }

    parseMarkdownWithMarked(markdown, noteRoot) {
        try {
            const markdownBody = this.stripFrontmatter(markdown);

            // 配置marked选项
            marked.setOptions({
                highlight: function(code, lang) {
                    // 使用Prism.js进行代码高亮
                    const grammar = Prism.languages[lang] || Prism.languages.plain || Prism.languages.plaintext;
                    return grammar ? Prism.highlight(code, grammar, lang || 'plain') : code;
                },
                breaks: true, // 将\n转换为<br>
                gfm: true,    // 启用GitHub Flavored Markdown
            });
            
            // 使用marked解析Markdown
            const parsedHtml = marked.parse(markdownBody);
            
            // 处理资源文件路径
            const processedHtml = this.processResourcePaths(parsedHtml, noteRoot);
            
            // 使用DOMPurify进行安全过滤
            const cleanHtml = DOMPurify.sanitize(processedHtml);
            
            return cleanHtml;
        } catch (error) {
            console.error('Markdown解析错误:', error);
            return '<div class="error-message">Markdown解析错误</div>';
        }
    }

    stripFrontmatter(markdown) {
        const normalized = markdown.replace(/^[\uFEFF\r\n]+/, '');
        if (!normalized.startsWith('---')) {
            return normalized;
        }

        const match = normalized.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/);
        return match ? normalized.slice(match[0].length) : normalized;
    }

    processResourcePaths(html, noteRoot) {
        // 创建一个临时DOM元素来处理HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // 处理图片路径
        const images = tempDiv.querySelectorAll('img');
        images.forEach(img => {
            const src = img.getAttribute('src');
            if (src && !src.startsWith('http') && !src.startsWith('/') && !src.startsWith('data:')) {
                // 相对路径，转换为基于noteRoot的绝对路径
                const fullPath = this.resolvePath(src, noteRoot);
                img.setAttribute('src', fullPath);
            }
        });
        
        // 处理链接路径（如果有相对链接指向资源文件）
        const links = tempDiv.querySelectorAll('a');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && !href.startsWith('http') && !href.startsWith('/') && !href.startsWith('#') && 
                (href.endsWith('.png') || href.endsWith('.jpg') || href.endsWith('.jpeg') || href.endsWith('.gif') || href.endsWith('.svg'))) {
                // 相对路径的资源文件链接，转换为基于noteRoot的绝对路径
                const fullPath = this.resolvePath(href, noteRoot);
                link.setAttribute('href', fullPath);
            }
        });
        
        return tempDiv.innerHTML;
    }

    resolvePath(relativePath, noteRoot) {
        // 简单的路径解析：将相对路径与noteRoot组合
        if (relativePath.startsWith('./')) {
            relativePath = relativePath.substring(2);
        }
        
        // 确保noteRoot以斜杠结尾
        const baseRoot = noteRoot.endsWith('/') ? noteRoot : noteRoot + '/';
        
        return baseRoot + relativePath;
    }

    updateOutline(contentElement) {
        const outlineContainer = document.querySelector('.outline-container');
        const headings = contentElement.querySelectorAll('h1, h2, h3');
        this.currentHeadings = Array.from(headings);
        
        if (headings.length === 0) {
            outlineContainer.innerHTML = '<div class="empty-outline">暂无大纲</div>';
            return;
        }

        let outlineHtml = '';
        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.substring(1));
            const text = heading.textContent;
            if (!heading.id) {
                heading.id = `heading-${index}-${this.slugifyHeading(text) || 'section'}`;
            }
            outlineHtml += `
                <div class="outline-item level-${level}" data-index="${index}">
                    ${this.escapeHtml(text)}
                </div>
            `;
        });

        outlineContainer.innerHTML = outlineHtml;
        
        // 绑定大纲点击事件
        this.bindOutlineEvents(headings);
        this.bindOutlineScrollSpy();
        requestAnimationFrame(() => this.updateActiveOutline());
    }

    bindOutlineEvents(headings) {
        const outlineItems = document.querySelectorAll('.outline-item');
        outlineItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                if (headings[index]) {
                    headings[index].scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    bindOutlineScrollSpy() {
        const contentArea = document.querySelector('.content-area');
        if (!contentArea || this.outlineScrollHandler) return;

        this.outlineScrollHandler = () => this.updateActiveOutline();
        contentArea.addEventListener('scroll', this.outlineScrollHandler, { passive: true });
    }

    updateActiveOutline() {
        const contentArea = document.querySelector('.content-area');
        const outlineItems = document.querySelectorAll('.outline-item');
        if (!contentArea || !this.currentHeadings.length || outlineItems.length === 0) return;

        const containerTop = contentArea.getBoundingClientRect().top;
        let activeIndex = 0;

        this.currentHeadings.forEach((heading, index) => {
            const headingTop = heading.getBoundingClientRect().top - containerTop;
            if (headingTop <= 90) {
                activeIndex = index;
            }
        });

        outlineItems.forEach((item, index) => {
            item.classList.toggle('active', index === activeIndex);
        });
    }

    escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    loadDefaultHome() {
        const overviewPage = this.findPageBySlug('overview');
        if (overviewPage) {
            this.activateEntry(overviewPage, false);
        }
    }

    // URL路由处理方法
    handleHashChange() {
        const hash = window.location.hash;

        if (hash && hash.startsWith('#/')) {
            const path = decodeURIComponent(hash.substring(2)).replace(/^\/+|\/+$/g, '');
            const normalizedPath = this.resolveLegacyPath(path);

            if (normalizedPath !== path) {
                this.replaceHash(normalizedPath);
                return;
            }

            this.loadEntryFromPath(normalizedPath);
        } else {
            // 没有hash或hash为空，重定向到默认主页
            this.redirectToDefaultHome();
        }
    }

    
    resolveLegacyPath(path) {
        const legacyMap = {
            'LEA/index': 'overview',
            'LEA/Timeline': 'timeline',
            'LEA/Friends': 'friends',
        };
        return legacyMap[path] || path;
    }

    replaceHash(path) {
        const url = new URL(window.location.href);
        url.hash = `#/${path}`;
        window.history.replaceState(null, '', url.toString());
        this.loadEntryFromPath(path);
    }

    loadEntryFromPath(path) {
        if (!path) {
            this.loadDefaultHome();
            return;
        }

        const page = this.findPageBySlug(path);
        if (page) {
            this.activateEntry(page, false);
            return;
        }

        const parts = path.split('/');
        if (parts.length >= 2) {
            const category = parts[0];
            const slug = parts[1];
            const note = this.findNoteByPath(category, slug);
            if (note) {
                this.activateEntry(note, false);
                return;
            }
        }

        console.warn('未找到路径:', path);
        this.loadDefaultHome();
    }

    findPageBySlug(slug) {
        return this.pageMap.get(slug) || null;
    }
    
    findNoteByPath(category, slug) {
        if (!this.navData.notes || !this.navData.notes[category]) {
            return null;
        }
        
        // 在指定目录中查找笔记
        for (const note of this.navData.notes[category]) {
            if (note.slug === slug) {
                return note;
            }
        }
        return null;
    }
    
    expandCategory(category) {
        // 展开指定目录
        const categoryItems = document.querySelectorAll('.category-item');
        categoryItems.forEach(item => {
            const categoryName = item.querySelector('.category-name').textContent;
            if (categoryName === category) {
                this.toggleCategory(item, true);
            }
        });
    }
    
    updateURLForEntry(entry) {
        const url = new URL(window.location.href);
        url.searchParams.delete('section');
        url.hash = entry.type === 'page'
            ? `#/${entry.slug}`
            : `#/${entry.category}/${entry.slug}`;

        if (window.location.href !== url.toString()) {
            window.history.replaceState(null, '', url.toString());
        }
    }
    
    redirectToDefaultHome() {
        // 重定向到默认主页
        const defaultPath = 'overview';
        const newHash = `#/${defaultPath}`;
        
        if (window.location.hash !== newHash) {
            window.location.hash = newHash;
        } else {
            // 如果已经是默认路径，则加载默认主页
            this.loadDefaultHome();
        }
    }

    renderError(message) {
        const contentArea = document.querySelector('.markdown-body');
        contentArea.innerHTML = `<div class="error-message">${message}</div>`;
        window.dispatchEvent(new CustomEvent('note-rendered'));
    }
}

class MobileNavigation {
    constructor() {
        this.sidebar = document.getElementById('sidebar-left');
        this.backdrop = document.getElementById('sidebar-backdrop');
        this.toggleButton = document.getElementById('mobile-menu-toggle');
        this.init();
    }

    init() {
        if (!this.sidebar || !this.backdrop || !this.toggleButton) return;

        this.toggleButton.addEventListener('click', () => this.toggle());
        this.backdrop.addEventListener('click', () => this.close());
        window.addEventListener('note-selected', () => this.close());

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.close();
            }
        });
    }

    toggle() {
        const shouldOpen = !this.sidebar.classList.contains('active');
        if (shouldOpen) {
            this.open();
        } else {
            this.close();
        }
    }

    open() {
        this.sidebar.classList.add('active');
        this.backdrop.classList.add('active');
        this.toggleButton.setAttribute('aria-expanded', 'true');
    }

    close() {
        this.sidebar.classList.remove('active');
        this.backdrop.classList.remove('active');
        this.toggleButton.setAttribute('aria-expanded', 'false');
    }
}

class ReadingProgress {
    constructor() {
        this.contentArea = document.querySelector('.content-area');
        this.progressBar = document.getElementById('reading-progress-bar');
        this.percentLabel = document.getElementById('reading-percent');
        this.scrollTopButton = document.getElementById('scroll-top');
        this.init();
    }

    init() {
        if (!this.contentArea || !this.progressBar) return;

        this.contentArea.addEventListener('scroll', () => this.update(), { passive: true });
        window.addEventListener('resize', () => this.update());
        window.addEventListener('note-rendered', () => requestAnimationFrame(() => this.update()));
        if (this.scrollTopButton) {
            this.scrollTopButton.addEventListener('click', () => {
                this.contentArea.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
        this.update();
    }

    update() {
        const maxScroll = this.contentArea.scrollHeight - this.contentArea.clientHeight;
        const progress = maxScroll <= 0 ? 0 : (this.contentArea.scrollTop / maxScroll) * 100;
        const boundedProgress = Math.min(100, Math.max(0, progress));
        this.progressBar.style.width = `${boundedProgress}%`;
        if (this.percentLabel) {
            this.percentLabel.textContent = `${Math.round(boundedProgress)}%`;
        }
    }
}

class StartupIntro {
    constructor() {
        this.intro = document.getElementById('startup-intro');
        this.app = document.querySelector('.app-container');
        this.isClosed = false;
        this.startedAt = performance.now();
        this.minDuration = 1700;
        this.init();
    }

    init() {
        if (!this.intro) return;

        window.addEventListener('note-rendered', () => this.close(), { once: true });
        window.addEventListener('load', () => {
            window.setTimeout(() => this.close(), 2300);
        }, { once: true });

        window.setTimeout(() => this.close(), 4600);
    }

    close() {
        if (this.isClosed || !this.intro) return;

        const elapsed = performance.now() - this.startedAt;
        if (elapsed < this.minDuration) {
            window.setTimeout(() => this.close(), this.minDuration - elapsed);
            return;
        }

        this.isClosed = true;
        this.intro.classList.add('is-hidden');
        this.app?.classList.add('is-entering');
        window.setTimeout(() => {
            this.intro?.remove();
            this.app?.classList.remove('is-entering');
        }, 950);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const resizer = new Resizer();
    new StartupIntro();
    new ThemeManager();
    new MobileNavigation();
    new ReadingProgress();
    new NavManager();
    
    // 加载保存的布局
    setTimeout(() => {
        resizer.loadLayout();
    }, 100);
});

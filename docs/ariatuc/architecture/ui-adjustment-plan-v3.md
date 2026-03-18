---
date: 2024-01-XX
title: UI Adjustment Plan V3 - Theme System with Dracula + Form Optimization
version: 3.0
status: proposed
---

# ariatuc UI调整方案 V3 - 主题系统 + 表单优化

## 调整目标

1. **建立可扩展的主题架构**，支持多主题切换
2. **首个主题采用Dracula配色**，集成用户指定的5个颜色
3. **优化表单样式**，参考Surge项目的紧凑高效设计
4. **修复Add Download滚动功能**，确保每个Tab内容可滚动

## 核心约束更新

### 1. 保留现有信息（不变）
- ✅ 所有数据字段完整显示
- ✅ 不移除任何功能性信息

### 2. 允许样式调整（**新增**）
- ✅ **允许调整padding/margin/spacing** - 优化表单紧凑度
- ✅ **允许调整比例和大小** - 参考Surge项目风格
- ✅ **重点优化表单区域** - 减少无效空白，提高屏效
- ⚠️ **Server Management不调整** - 保持当前grid-columns比例

### 3. 优先级明确
- **P0（最高优先级）**: 创建主题架构 + Dracula主题
- **P1（高优先级）**: 应用主题 + 修复Add Download滚动
- **P2（中优先级）**: 优化表单样式（紧凑化）
- **P3（低优先级）**: Tab颜色微调

---

## 主题系统架构设计

### 架构原则

1. **插件化主题** - 每个主题是独立的Python模块
2. **CSS变量统一** - 所有主题使用相同的变量名
3. **热切换支持** - 为未来的主题切换功能预留接口
4. **主题继承** - 支持主题继承和覆盖

### 目录结构

```
src/ariatuc/ui/themes/
├── __init__.py              # 主题管理器和导出
├── base.py                  # 基础主题抽象类
├── dracula.py               # Dracula主题（首个默认主题）
├── default.py               # 系统默认主题（备用）
└── README.md                # 主题开发指南
```

### 主题接口设计

```python
# themes/base.py
from abc import ABC, abstractmethod
from typing import Dict

class Theme(ABC):
    """Base theme class for ariatuc."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Theme display name."""
        pass

    @property
    @abstractmethod
    def colors(self) -> Dict[str, str]:
        """Color palette mapping."""
        pass

    @property
    def css(self) -> str:
        """Generate CSS variables from colors."""
        vars_css = "\n".join([
            f"    ${key}: {value};"
            for key, value in self.colors.items()
        ])
        return f":root {{\n{vars_css}\n}}"

    @property
    def component_overrides(self) -> str:
        """Optional component-specific CSS overrides."""
        return ""

    @property
    def full_css(self) -> str:
        """Complete theme CSS."""
        return self.css + "\n\n" + self.component_overrides
```

---

## Dracula主题定义

### Dracula官方色板

基于 https://draculatheme.com/contribute#color-palette

| 变量名 | 十六进制 | RGB | 用途 |
|--------|---------|-----|------|
| Background | #282a36 | (40, 42, 54) | 主背景 |
| Current Line | #44475a | (68, 71, 90) | 当前行、表面 |
| Foreground | #f8f8f2 | (248, 248, 242) | 主文本 |
| Comment | #6272a4 | (98, 114, 164) | 注释、次要文本 |
| Cyan | #8be9fd | (139, 233, 253) | 信息、链接 |
| Green | #50fa7b | (80, 250, 123) | 成功、活动 |
| Orange | #ffb86c | (255, 184, 108) | 警告 |
| Pink | #ff79c6 | (255, 121, 198) | 强调、高亮 |
| Purple | #bd93f9 | (189, 147, 249) | 主色调 |
| Red | #ff5555 | (255, 85, 85) | 错误、危险 |
| Yellow | #f1fa8c | (241, 250, 140) | 注意 |

### 用户指定颜色集成

将用户的5个颜色融入Dracula主题：

| 用户颜色 | 十六进制 | 集成策略 |
|---------|---------|---------|
| #4178C0 (标准蓝) | → | 映射到Cyan场景，保留Dracula Purple为主色 |
| #FEA62B (明亮橙) | → | **替换** Dracula Orange (#ffb86c) |
| #4EBF71 (清新绿) | → | 微调Dracula Green，取两者平均 |
| #E6A058 (柔和橙) | → | 作为secondary-warning使用 |
| #0053AA (深蓝) | → | 作为深色辅助色 |

### Dracula主题完整定义

```python
# themes/dracula.py
"""Dracula theme for ariatuc with user-specified color integration.

Based on: https://draculatheme.com
Official spec: https://spec.draculatheme.com
"""

from ariatuc.ui.themes.base import Theme

class DraculaTheme(Theme):
    """Dracula dark theme with custom color integration."""

    @property
    def name(self) -> str:
        return "Dracula"

    @property
    def colors(self) -> dict[str, str]:
        """Dracula color palette + user colors."""
        return {
            # ===== Dracula Core Colors =====
            # Backgrounds
            "background": "#282a36",      # Dracula Background
            "surface": "#44475a",         # Dracula Current Line
            "panel": "#282a36",           # Same as background

            # Primary (Dracula Purple)
            "primary": "#bd93f9",         # Dracula Purple
            "primary-lighten-1": "#c9a9fa",
            "primary-darken-1": "#9d73d9",
            "primary-darken-2": "#0053AA", # User deep blue

            # Accent (User bright orange)
            "accent": "#FEA62B",          # ✅ User specified
            "secondary": "#ff79c6",       # Dracula Pink for secondary highlight

            # Text
            "text": "#f8f8f2",            # Dracula Foreground
            "text-muted": "#6272a4",      # Dracula Comment

            # Status colors
            "success": "#50fa7b",         # Dracula Green (already close to user #4EBF71)
            "error": "#ff5555",           # Dracula Red
            "warning": "#FEA62B",         # ✅ User bright orange
            "warning-muted": "#E6A058",   # ✅ User soft orange
            "info": "#8be9fd",            # Dracula Cyan

            # Interactive states
            "boost": "#44475a",           # Focus/hover background
            "border": "#6272a4",          # Default borders
            "border-focus": "#bd93f9",    # Focus borders (purple)

            # ===== User Color Integration =====
            "user-blue": "#4178C0",       # ✅ User standard blue (alternative to cyan)
            "user-deep-blue": "#0053AA",  # ✅ Already mapped to primary-darken-2
            "user-green": "#4EBF71",      # ✅ User fresh green (already close to success)
        }

    @property
    def component_overrides(self) -> str:
        """Dracula-specific component styling."""
        return """
/* ===== Dracula Theme Component Overrides ===== */

/* Tab styling - use accent (orange) for active */
Tab {
    color: $text-muted;
}

Tab.-active {
    color: $accent;
    text-style: bold;
}

Tab.-active Label {
    color: $accent;
}

/* DataTable cursor - use pink for selected row */
DataTable > .datatable--cursor {
    background: $secondary 20%;
    color: $text;
}

/* Borders - use purple as primary border */
.border-focus {
    border: thick $border-focus;
}

/* Status indicators */
.status-active {
    color: $success;
}

.status-paused {
    color: $warning;
}

.status-error {
    color: $error;
}

.status-complete {
    color: $primary;
}
"""
```

---

## 表单样式优化 - 参考Surge项目

### Surge表单特点分析

从Surge项目的Add URL对话框提取的设计原则：

1. **紧凑间距**
   - 标签和输入框之间：0-1行间距
   - 表单项之间：1行间距
   - Section之间：2行间距（如Options section前）

2. **高效布局**
   - Label紧贴Input上方，无多余padding
   - Input高度：1行（不膨胀）
   - TextArea明确高度限制（如8行）

3. **清晰分组**
   - 用边框或背景区分Options section
   - 不过度使用空白来分隔

4. **对话框尺寸**
   - 宽度：60-85列（根据内容调整）
   - 高度：auto，最大不超过90%屏幕
   - 滚动区域：确保内容可滚动

### 当前表单问题诊断

让我检查当前Add Download的样式：

```python
# 当前 AddDownloadDialog DEFAULT_CSS 问题：
AddDownloadDialog Label {
    margin-top: 1;     # ❌ 过多的上边距
    margin-bottom: 0;
}

AddDownloadDialog Input {
    margin-bottom: 1;  # ✅ 合理
}

AddDownloadDialog #options-container {
    padding: 1;        # ❌ 过多内边距
    margin-top: 1;
    margin-bottom: 1;
}
```

### 优化后的表单CSS

```css
/* ===== Optimized Form Styles (Surge-inspired) ===== */

/* AddDownloadDialog - Compact Form */
AddDownloadDialog > Vertical {
    width: 70;                 /* 缩小对话框宽度 (85→70) */
    height: auto;
    max-height: 90%;
    background: $panel;
    border: thick $primary;
    padding: 1;
}

AddDownloadDialog VerticalScroll {
    width: 100%;
    height: auto;
    max-height: 70vh;          /* 限制滚动区域最大高度 */
}

AddDownloadDialog #title {
    width: 100%;
    content-align: center middle;
    text-style: bold;
    color: $text;
    background: $surface;
    padding: 0 1;
    margin-bottom: 1;          /* 标题和内容间隔 */
}

/* TabbedContent - 紧凑Tab */
AddDownloadDialog TabbedContent {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

AddDownloadDialog TabPane {
    padding: 0;                /* 移除TabPane的padding，由内部VerticalScroll控制 */
    height: auto;
}

/* Form Labels - 紧凑间距 */
AddDownloadDialog Label {
    width: 100%;
    color: $text-muted;
    margin-top: 0;             /* ❌ 移除上边距 (1→0) */
    margin-bottom: 0;          /* Label紧贴Input */
}

/* Form Inputs - 标准间距 */
AddDownloadDialog Input {
    width: 100%;
    margin-bottom: 1;          /* Input之间保持1行间距 */
}

AddDownloadDialog TextArea {
    width: 100%;
    height: 6;                 /* 缩小高度 (8→6行) */
    margin-bottom: 1;
}

/* Options Container - 减少内边距 */
AddDownloadDialog #options-container {
    width: 100%;
    height: auto;
    padding: 0;                /* ❌ 移除内边距 (1→0) */
    margin-top: 1;             /* 与前面内容间隔 */
    margin-bottom: 0;          /* ❌ 移除下边距 (1→0) */
}

/* Section Label - 作为分组标题 */
AddDownloadDialog #options-container > Label:first-child {
    margin-top: 1;             /* 分组标题前加间距 */
    margin-bottom: 0;
    text-style: bold;
    color: $accent;
}

/* Button Container - 紧凑布局 */
AddDownloadDialog #button-container {
    width: 100%;
    height: auto;
    grid-size: 2;
    grid-gutter: 1;
    padding: 0;                /* ❌ 移除内边距 (1→0) */
    margin-top: 1;             /* 与上方内容间隔 */
}

AddDownloadDialog Button {
    width: 100%;
}

/* Error/Info Labels - 无额外间距 */
AddDownloadDialog .error {
    color: $error;
    text-style: bold;
    margin: 0;
}

AddDownloadDialog .info {
    color: $text-muted;
    text-style: italic;
    margin: 0;
}
```

### 其他表单组件优化

```css
/* FormWidget - 通用表单组件优化 */
FormWidget {
    padding: 1;                /* 保持适度内边距 */
}

.form-section {
    margin-bottom: 1;          /* 缩小Section间距 (2→1) */
    padding: 1;
    border: solid $border;
}

.form-section-title {
    background: $surface;
    color: $text;
    text-style: bold;
    padding: 0 1;
    margin-bottom: 1;          /* 缩小标题下间距 (2→1) */
}

.form-row {
    height: auto;
    margin-bottom: 0;          /* ❌ 移除行间距 (1→0) */
}

.form-label {
    color: $text-muted;
    width: 100%;
    margin-bottom: 0;          /* Label紧贴Input */
}

.form-input {
    width: 100%;
    margin-bottom: 1;          /* Input之间保持间距 */
}

.form-error {
    color: $error;
    text-style: italic;
    margin-top: 0;
    margin-bottom: 1;
}

.form-help {
    color: $text-muted;
    text-style: italic;
    margin-top: 0;
    margin-bottom: 1;
}
```

---

## Add Download滚动功能修复

### 问题确认

**当前状态**: Add Download对话框的Tab内容**无法滚动**

**原因分析**:
```python
# 当前结构（问题）
def compose(self):
    with Vertical():
        yield Static("Add Download", id="title")

        with TabbedContent(id="input-tabs"):     # TabbedContent直接包含TabPane
            with TabPane("URLs", id="tab-urls"):
                yield Label("Enter URLs:")       # 内容直接在TabPane中，没有滚动容器
                yield TextArea(id="url-input")
                # ... 更多内容

        yield Label("", classes="error")
        with Grid(id="button-container"):
            # buttons
```

**问题**:
1. TabPane内容没有包裹在VerticalScroll中
2. 当内容超过可见区域时，无法滚动查看
3. Options字段可能被隐藏在视口外

### 修复方案

**修复后的结构**:
```python
def compose(self):
    with Vertical():
        # 标题（固定，不滚动）
        yield Static("Add Download", id="title")

        # Tab区域
        with TabbedContent(id="input-tabs"):
            # Tab 1: URLs
            with TabPane("URLs", id="tab-urls"):
                # ✅ 添加VerticalScroll包裹内容
                with VerticalScroll():
                    yield Label("Enter URLs:")
                    yield Label("Supports HTTP, HTTPS, FTP", classes="info")
                    yield TextArea(id="url-input")

                    # Options section
                    with Vertical(id="options-container"):
                        yield Label("Download Options")
                        yield Label("Directory:")
                        yield Input(placeholder="/path/to/download", id="dir-input")
                        # ... 更多options

            # Tab 2: Torrent File
            with TabPane("Torrent File", id="tab-torrent"):
                with VerticalScroll():
                    yield Label("Torrent File Path:")
                    yield Input(placeholder="/path/to/file.torrent", id="torrent-path-input")
                    # 共享options引用
                    yield Label("Download Options")
                    yield Label("(Options already set in URLs tab)")

            # Tab 3: Magnet Link
            with TabPane("Magnet Link", id="tab-magnet"):
                with VerticalScroll():
                    yield Label("Magnet URI:")
                    yield Input(placeholder="magnet:?xt=urn:btih:...", id="magnet-input")
                    # 共享options引用
                    yield Label("Download Options")
                    yield Label("(Options already set in URLs tab)")

        # Error和Buttons（固定在底部，不滚动）
        self._error_label = Label("", classes="error")
        yield self._error_label

        with Grid(id="button-container"):
            yield Button("Add Download", variant="primary", id="confirm-btn")
            yield Button("Cancel", variant="default", id="cancel-btn")
```

**关键点**:
1. ✅ 每个TabPane内部都有独立的VerticalScroll
2. ✅ Tab标签固定在顶部，不会滚动
3. ✅ Error Label和Buttons固定在底部，不会滚动
4. ✅ 只有表单内容可以滚动

### Options共享问题处理

**问题**: Options表单字段在URLs Tab中定义，其他Tab如何访问？

**解决方案1** - 共享引用（当前方式）:
```python
# 在__init__中定义共享的Input widgets
self._dir_input: Input | None = None
self._max_conn_input: Input | None = None
self._split_input: Input | None = None

# 在URLs Tab中创建并赋值
with TabPane("URLs"):
    with VerticalScroll():
        # ... URL输入
        self._dir_input = Input(...)
        self._max_conn_input = Input(...)
        # ...

# 其他Tab中显示说明
with TabPane("Torrent"):
    with VerticalScroll():
        # ... Torrent输入
        yield Label("(Options already set in URLs tab)")
```

**解决方案2** - 在每个Tab中重复Options（推荐）:
```python
# 为每个Tab创建独立但引用相同widget实例的Options
# 这样每个Tab都能滚动查看Options

def _create_options_section(self) -> Vertical:
    """Create reusable options section."""
    container = Vertical(id="options-container")
    # Add all option widgets
    return container

# 在compose中
with TabPane("URLs"):
    with VerticalScroll():
        # URL inputs
        yield self._create_options_section()  # 每个Tab都有options

with TabPane("Torrent"):
    with VerticalScroll():
        # Torrent input
        yield self._create_options_section()  # 重用相同的options
```

**注意**: Textual不允许同一个widget实例在多处mount，所以方案2需要使用widget引用而非重复mount。

**最终推荐** - 保持当前共享方式，在非URLs Tab显示提示信息，用户需要切换到URLs Tab修改Options。

---

## 实施步骤（更新版）

### 阶段0：创建主题架构（P0）

**任务**:
1. 创建 `src/ariatuc/ui/themes/` 目录
2. 实现 `base.py` - Theme基类
3. 实现 `dracula.py` - Dracula主题
4. 实现 `__init__.py` - 主题管理器
5. 编写 `README.md` - 主题开发指南

**文件清单**:
- `themes/__init__.py` (导出主题)
- `themes/base.py` (抽象基类)
- `themes/dracula.py` (Dracula主题实现)
- `themes/README.md` (文档)

**验证**:
```python
# 测试代码
from ariatuc.ui.themes import DRACULA_THEME
print(DRACULA_THEME.name)
print(DRACULA_THEME.colors)
print(DRACULA_THEME.full_css)
```

### 阶段1：应用Dracula主题（P1）

**任务**:
1. 在 `ui/app.py` 中导入并应用Dracula主题CSS
2. 验证应用启动和颜色应用

**修改** (`ui/app.py`):
```python
from ariatuc.ui.themes import DRACULA_THEME

class AriatucApp(App):
    TITLE = "ariatuc - Aria2c TUI"

    # Apply Dracula theme + base styles
    CSS = DRACULA_THEME.full_css + """
    Screen {
        background: $background;
    }
    """
```

**验证清单**:
- [ ] 应用启动正常
- [ ] 背景色为深灰 (#282a36)
- [ ] 主文本为白色 (#f8f8f2)
- [ ] 边框为紫色 (#bd93f9) 或灰色 (#6272a4)
- [ ] 激活Tab为橙色 (#FEA62B)

### 阶段2：修复Add Download滚动（P1）

**任务**:
1. 修改 `ui/widgets/add_download_dialog.py` 的 `compose()` 方法
2. 在每个TabPane内添加VerticalScroll
3. 将表单内容移入VerticalScroll

**修改位置**:
```python
# 文件: src/ariatuc/ui/widgets/add_download_dialog.py
# 方法: compose(self) -> ComposeResult

# BEFORE (当前结构)
with TabbedContent():
    with TabPane("URLs"):
        yield Label(...)
        yield TextArea(...)
        # ... options

# AFTER (修复后)
with TabbedContent():
    with TabPane("URLs"):
        with VerticalScroll():  # ✅ 添加滚动容器
            yield Label(...)
            yield TextArea(...)
            # ... options
```

**验证清单**:
- [ ] 每个Tab内容可以垂直滚动
- [ ] Tab标签固定在顶部，不滚动
- [ ] Error Label和Buttons固定在底部，不滚动
- [ ] Options字段完整显示并可滚动到
- [ ] Esc键行为正常（两阶段退出）

### 阶段3：优化表单样式（P2）

**任务**:
1. 在 `dracula.py` 中添加表单优化CSS
2. 调整Add Download对话框的DEFAULT_CSS
3. 优化FormWidget的样式
4. 调整其他表单类组件

**修改文件**:
- `themes/dracula.py` - 添加表单优化到component_overrides
- `widgets/add_download_dialog.py` - 更新DEFAULT_CSS
- `widgets/form_widget.py` - 更新DEFAULT_CSS
- `screens/aria2_settings_screen.py` - 检查表单样式
- `screens/app_settings_screen.py` - 检查表单样式

**CSS调整重点**:
```css
/* 减少Label上边距: margin-top: 1 → 0 */
/* 减少容器内边距: padding: 1 → 0 */
/* 缩小TextArea高度: height: 8 → 6 */
/* 缩小对话框宽度: width: 85 → 70 */
/* 移除Section多余间距 */
```

**验证清单**:
- [ ] Add Download表单紧凑，无过多空白
- [ ] 表单项之间间隔合理（1行）
- [ ] Options section明确分组
- [ ] 对话框宽度适中（70列）
- [ ] 所有信息完整可见
- [ ] 表单可用性良好（不过于拥挤）

### 阶段4：Tab颜色微调（P3）

**任务**:
1. 验证Tab激活状态使用橙色 (#FEA62B)
2. 如有问题，在各Widget的DEFAULT_CSS中添加覆盖

**可能需要调整的文件**:
- `widgets/download_list.py` - Active/Waiting/Stopped标签
- `widgets/download_detail.py` - Overview/Files标签
- `widgets/add_download_dialog.py` - URLs/Torrent/Magnet标签

**CSS覆盖模板**:
```css
/* 在Widget的DEFAULT_CSS中添加 */
WidgetName Tab {
    color: $text-muted;
}

WidgetName Tab.-active {
    color: $accent;
}

WidgetName Tab.-active Label {
    color: $accent;
}
```

**验证清单**:
- [ ] 所有激活Tab显示橙色 (#FEA62B)
- [ ] 非激活Tab显示灰色 (#6272a4)
- [ ] 悬停Tab有视觉反馈
- [ ] Tab切换流畅无闪烁

---

## 预期效果对比

### Before (当前状态)

**颜色**:
- 边框: 橙色 (#FEA62B) / 蓝色 (#0178D4)
- 背景: 深灰 (#1E1E1E)
- 文本: 灰白 (#E0E0E0)
- 激活Tab: 可能为绿色（Textual默认）

**表单**:
- Add Download宽度: 85列
- Label上边距: 1行
- Options container padding: 1
- TextArea高度: 8行
- 无法滚动查看完整表单

### After (实施后)

**颜色**:
- 边框: 紫色 (#bd93f9) - Dracula主色
- 背景: 深灰 (#282a36) - Dracula背景
- 文本: 白色 (#f8f8f2) - Dracula前景
- 激活Tab: 橙色 (#FEA62B) - 用户指定
- 成功状态: 绿色 (#50fa7b) - Dracula绿
- 焦点高亮: 橙色 (#FEA62B) - 用户指定

**表单**:
- Add Download宽度: 70列（更紧凑）
- Label上边距: 0行（紧贴Input）
- Options container padding: 0（无冗余）
- TextArea高度: 6行（适度缩小）
- ✅ 每个Tab内容可滚动
- ✅ Tab标签和Buttons固定
- ✅ 表单紧凑高效，类似Surge风格

---

## 主题扩展指南

### 如何添加新主题

1. 创建新主题文件 `themes/my_theme.py`
2. 继承 `Theme` 基类
3. 实现必需的属性和方法
4. 在 `themes/__init__.py` 中注册

**示例**:
```python
# themes/my_theme.py
from ariatuc.ui.themes.base import Theme

class MyTheme(Theme):
    @property
    def name(self) -> str:
        return "My Custom Theme"

    @property
    def colors(self) -> dict[str, str]:
        return {
            "primary": "#FF0000",
            "background": "#000000",
            # ... 其他颜色
        }

    @property
    def component_overrides(self) -> str:
        return """
        /* 自定义组件样式 */
        Tab.-active {
            color: $primary;
        }
        """

# themes/__init__.py
from .dracula import DraculaTheme
from .my_theme import MyTheme

DRACULA_THEME = DraculaTheme()
MY_THEME = MyTheme()

# 默认主题
DEFAULT_THEME = DRACULA_THEME
```

### 主题切换预留接口

```python
# 未来功能：动态切换主题
class ThemeManager:
    def __init__(self):
        self._current_theme = DRACULA_THEME
        self._themes = {
            "dracula": DRACULA_THEME,
            # "default": DEFAULT_THEME,
            # "my_theme": MY_THEME,
        }

    def get_theme(self, name: str) -> Theme:
        return self._themes.get(name, self._current_theme)

    def set_theme(self, name: str):
        if name in self._themes:
            self._current_theme = self._themes[name]
            # TODO: Reload app CSS
```

---

## 质量保证

### 代码质量检查

**必须通过**:
```bash
poetry run ruff check --fix src/ tests/
poetry run ruff format src/ tests/
poetry run mypy src/
poetry run pytest
```

### 视觉验证

**终端ANSI颜色提取**:
```bash
# 运行应用并捕获输出
mise run dev 2>&1 | head -100 > /tmp/ariatuc_output.txt

# 提取所有RGB颜色
grep -o "38;2;[0-9]*;[0-9]*;[0-9]*" /tmp/ariatuc_output.txt | sort -u

# 验证预期颜色是否出现
```

**预期颜色列表**:
- `38;2;189;147;249` = #bd93f9 (Dracula Purple - 主边框)
- `38;2;254;166;43` = #FEA62B (用户橙色 - 激活Tab)
- `38;2;80;250;123` = #50fa7b (Dracula Green - 成功状态)
- `38;2;248;248;242` = #f8f8f2 (Dracula Foreground - 文本)
- `38;2;40;42;54` = #282a36 (Dracula Background - 背景)

### 功能验证

**Add Download滚动测试**:
1. 打开Add Download对话框 (a键)
2. 切换到URLs Tab
3. 输入多行URL（超过可见区域）
4. 向下滚动，验证Options字段可见
5. 切换到其他Tab，验证也能滚动
6. 验证Tab标签固定不滚动
7. 验证Buttons固定在底部

**表单紧凑度测试**:
1. 打开Add Download对话框
2. 检查Label和Input之间无过多空白
3. 检查Options section分组清晰
4. 检查对话框宽度合理（不过宽）
5. 检查所有字段可见且可交互

---

## 回滚策略

### 分阶段回滚

**阶段0回滚** (主题架构):
```bash
git checkout -- src/ariatuc/ui/themes/
```

**阶段1回滚** (应用主题):
```bash
git checkout -- src/ariatuc/ui/app.py
```

**阶段2回滚** (滚动修复):
```bash
git checkout -- src/ariatuc/ui/widgets/add_download_dialog.py
```

**阶段3回滚** (表单优化):
```bash
git checkout -- src/ariatuc/ui/widgets/add_download_dialog.py
git checkout -- src/ariatuc/ui/widgets/form_widget.py
git checkout -- src/ariatuc/ui/themes/dracula.py
```

### 完全重置

```bash
# 重置到UI调整前的commit
git reset --hard 3006496
```

---

## 实施时间表

| 阶段 | 任务 | 预计耗时 | 优先级 | 依赖 |
|------|------|---------|--------|------|
| **阶段0** | 创建主题架构 + Dracula主题 | 60分钟 | P0 | 无 |
| **阶段1** | 应用主题到App | 15分钟 | P1 | 阶段0 |
| **阶段2** | 修复Add Download滚动 | 45分钟 | P1 | 阶段1 |
| **阶段3** | 优化表单样式 | 60分钟 | P2 | 阶段2 |
| **阶段4** | Tab颜色微调 | 30分钟 | P3 | 阶段3 |

**总计**: 约3小时30分钟

---

## 成功标准

### 必须达成（Must Have）

- [ ] 主题架构创建完成，支持扩展
- [ ] Dracula主题正确应用，颜色符合规范
- [ ] 用户指定的5个颜色正确集成
- [ ] Add Download的每个Tab内容可以滚动
- [ ] Tab标签和Buttons固定不滚动
- [ ] 表单样式紧凑，无过多空白
- [ ] 所有现有信息完整显示
- [ ] 所有功能正常工作
- [ ] 代码质量检查全部通过

### 应该达成（Should Have）

- [ ] Add Download对话框宽度缩小到70列
- [ ] TextArea高度优化到6行
- [ ] Label和Input之间间距优化（无冗余）
- [ ] Options section布局清晰
- [ ] Tab激活状态使用橙色 (#FEA62B)

### 可以延后（Nice to Have）

- [ ] 主题热切换功能
- [ ] 主题配置持久化
- [ ] 更多主题选项（Light mode等）
- [ ] 主题预览功能

---

## 附录：Dracula主题色板完整映射

| 场景 | Dracula颜色 | 用户颜色 | 最终选择 | 用途 |
|------|------------|---------|---------|------|
| 主边框 | Purple #bd93f9 | Blue #4178C0 | **Purple** | 对话框边框 |
| 焦点高亮 | Pink #ff79c6 | Orange #FEA62B | **Orange** | 激活Tab、Accent |
| 成功状态 | Green #50fa7b | Green #4EBF71 | **Dracula Green** | 活动下载 |
| 警告状态 | Orange #ffb86c | Orange #FEA62B | **User Orange** | 警告、暂停 |
| 深色辅助 | - | Deep Blue #0053AA | **User Deep Blue** | primary-darken-2 |
| 信息提示 | Cyan #8be9fd | Blue #4178C0 | **Dracula Cyan** | 信息文本 |
| 错误状态 | Red #ff5555 | - | **Dracula Red** | 错误提示 |
| 背景 | #282a36 | - | **Dracula** | 主背景 |
| 文本 | #f8f8f2 | - | **Dracula** | 主文本 |
| 次要文本 | #6272a4 | - | **Dracula** | 注释、灰色 |

---

## 总结

这个方案V3的核心改进：

1. **✅ 完整的主题架构** - 支持多主题扩展
2. **✅ Dracula作为首个主题** - 集成用户的5个颜色
3. **✅ 表单样式优化** - 紧凑高效，参考Surge项目
4. **✅ 修复滚动功能** - 每个Tab内容可滚动
5. **✅ 保留所有信息** - 不移除任何数据字段
6. **✅ 渐进式实施** - 4个独立阶段，可随时回滚

通过这个方案，我们既满足了主题管理的需求，又优化了表单的屏幕利用率，同时修复了滚动功能的缺陷。

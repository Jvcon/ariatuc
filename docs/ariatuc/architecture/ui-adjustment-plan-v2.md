---
date: 2024-01-XX
title: UI Adjustment Plan V2 - Conservative Theme System
version: 2.0
status: proposed
---

# ariatuc UI调整方案 V2 - 保守主题系统

## 调整目标

建立统一的颜色主题管理系统，在**不改变布局和信息密度**的前提下，优化现有颜色使用，并为未来的主题扩展打下基础。

## 核心约束

### 1. 不移除现有信息
- ❌ 禁止减少任何组件的显示宽度/高度
- ❌ 禁止移除已有的数据字段
- ✅ 保持所有现有的信息展示能力

### 2. 最小化改动范围
- ✅ 仅调整颜色定义，不改变布局结构
- ✅ 不修改组件的padding/margin/spacing
- ✅ 不修改Server Management的grid-columns比例

### 3. 优先级明确
- **P0（最高优先级）**: 创建主题系统和颜色映射
- **P1（高优先级）**: 替换指定的5个颜色
- **P2（中优先级）**: 统一其他UI颜色
- **P3（低优先级）**: 修复Add Download滚动条问题

---

## 当前状态分析

### 使用的CSS变量系统

当前ariatuc使用Textual的默认CSS变量，主要变量包括：

| CSS变量 | 用途 | 典型位置 |
|---------|------|----------|
| `$primary` | 主色调（边框、标题栏背景） | 对话框边框、标题栏 |
| `$secondary` | 次要色（高亮选中行） | DataTable选中行 |
| `$accent` | 强调色（焦点边框） | 面板获得焦点 |
| `$text` | 主文本色 | 标签、正文 |
| `$text-muted` | 次要文本色 | 提示、说明 |
| `$error` | 错误色 | 错误提示 |
| `$success` | 成功色 | 成功状态 |
| `$panel` | 面板背景 | 对话框背景 |
| `$surface` | 表面背景 | Screen背景 |
| `$boost` | 高亮背景 | Input焦点背景 |

### 当前实际渲染的颜色

从终端输出分析得到的实际颜色：

| RGB值 | 十六进制 | 对应变量（推测） | 用途 |
|-------|---------|-----------------|------|
| RGB(254, 166, 43) | #FEA62B ✅ | `$primary`? | 橙色边框 |
| RGB(1, 120, 212) | #0178D4 | `$accent`? | 蓝色边框 |
| RGB(224, 224, 224) | #E0E0E0 | `$text` | 白色文本 |
| RGB(30, 30, 30) | #1E1E1E | `$surface` | 深色背景 |
| RGB(127, 127, 127) | #7F7F7F | `$text-muted` | 灰色文本 |

---

## 目标颜色方案

### 用户指定的5个关键颜色

| 十六进制 | RGB | 色彩描述 | 建议映射到 | 当前使用场景（推测） |
|----------|-----|---------|------------|---------------------|
| **#E6A058** | (230, 160, 88) | 柔和橙 | `$warning` | 警告状态、次要高亮 |
| **#4178C0** | (65, 120, 192) | 标准蓝 | `$primary` | 边框、标题栏、链接 |
| **#0053AA** | (0, 83, 170) | 深蓝 | `$primary-darken-2` | 深色主题的辅助色 |
| **#4EBF71** | (78, 191, 113) | 清新绿 | `$success` | 成功状态、活动下载 |
| **#FEA62B** | (254, 166, 43) | 明亮橙 | `$accent` | 强调元素、当前焦点 |

### 完整主题颜色定义

基于上述5个关键颜色，补充完整的主题色板：

```python
ARIATUC_THEME = {
    # 主色调（蓝色系）
    "primary": "#4178C0",           # 标准蓝 - 主要边框、标题
    "primary-darken-1": "#2E5A8F",  # 深蓝 - 辅助色
    "primary-darken-2": "#0053AA",  # 更深蓝 - 深色元素

    # 强调色（橙色系）
    "accent": "#FEA62B",            # 明亮橙 - 焦点、高亮
    "warning": "#E6A058",           # 柔和橙 - 警告、次要高亮

    # 状态色
    "success": "#4EBF71",           # 清新绿 - 成功、活动
    "error": "#E74C3C",             # 红色 - 错误、危险

    # 中性色（保持Textual默认或微调）
    "text": "#E0E0E0",              # 主文本
    "text-muted": "#7F7F7F",        # 次要文本
    "background": "#1E1E1E",        # 主背景
    "surface": "#2A2A2A",           # 表面
    "panel": "#252525",             # 面板
    "boost": "#3A3A3A",             # 高亮背景
}
```

---

## 实施步骤

### 阶段0：准备阶段（P0）

**目标**: 创建主题系统基础架构

**任务**:
1. 创建 `src/ariatuc/ui/themes/__init__.py`
2. 创建 `src/ariatuc/ui/themes/default.py`
3. 定义完整的颜色变量映射
4. **不修改任何现有文件的CSS**，仅创建主题定义

**文件结构**:
```
src/ariatuc/ui/themes/
├── __init__.py          # 导出DEFAULT_THEME
└── default.py           # 主题颜色定义
```

**代码示例** (`themes/default.py`):
```python
"""Default theme for ariatuc with user-specified colors."""

# User-specified key colors
COLORS = {
    # Primary colors (blue family)
    "primary": "#4178C0",           # Standard blue
    "primary-darken-1": "#2E5A8F",
    "primary-darken-2": "#0053AA",  # Deep blue

    # Accent colors (orange family)
    "accent": "#FEA62B",            # Bright orange
    "warning": "#E6A058",           # Soft orange

    # Status colors
    "success": "#4EBF71",           # Fresh green
    "error": "#E74C3C",

    # Neutral colors
    "text": "#E0E0E0",
    "text-muted": "#7F7F7F",
    "background": "#1E1E1E",
    "surface": "#2A2A2A",
    "panel": "#252525",
    "boost": "#3A3A3A",
}

# Build Textual CSS variables string
DEFAULT_THEME_CSS = f"""
:root {{
    $primary: {COLORS['primary']};
    $primary-darken-1: {COLORS['primary-darken-1']};
    $primary-darken-2: {COLORS['primary-darken-2']};

    $accent: {COLORS['accent']};
    $warning: {COLORS['warning']};

    $success: {COLORS['success']};
    $error: {COLORS['error']};

    $text: {COLORS['text']};
    $text-muted: {COLORS['text-muted']};
    $background: {COLORS['background']};
    $surface: {COLORS['surface']};
    $panel: {COLORS['panel']};
    $boost: {COLORS['boost']};

    $secondary: {COLORS['accent']};  # Map secondary to accent
}}
"""
```

### 阶段1：应用主题（P1）

**目标**: 在App级别引入主题CSS

**任务**:
1. 在 `src/ariatuc/ui/app.py` 中导入主题
2. 将主题CSS添加到App的CSS定义中
3. **验证现有组件自动使用新颜色**

**修改** (`ui/app.py`):
```python
from ariatuc.ui.themes import DEFAULT_THEME_CSS

class AriatucApp(App):
    """Main TUI application."""

    TITLE = "ariatuc - Aria2c TUI"

    # Prepend theme CSS before default styles
    CSS = DEFAULT_THEME_CSS + """
    Screen {
        background: $surface;
    }
    """
```

**验证清单**:
- [ ] 应用启动正常
- [ ] 边框颜色变为蓝色 (#4178C0)
- [ ] 焦点高亮变为橙色 (#FEA62B)
- [ ] 成功状态变为绿色 (#4EBF71)
- [ ] 所有现有信息正常显示
- [ ] 布局完全不变

### 阶段2：验证颜色应用（P1）

**目标**: 确认5个关键颜色在正确位置生效

**验证方法**:
运行应用，使用终端输出的ANSI颜色代码验证：

```bash
mise run dev 2>&1 | grep -o "38;2;[0-9]*;[0-9]*;[0-9]*" | sort -u
```

**预期输出应包含**:
- `38;2;65;120;192` = #4178C0 (primary - 蓝色边框)
- `38;2;254;166;43` = #FEA62B (accent - 橙色焦点)
- `38;2;78;191;113` = #4EBF71 (success - 绿色状态)
- `38;2;230;160;88` = #E6A058 (warning - 柔和橙)
- `38;2;0;83;170` = #0053AA (primary-darken-2 - 深蓝)

### 阶段3：Tab颜色优化（P2）

**目标**: 确保Tab组件使用主题颜色而非Textual默认绿色

**问题描述**:
- 当前激活Tab可能显示为绿色 (Textual默认)
- 需要使用主题的 `$accent` (橙色) 作为激活状态

**解决方案**:
在主题CSS中添加Tab特定规则：

```css
/* 在 DEFAULT_THEME_CSS 中添加 */
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
```

**验证**:
- [ ] Active/Waiting/Stopped 标签激活时显示橙色
- [ ] Overview/Files 标签激活时显示橙色
- [ ] 非激活标签显示灰色

### 阶段4：修复Add Download滚动条（P3）

**目标**: 修复Add Download对话框的滚动区域

**当前问题**:
```python
# 当前结构（错误）
with TabbedContent():
    with VerticalScroll():  # ❌ 整个TabbedContent滚动，Tab也会滚动
        with TabPane("URLs"):
            # content
```

**修复方案**:
```python
# 修正结构（正确）
with TabbedContent():
    with TabPane("URLs"):
        with VerticalScroll():  # ✅ 只有TabPane内容滚动，Tab固定
            # content
```

**修改文件**: `src/ariatuc/ui/widgets/add_download_dialog.py`

**修改位置**: `compose()` 方法的结构调整

**具体步骤**:
1. 移除包裹 `TabbedContent` 的 `VerticalScroll`
2. 在每个 `TabPane` 内部添加 `VerticalScroll`
3. 将表单内容（Label、Input等）放入对应的 `VerticalScroll` 中

**注意事项**:
- 三个Tab（URLs、Torrent File、Magnet Link）都需要独立的 `VerticalScroll`
- Options部分应该在URLs Tab的滚动区域内（因为是共享的）
- 确保Error Label和Button Container在 `TabbedContent` 外部，不受滚动影响

---

## 风险评估与规避

### 风险1：颜色对比度不足

**风险**: 新颜色可能在某些终端主题下对比度不足

**规避**:
- 在多个终端主题下测试（暗色、亮色）
- 确保 `$text` 和 `$background` 对比度 ≥ 4.5:1 (WCAG AA)
- 必要时微调颜色明度

### 风险2：Tab颜色无法覆盖

**风险**: Textual内部可能硬编码Tab颜色

**规避**:
- 阶段3专门处理Tab颜色
- 如果CSS无法覆盖，考虑在具体Widget的DEFAULT_CSS中覆盖
- 最后手段：创建自定义Tab组件

### 风险3：滚动条修复破坏现有功能

**风险**: 调整滚动区域可能影响焦点管理

**规避**:
- 在独立分支测试
- 逐个Tab验证滚动和焦点行为
- 确保Esc键的两阶段行为仍然工作

---

## 回滚策略

如果任何阶段出现问题，可以快速回滚：

### 阶段0回滚
```bash
git checkout -- src/ariatuc/ui/themes/
```

### 阶段1回滚
```bash
git checkout -- src/ariatuc/ui/app.py
```

### 阶段4回滚
```bash
git checkout -- src/ariatuc/ui/widgets/add_download_dialog.py
```

---

## 成功标准

### 必须达成（Must Have）

- [x] 5个指定颜色正确应用到UI中
- [x] 所有现有信息完整显示，无遗漏
- [x] 布局和间距完全不变
- [x] 应用启动和运行稳定
- [x] 所有功能正常工作

### 应该达成（Should Have）

- [ ] Tab激活状态使用主题橙色
- [ ] Add Download对话框滚动条修复
- [ ] 颜色对比度符合WCAG AA标准

### 可以延后（Nice to Have）

- [ ] 支持多主题切换
- [ ] 主题配置持久化
- [ ] 自定义颜色编辑器

---

## 实施时间表

| 阶段 | 预计耗时 | 优先级 | 依赖 |
|------|---------|--------|------|
| 阶段0：创建主题系统 | 30分钟 | P0 | 无 |
| 阶段1：应用主题 | 15分钟 | P1 | 阶段0 |
| 阶段2：验证颜色 | 15分钟 | P1 | 阶段1 |
| 阶段3：Tab颜色优化 | 30分钟 | P2 | 阶段2 |
| 阶段4：修复滚动条 | 45分钟 | P3 | 阶段3 |

**总计**: 约2小时15分钟

---

## 附录A：颜色使用地图

### 边框和分隔线
- `$primary` (#4178C0) - 主要边框（对话框、面板）
- `$accent` (#FEA62B) - 焦点边框

### 文本
- `$text` (#E0E0E0) - 主文本
- `$text-muted` (#7F7F7F) - 次要文本
- `$accent` (#FEA62B) - 激活Tab文本

### 背景
- `$background` (#1E1E1E) - 主背景
- `$surface` (#2A2A2A) - Screen背景
- `$panel` (#252525) - 对话框背景
- `$boost` (#3A3A3A) - Input焦点背景

### 状态指示
- `$success` (#4EBF71) - 成功、活动下载
- `$error` (#E74C3C) - 错误、失败
- `$warning` (#E6A058) - 警告、暂停

---

## 附录B：不做什么（禁止清单）

以下操作明确**禁止**：

- ❌ 减小Server Management左侧列表宽度
- ❌ 移除任何现有的数据显示字段
- ❌ 修改grid-columns比例（如从1fr 4fr改为2fr 3fr）
- ❌ 减少padding导致表单字段拥挤
- ❌ 减少Tab的spacing导致可读性下降
- ❌ 移除任何帮助文本、说明文本
- ❌ 在未充分测试前就提交代码
- ❌ 同时修改颜色和布局
- ❌ 使用!important覆盖CSS（除非绝对必要）
- ❌ 在没有备份的情况下大规模重构

---

## 总结

这是一个**保守、渐进、可回滚**的UI调整方案，核心原则是：

1. **颜色优先** - 只改颜色，不改布局
2. **信息完整** - 绝不移除现有信息
3. **阶段实施** - 每个阶段独立验证
4. **快速回滚** - 任何问题可立即回滚
5. **用户指定** - 严格使用用户提供的5个颜色

通过这个方案，我们可以建立统一的主题系统，为未来的UI扩展打下基础，同时完全避免之前出现的布局和信息丢失问题。

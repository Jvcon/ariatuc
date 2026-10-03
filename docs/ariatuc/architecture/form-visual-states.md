# Form Field Visual States

ariatuc 使用丰富的视觉反馈系统来区分表单字段的不同状态，帮助用户清楚地了解当前正在做什么。

## 视觉状态概览

### 1. VIEW 模式 - 可编辑字段高亮

**触发条件：**
- 在 VIEW 模式下使用 `j`/`k` 导航到可编辑字段

**视觉效果：**
- 边框：`tall $accent`（加粗的强调色边框）
- 背景：`$boost`（提升的背景色）

**目的：**
- 清楚指示当前"查看"的字段位置
- 与 EDIT 模式的 focus 状态区分开
- 提示用户按 `i` 可以进入编辑

**CSS 类：**
```css
.view-highlighted
```

---

### 2. VIEW 模式 - 只读字段高亮

**触发条件：**
- 在 VIEW 模式下使用 `j`/`k` 导航到不可编辑（disabled）字段

**视觉效果：**
- 边框：`tall $primary`（主色边框）
- 背景：`$surface-darken-1`（较暗的表面色）
- 透明度：`0.9`（略微透明）

**目的：**
- 表明当前字段不可编辑
- 与可编辑字段高亮有明显区别
- 保持视觉一致性

**CSS 类：**
```css
.view-highlighted:disabled
```

---

### 3. EDIT 模式 - 聚焦字段

**触发条件：**
- 字段获得键盘焦点（focus）
- 用户正在输入

**视觉效果：**
- 边框：`heavy $success`（加粗的成功色边框）
- 背景：`$panel`（面板背景色）

**目的：**
- 明确指示用户正在编辑的字段
- 使用成功色（通常是绿色）表示"准备好输入"
- 与 VIEW 模式高亮完全不同的视觉语言

**CSS 类：**
```css
:focus (native pseudo-class)
```

---

### 4. 修改标记

**触发条件：**
- 字段值被修改（与初始值不同）

**视觉效果：**
- 左边框：`thick $accent`（加粗的强调色左边框）
- 左内边距：`1`（避免内容贴边）

**目的：**
- 持久标记已修改的字段
- 帮助用户追踪哪些内容被改过
- 配合"仅保存修改字段"的功能

**CSS 类：**
```css
.form-field-modified
```

---

### 5. 校验错误 - 无焦点

**触发条件：**
- 字段值不满足验证规则
- 字段当前没有焦点

**视觉效果：**
- 边框：`heavy $error`（加粗的错误色边框）
- 背景：`$error 10%`（10% 透明度的错误色背景）

**目的：**
- 醒目地标记无效字段
- 在不干扰输入的情况下显示错误
- 配合错误消息文本

**CSS 类：**
```css
.invalid
```

---

### 6. 校验错误 - 有焦点

**触发条件：**
- 字段值不满足验证规则
- 用户正在编辑该字段

**视觉效果：**
- 边框：`heavy $error`（加粗的错误色边框）
- 背景：`$error 20%`（20% 透明度的错误色背景，略深）

**目的：**
- 在用户输入时持续提醒错误
- 背景略深以增强视觉反馈
- 鼓励用户修正错误

**CSS 类：**
```css
.invalid:focus
```

---

## 状态优先级

当多个状态同时存在时，CSS 的优先级规则确保正确的视觉效果：

### 优先级从高到低

1. **EDIT 模式焦点** (`:focus`) - 最高优先级
   - 压制所有其他状态
   - 用户正在输入时最重要

2. **校验错误焦点** (`.invalid:focus`)
   - 覆盖普通焦点样式
   - 错误状态比成功状态更需要注意

3. **校验错误无焦点** (`.invalid`)
   - 持续显示错误
   - 即使字段失去焦点

4. **VIEW 模式高亮** (`.view-highlighted`)
   - 导航时的视觉引导
   - 不会与焦点冲突（VIEW 模式下不会有焦点）

5. **修改标记** (`.form-field-modified`)
   - 最低优先级
   - 作为辅助标记存在

## 实现细节

### FormWidget 方法

```python
# VIEW 模式导航高亮
form_widget.highlight_field(field_key)  # 高亮指定字段
form_widget.clear_highlight()           # 清除所有高亮

# 自动应用的状态
form_widget.validate_all()              # 自动添加/移除 .invalid class
# 字段变化时自动添加/移除 .form-field-modified
```

### Screen 集成

```python
def _navigate_field(self, direction: int):
    """VIEW 模式下导航字段"""
    field_keys = form.get_field_keys()
    self._current_field_index = (index + direction) % len(field_keys)

    # 高亮当前字段
    form.highlight_field(field_keys[self._current_field_index])

def action_enter_edit_mode(self):
    """进入 EDIT 模式"""
    # 清除 VIEW 高亮
    form.clear_highlight()

    # 聚焦第一个字段（触发 :focus 样式）
    first_field.focus()
```

## 用户体验流程

### 典型工作流示例

```
[VIEW 模式]
j j j                  → 字段依次显示 .view-highlighted 样式
                         (accent 边框, boost 背景)

到达目标字段
i                      → 清除 .view-highlighted
                         字段获得 :focus
                         (success 边框, panel 背景)

[EDIT 模式]
输入内容              → 自动添加 .form-field-modified
                         (左侧 accent 粗边框)

输入无效值            → 自动添加 .invalid
                         (error 边框和背景)
                         显示错误消息

修正错误              → 自动移除 .invalid
                         恢复正常 :focus 样式

Esc                   → 失去焦点，返回 VIEW 模式
                         保留 .form-field-modified 标记
```

## 设计理念

### 1. **清晰的模式区分**

- VIEW 模式用 accent 色（通常是蓝色/青色）
- EDIT 模式用 success 色（通常是绿色）
- 错误状态用 error 色（通常是红色）

### 2. **渐进增强**

- 基础状态：无标记
- 导航状态：VIEW 高亮
- 编辑状态：EDIT 焦点
- 修改状态：左边框标记
- 错误状态：全边框+背景

### 3. **非干扰性**

- VIEW 高亮不会抢占焦点
- 修改标记是左侧边框，不影响阅读
- 错误状态背景透明度低，不刺眼

### 4. **即时反馈**

- j/k 导航立即更新高亮
- 输入时实时验证和标记
- 模式切换立即改变视觉状态

## 相关文档

- [Unified Navigation Model](./unified-navigation-model.md) - 统一导航模式
- [Server Management Testing](./server-management-testing.md) - 服务器管理测试指南

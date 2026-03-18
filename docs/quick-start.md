# Quick Start Guide - ariatuc

快速开始使用 ariatuc TUI 应用进行 aria2c 下载管理。

## 前置要求

```bash
# 1. 安装 aria2c
# macOS
brew install aria2

# Ubuntu/Debian
sudo apt install aria2

# Arch Linux
sudo pacman -S aria2

# 2. 安装项目依赖
poetry install
```

## 运行方式

ariatuc 支持两种运行方式：源代码运行和用户二进制运行。

### 源代码运行

从源代码运行 ariatuc，适合开发和测试环境。

#### 方式 1: 使用 mise 任务运行（推荐）

##### 一键启动（最简单）

自动启动 aria2c 服务和 TUI 应用：

```bash
mise run start
```

这个命令会：
1. 自动启动 aria2c RPC 服务器（如果尚未运行）
2. 验证服务器状态
3. 启动 ariatuc TUI 应用

##### 分步启动

如果你想分别控制各个组件：

**步骤 1: 启动 aria2c RPC 服务器**

```bash
mise run aria2:start
```

输出示例：
```
============================================================
Starting aria2c RPC Server
============================================================

✓ Setting up aria2c configuration...
✓ Configuration created at: .aria2/aria2.conf
✓ aria2c started successfully (PID: 12345)
✓ RPC is ready!

✓ RPC URL: http://localhost:6800/jsonrpc
✓ Log file: .aria2/aria2.log
✓ Downloads: .aria2/downloads/
```

**步骤 2: 启动 TUI 应用**

在另一个终端窗口：

```bash
mise run dev
```

##### aria2c 服务器管理

```bash
# 查看服务器状态
mise run aria2:status

# 停止服务器
mise run aria2:stop

# 重启服务器
mise run aria2:restart

# 查看日志（最后 50 行）
mise run aria2:logs

# 实时跟踪日志
mise run aria2:logs:follow
```

##### 开发命令

```bash
# 运行测试
mise run test              # 所有测试
mise run test:unit         # 仅单元测试
mise run test:integration  # 仅集成测试

# 代码质量
mise run lint              # 代码检查
mise run format            # 格式化代码
```

#### 方式 2: 手动执行

不使用 mise 任务，直接通过 Python 或 Poetry 运行。

##### 启动 aria2c RPC 服务器

```bash
# 使用项目提供的启动脚本
python scripts/start_aria2.py
```

##### 启动 TUI 应用

选择以下任一方式启动应用（所有方式等效）：

```bash
# 方式 1: 通过 Python 模块
python -m ariatuc

# 方式 2: 通过 poetry 运行
poetry run ariatuc

# 方式 3: 通过 poetry 脚本
poetry run python -m ariatuc

# 方式 4: 通过启动脚本
python scripts/start_app.py
```

### 用户二进制运行

> **注意**: 用户二进制打包功能目前尚未实现。
>
> 计划中的功能：
> - 预编译的可执行文件（无需 Python 环境）
> - 一键安装和启动
> - 跨平台支持（macOS, Linux, Windows）
>
> 目前请使用源代码运行方式。

## 基本使用

### 键盘快捷键

**全局快捷键**:
- `?` - 显示帮助
- `q` - 退出应用
- `Tab` - 在面板间切换焦点

**下载列表**:
- `j/k` 或 `↑/↓` - 上下导航
- `1/2/3` - 切换标签（活动/等待/已停止）
- `Enter` - 查看下载详情

**下载操作**:
- `a` - 添加新下载
- `d` - 删除选中的下载
- `p` - 暂停/恢复下载
- `r` - 刷新下载列表

**对话框**:
- `Enter` - 确认
- `Esc` - 取消
- `Tab` - 下一个字段
- `Ctrl+s` - 保存（在添加对话框中）

### 添加下载

1. 按 `a` 打开添加下载对话框
2. 输入一个或多个 URL（每行一个）
3. 可选设置下载选项：
   - 下载目录
   - 每服务器最大连接数
   - 分片数（每文件连接数）
4. 按 `Enter` 或 `Ctrl+s` 添加

### 示例：下载文件

```
# 1. 启动服务和应用
mise run start

# 2. 在 TUI 中按 'a' 打开添加对话框
# 3. 输入 URL：
http://example.com/file.zip
http://mirror.com/file.iso

# 4. 可选设置下载目录：
/Users/你的用户名/Downloads

# 5. 按 Enter 开始下载
# 6. 按 '1' 查看活动下载
# 7. 按 'p' 暂停/恢复
# 8. 按 'd' 删除下载
```

## 配置

### 自动配置（首次运行）

ariatuc 首次运行时会自动创建配置文件，包含默认的 localhost 服务器：

**配置文件位置**: `~/.config/ariatuc/config.json`

**默认配置**:
```json
{
  "servers": [
    {
      "name": "local",
      "url": "http://localhost:6800/jsonrpc",
      "secret": null
    }
  ],
  "current_server": "local"
}
```

应用启动时会自动连接到这个服务器，无需手动配置！✨

### 修改配置

如果你的 aria2c 运行在不同的地址或端口，编辑配置文件：

```bash
# 编辑配置文件
vim ~/.config/ariatuc/config.json

# 或者使用你喜欢的编辑器
code ~/.config/ariatuc/config.json
```

**示例 - 修改端口**:
```json
{
  "servers": [
    {
      "name": "local",
      "url": "http://localhost:8080/jsonrpc",
      "secret": "your-secret-token"
    }
  ]
}
```

**示例 - 添加多个服务器**:
```json
{
  "servers": [
    {
      "name": "local",
      "url": "http://localhost:6800/jsonrpc",
      "secret": null
    },
    {
      "name": "remote",
      "url": "https://remote.example.com:6800/jsonrpc",
      "secret": "remote-secret"
    }
  ],
  "current_server": "local"
}
```

### aria2c 服务器配置

配置文件位置：`.aria2/aria2.conf`

默认设置：
- **RPC URL**: `http://localhost:6800/jsonrpc`
- **端口**: 6800
- **认证**: 无（开发环境）
- **下载目录**: `.aria2/downloads/`
- **最大并发下载**: 5
- **每服务器连接数**: 16

## 常见问题

### aria2c 无法启动

**错误**: "aria2c command not found"
- **解决**: 安装 aria2c（见前置要求）

**错误**: "Port 6800 already in use"
- **解决**:
  ```bash
  # 查找占用端口的进程
  lsof -i :6800

  # 或停止现有的 aria2c
  mise run aria2:stop
  ```

### 应用无法连接

1. 检查 aria2c 是否运行：
   ```bash
   mise run aria2:status
   ```

2. 测试 RPC 端点：
   ```bash
   curl http://localhost:6800/jsonrpc
   ```

3. 查看日志：
   ```bash
   mise run aria2:logs
   ```

### 下载未出现

- 检查 URL 是否有效
- 查看 aria2c 日志是否有错误
- 确认下载目录权限

## 目录结构

```
.aria2/                 # aria2c 服务器文件（自动创建）
├── aria2.conf          # 服务器配置
├── aria2.log           # 服务器日志
├── aria2.pid           # 进程 ID
├── session.txt         # 会话持久化
└── downloads/          # 默认下载目录

~/.config/ariatuc/      # 应用配置目录
└── config.json         # 应用配置文件
```

## 下一步

- 功能路线图： `TODO.md`

## 获取帮助

- 在 TUI 中按 `?` 查看所有快捷键
- 查看 aria2c 日志：`mise run aria2:logs`
- 查看问题追踪器：GitHub Issues

---

**享受使用 ariatuc！** 🚀

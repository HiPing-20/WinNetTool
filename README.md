# WinNetTool - 网络工具箱

![Python Version](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![GUI Framework](https://img.shields.io/badge/GUI-PyQt6-41cd52?style=flat-square&logo=qt)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square)

## 项目简介

WinNetTool 是一款基于 Python 和 PyQt6 开发的 Windows 综合网络工具箱，提供本地端口管理、DHCP 配置、Hosts 文件管理、系统服务控制、Wi-Fi/局域网扫描等功能。采用深色主题 UI，所有操作通过后台线程执行，不会阻塞界面。

## 功能列表

### 端口管理
- **本地端口查询** — 实时查看所有本地监听端口、占用进程和状态
- **防火墙规则** — 查看 Windows 防火墙入站规则（支持中英文）
- **开放端口** — 通过防火墙规则添加端口放行
- **关闭端口** — 禁用指定防火墙规则
- **删除端口规则** — 永久删除防火墙规则
- **局域网端口扫描** — 使用 Nmap 扫描指定 IP 范围的开放端口（支持 CIDR）
- **端口分布图** — ASCII 直方图展示本地端口使用频率 TOP N

### DHCP 管理
- **DHCP 信息** — 查看所有网络适配器的 DHCP 配置（IP、DHCP 服务器、启用状态）
- **DHCP 服务器** — 列出当前活动的 DHCP 服务器地址
- **释放 IP** — 执行 `ipconfig /release`
- **续订 IP** — 执行 `ipconfig /renew`

### Hosts 管理
- **查看 Hosts** — 读取 `C:\Windows\System32\drivers\etc\hosts` 文件
- **添加 Host** — 添加新的 IP-域名映射（自动检测重复）
- **修改 Host** — 修改已有域名的 IP 地址
- **删除 Host** — 删除指定域名记录
- **备份 Hosts** — 备份 Hosts 文件到同目录（带时间戳）

### 系统服务
- **服务列表** — 列出所有系统服务（名称、状态、启动类型、PID），状态彩色标记
- **启动服务** — 启动指定 Windows 服务
- **停止服务** — 停止指定 Windows 服务（带确认提示）
- **重启服务** — 停止后重新启动服务
- **操作日志** — 记录所有服务操作的历史

### Wi-Fi / 局域网
- **周边 Wi-Fi** — 扫描周围 Wi-Fi 网络（SSID、信号强度、认证方式、加密、频道）
- **当前连接** — 查看当前 Wi-Fi 连接详情（信号、速率、频道、无线电类型）
- **局域网设备** — 基于 ARP 表获取局域网内所有设备的 IP 和 MAC 地址
- **局域网拓扑图** — 生成 HTML 拓扑图（SVG 渲染），自动在浏览器打开

### 其他
- **检查更新** — 通过 GitHub Releases API 检查新版本
- **保存结果** — 表格数据导出为 JSON，文本数据导出为 TXT
- **搜索过滤** — 所有表格支持实时搜索过滤

## 项目结构

```
WinNetTool/
├── main.py                      # 程序入口
├── requirements.txt             # Python 依赖
├── WinNetTool.spec              # PyInstaller 打包配置
├── app_icon.ico                 # 应用图标
├── utils.py                     # 工具函数（文件保存、图表生成）
│
├── network/                     # 后端模块
│   ├── __init__.py              # 模块导出
│   ├── base.py                  # 命令执行、编码处理
│   ├── ports.py                 # 端口管理、防火墙、Nmap 扫描
│   ├── dhcp.py                  # DHCP 信息获取
│   ├── hosts.py                 # Hosts 文件读写
│   ├── services.py              # Windows 服务管理
│   ├── wifi.py                  # Wi-Fi 和局域网设备
│   └── version.py               # 版本检查
│
├── gui/                         # 前端模块
│   ├── __init__.py              # 模块导出
│   ├── main_window.py           # 主窗口、侧边栏、路由
│   ├── styles.py                # QSS 样式表（Tokyo Night 主题）
│   ├── workers.py               # 后台工作线程
│   ├── dialogs.py               # 通用对话框
│   └── panels/                  # 功能面板
│       ├── __init__.py
│       ├── welcome.py           # 欢迎页
│       ├── port_panel.py        # 端口管理相关
│       ├── dhcp_panel.py        # DHCP 管理相关
│       ├── host_panel.py        # Hosts 管理相关
│       ├── service_panel.py     # 系统服务相关
│       ├── wifi_panel.py        # Wi-Fi / 局域网相关
│       └── update_panel.py      # 检查更新
│
├── dist/                        # 打包输出
│   └── WinNetTool.exe
└── build/                       # 构建缓存
```

## 环境要求

- **操作系统：** Windows 10 / 11（需要管理员权限）
- **Python：** 3.11 或更高版本
- **Nmap：** 需要安装 [Nmap](https://nmap.org/download.html) 并添加到系统 PATH（端口扫描功能依赖）

## 快速开始

### 方式一：直接运行源码

```bash
# 1. 克隆仓库
git clone https://github.com/HiPing-20/WinNetTool.git
cd WinNetTool

# 2. 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 以管理员身份运行（右键终端 → 以管理员身份运行）
python main.py
```

### 方式二：运行打包后的 EXE

直接双击 `dist/WinNetTool.exe`，程序会自动请求管理员权限。

## 构建 EXE

### 步骤 1：安装 PyInstaller

```bash
pip install pyinstaller
```

### 步骤 2：执行打包

在项目根目录运行：

```bash
pyinstaller --clean WinNetTool.spec
```

或者使用手动命令：

```bash
pyinstaller --noconsole --onefile --windowed --name "WinNetTool" main.py
```

### 步骤 3：获取输出

打包完成后，可执行文件位于：

```
dist\WinNetTool.exe
```

### 打包说明

- `--noconsole` / `--windowed`：不显示控制台窗口
- `--onefile`：打包为单个 EXE 文件
- `--name "WinNetTool"`：指定输出文件名
- `WinNetTool.spec`：预配置了所有必要的 `hiddenimports`，推荐使用 spec 文件打包

### 打包后注意事项

1. EXE 需要**管理员权限**才能运行（已配置 `uac_admin=True`）
2. 图标已嵌入 EXE，无需额外携带 `app_icon.ico`
3. 如需修改更新检查 URL，编辑 `gui/main_window.py` 中的 `UPDATE_CHECK_URL`

## 配置说明

### 更新检查 URL

在 `gui/main_window.py` 中修改：

```python
UPDATE_CHECK_URL = "https://api.github.com/repos/HiPing-20/WinNetTool/releases/latest"
```

当你在 GitHub 发布新 Release 后，应用内的「检查更新」功能会自动检测到新版本。

### 发布新版本

1. 修改 `gui/main_window.py` 中的 `CURRENT_VERSION`
2. 提交代码并推送
3. 在 GitHub 仓库创建新的 Release，Tag 格式为 `v1.0.0`
4. 上传打包好的 EXE 作为 Release Asset

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| GUI | PyQt6 |
| 端口扫描 | python-nmap |
| 进程/服务 | psutil |
| HTTP 请求 | requests |
| 打包 | PyInstaller |
| UI 主题 | Tokyo Night（深色） |

## 常见问题

**Q: 提示"请使用管理员权限运行软件"？**
A: 右键点击程序，选择「以管理员身份运行」。

**Q: 端口扫描功能不工作？**
A: 需要安装 Nmap 并确保 `nmap.exe` 在系统 PATH 中。下载地址：https://nmap.org/download.html

**Q: 防火墙规则显示乱码？**
A: 程序已内置编码自动检测，支持中英文系统。如仍有问题，请检查系统区域设置。

**Q: 打包后的 EXE 体积较大？**
A: 这是正常的，PyInstaller 会将 Python 解释器和所有依赖库打包进 EXE。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证。

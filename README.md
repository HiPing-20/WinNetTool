# WinNetTool - 强大的网络工具箱 ⚙️

![Python Version](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![GUI Framework](https://img.shields.io/badge/GUI-PyQt6-green?style=for-the-badge&logo=qt)
![License](https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge)

## 🌟 项目简介

WinNetTool 是一款基于 Python 3.11+ 和 PyQt6 开发的综合性网络工具箱，旨在为 Windows 用户提供便捷、高效的网络管理和诊断功能。从本地端口监控到局域网设备扫描，从 Hosts 文件管理到系统服务控制，WinNetTool 致力于成为你桌面上的全能网络助手。

## ✨ 主要功能

本项目的开发路线图分为多个阶段，以下是已实现和规划中的核心功能：

### 阶段一：核心原型 (已完成)
- **GUI 主窗口**：模块选择、内容区、日志显示。
- **本地端口查询**：实时查看端口占用情况。
- **本地端口开放/关闭**：动态管理防火墙端口规则。
- **局域网端口扫描**：扫描指定 IP 范围内的开放端口。
- **临时文件保存扫描结果**：方便导出和分析数据。
- **多线程异步操作**：保证 GUI 不卡顿，提升用户体验。

### 阶段二：DHCP & Hosts (已完成)
- **DHCP 信息解析与显示**：查看 DHCP 配置详情。
- **Hosts 文件管理**：查看、编辑、添加、删除、备份 Hosts 记录。
- **权限提示弹窗**：确保敏感操作在管理员权限下进行。
- **IP 释放/续订**：方便管理网络适配器的 IP 地址。

### 阶段三：系统服务管理 (已完成)
- **查询本地服务状态**：启动、停止、重启系统服务。
- **日志记录用户操作**：跟踪服务管理的历史行为。

### 阶段四：局域网 / Wi-Fi 扩展 (已完成)
- **扫描局域网在线设备**：发现当前网络中的所有活跃设备 (基于 ARP 表)。
- **Wi-Fi 信号强度分析 / IP / MAC**：获取周边 Wi-Fi 列表和当前连接详情。
- **可选生成局域网拓扑图**：生成 DOT 格式的拓扑描述，可通过 Graphviz 渲染。

### 阶段五：可选可视化 (部分完成)
- **ASCII 显示端口分布**：以文本形式展示本地端口使用频率直方图。
- **局域网拓扑图文本描述**：生成 DOT 格式文本，需配合 Graphviz 渲染为图形。
- **趣味性工具扩展**：待规划具体功能。

### 阶段六：UI & 优化 (部分完成)
- **简洁风格、现代按钮、状态提示**：已通过 PyQt6 实现美观的 UI 样式。
- **日志、进度条、扫描提示**：提供清晰的操作反馈。
- **滚动条 / 表格样式优化**：提升数据显示效果。

### 阶段七：打包与发布 (待完成)
- **PyInstaller 打包 EXE**：将 Python 项目打包为 Windows 可执行文件。
- **自动更新与版本检查**：已实现版本检查接口。
- **测试 Windows 7 / 10 / 11 兼容性**：待进行环境测试。

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的GitHub用户名/WinNetTool.git
cd WinNetTool
```
请将 `你的GitHub用户名` 替换为你的实际 GitHub 用户名。

### 2. 创建并激活虚拟环境 (推荐)
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source ./.venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 运行程序 (需要管理员权限)
```bash
# 在激活虚拟环境后
python main.py
```
**注意：** 程序需要管理员权限才能正常执行大部分网络和系统服务操作。请右键点击 `main.py` 或打包后的 `WinNetTool.exe`，选择“以管理员身份运行”。

## 📦 打包成 EXE (使用 PyInstaller)

### 1. 安装 PyInstaller
```bash
pip install pyinstaller
```

### 2. 打包命令 (单文件 EXE)
在项目根目录的命令行中执行：
```bash
pyinstaller --noconsole --onefile --windowed --name "WinNetTool" main.py
```
打包完成后，你会在 `dist/` 文件夹中找到 `WinNetTool.exe` 可执行文件。

## 📝 更新检查 (重要配置)

为了使应用内的“检查更新”功能正常工作，你需要修改 `gui.py` 文件中的 `UPDATE_CHECK_URL` 变量，将其指向你自己的 GitHub 仓库 Releases API 地址。

打开 `gui.py` 文件，找到 `MainWindow` 类，修改：
```python
UPDATE_CHECK_URL = "https://api.github.com/repos/你的GitHub用户名/你的仓库名/releases/latest" 
```
将 `你的GitHub用户名` 和 `你的仓库名` 替换为你的实际信息。

## 🤝 贡献
欢迎提交 Pull Request 或报告 Bug！

## 📄 许可证
本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件 (如果存在)。
import sys
import platform


def show_welcome(window):
    window._show_text_view()
    window.text_display_area.setText("")
    window.table.clear()
    window.table.setRowCount(0)
    window.table.setColumnCount(0)

    window.label_title.setText("欢迎使用 WinNetTool")
    window.label_status.setText(
        f"版本 v{window.CURRENT_VERSION}  |  {platform.system()} {platform.release()}  |  Python {sys.version.split(' ')[0]}"
    )
    window.search_box.setPlaceholderText("搜索...")

    win_ver = platform.version()
    win_ver_name = f"{platform.system()} {platform.release()} ({win_ver})"

    window.text_display_area.setHtml(f"""
        <div style="padding: 24px; font-size: 10pt; color: #c0caf5; line-height: 1.6;">
            <div style="text-align: center; padding: 30px 0 20px 0;">
                <div style="font-size: 28pt; color: #7aa2f7; font-weight: bold; letter-spacing: 2px;">
                    WinNetTool
                </div>
                <div style="font-size: 11pt; color: #565f89; margin-top: 4px;">
                    网络工具箱 v{window.CURRENT_VERSION}
                </div>
            </div>

            <div style="background-color: #1f2335; border: 1px solid #292e42; border-radius: 12px; padding: 20px; margin: 16px 0;">
                <div style="color: #7aa2f7; font-weight: bold; font-size: 11pt; margin-bottom: 12px;">
                    功能概览
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #292e42; width: 50%;">
                            <span style="color: #7aa2f7;">&#9881;</span>
                            <b>端口管理</b> - 本地端口 / 防火墙 / 扫描 / 分布图
                        </td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #292e42;">
                            <span style="color: #9ece6a;">&#9881;</span>
                            <b>DHCP 管理</b> - 信息查看 / 服务器 / IP 释放续订
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #292e42;">
                            <span style="color: #e0af68;">&#9998;</span>
                            <b>Hosts 管理</b> - 查看 / 添加 / 修改 / 删除 / 备份
                        </td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #292e42;">
                            <span style="color: #bb9af7;">&#9874;</span>
                            <b>系统服务</b> - 列表 / 启动 / 停止 / 重启 / 日志
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #292e42;">
                            <span style="color: #f7768e;">&#9741;</span>
                            <b>Wi-Fi / 局域网</b> - 周边WiFi / 连接详情 / 设备 / 拓扑图
                        </td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #292e42;">
                            <span style="color: #7dcfff;">&#10024;</span>
                            <b>检查更新</b> - 版本检查与下载
                        </td>
                    </tr>
                </table>
            </div>

            <div style="background-color: #1f2335; border: 1px solid #292e42; border-radius: 12px; padding: 20px; margin: 16px 0;">
                <div style="color: #7aa2f7; font-weight: bold; font-size: 11pt; margin-bottom: 12px;">
                    环境信息
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 12px; color: #565f89; width: 120px;">当前版本</td>
                        <td style="padding: 6px 12px; color: #9ece6a;">v{window.CURRENT_VERSION}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 12px; color: #565f89;">操作系统</td>
                        <td style="padding: 6px 12px; color: #c0caf5;">{win_ver_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 12px; color: #565f89;">Python</td>
                        <td style="padding: 6px 12px; color: #c0caf5;">{sys.version.split(' ')[0]}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 12px; color: #565f89;">GUI 框架</td>
                        <td style="padding: 6px 12px; color: #c0caf5;">PyQt6</td>
                    </tr>
                </table>
            </div>

            <div style="text-align: center; padding: 16px 0; color: #565f89; font-size: 9pt;">
                点击左侧菜单展开功能列表  |  所有操作需要管理员权限
            </div>
        </div>
    """)
    window.current_text_data = window.text_display_area.toPlainText()
    window.log.append(
        "WinNetTool 已就绪\n"
        "功能: 端口管理 / DHCP / Hosts / 系统服务 / Wi-Fi & 局域网 / 检查更新\n"
        "点击左侧菜单展开功能列表"
    )

import re
import os
import tempfile

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtCore import QUrl

import utils


def show_wifi_list(window):
    window._show_table_view()
    window.label_title.setText("周边 Wi-Fi 网络")
    window.search_box.setPlaceholderText("搜索 SSID / 认证方式 / 频道")
    window._setup_table(["SSID", "信号强度", "BSSID", "认证方式", "加密", "频道"])
    window._start_loading("正在扫描周边 Wi-Fi...")
    window.current_table_data = []

    def do():
        return window.wifi_manager.get_wifi_networks()

    def done(networks):
        window.current_table_data = networks
        window.table.setRowCount(len(networks))
        for i, n in enumerate(networks):
            signal_raw = n.get('signal', '')
            signal_bar = window.wifi_manager.get_signal_bar(signal_raw)
            window._set_row(i, [
                n.get('ssid', ''), signal_bar, n.get('bssid', ''),
                n.get('auth', ''), n.get('cipher', ''), n.get('channel', '')
            ])
            sig_item = window.table.item(i, 1)
            if sig_item:
                try:
                    pct_match = re.search(r'(\d+)%', signal_bar)
                    if pct_match:
                        pct = int(pct_match.group(1))
                        if pct >= 70:
                            sig_item.setForeground(QColor('#9ece6a'))
                        elif pct >= 40:
                            sig_item.setForeground(QColor('#e0af68'))
                        else:
                            sig_item.setForeground(QColor('#f7768e'))
                except Exception:
                    pass

        window._stop_loading(f"发现 {len(networks)} 个 Wi-Fi 网络")
        window.log.append(f"Wi-Fi 扫描完成，发现 {len(networks)} 个网络")

    window._run_worker(do, done)


def show_wifi_current(window):
    window._show_table_view()
    window.label_title.setText("当前 Wi-Fi 连接")
    window.search_box.setPlaceholderText("搜索...")
    window._setup_table(["属性", "值"])
    window._start_loading("正在获取当前 Wi-Fi 信息...")
    window.current_table_data = []

    def do():
        return window.wifi_manager.get_current_wifi()

    def done(info):
        label_map = {
            'ssid': 'SSID（网络名）',
            'bssid': 'BSSID（路由器 MAC）',
            'signal': '信号强度',
            'rx_rate': '接收速率',
            'tx_rate': '传输速率',
            'channel': '频道',
            'radio': '无线电类型',
            'auth': '认证方式'
        }
        rows = [(label_map.get(k, k), v) for k, v in info.items() if v]
        window.current_table_data = info
        window.table.setRowCount(len(rows))
        if not rows:
            window.table.setRowCount(1)
            window._set_row(0, ["状态", "未连接到任何 Wi-Fi 网络"])
        else:
            for i, (k, v) in enumerate(rows):
                if k == '信号强度':
                    v = window.wifi_manager.get_signal_bar(v)
                window._set_row(i, [k, v])

        window._stop_loading("当前 Wi-Fi 信息获取完成")
        window.log.append("当前 Wi-Fi 信息获取完成")

    window._run_worker(do, done)


def show_lan_devices(window):
    window._show_table_view()
    window.label_title.setText("局域网设备（ARP 表）")
    window.search_box.setPlaceholderText("搜索 IP / MAC / 主机名")
    window._setup_table(["IP 地址", "MAC 地址", "类型", "主机名"])
    window._start_loading("正在获取局域网设备...")
    window.current_table_data = []

    def do():
        return window.wifi_manager.get_lan_devices()

    def done(devices):
        window.current_table_data = devices
        window.table.setRowCount(len(devices))
        for i, d in enumerate(devices):
            window._set_row(i, [d.get('ip', ''), d.get('mac', ''), d.get('type', ''), d.get('hostname', '')])
        window._stop_loading(f"发现 {len(devices)} 台局域网设备")
        window.log.append(f"局域网设备获取完成，共 {len(devices)} 台")

    window._run_worker(do, done)


def show_lan_topology(window):
    window._show_text_view()
    window.label_title.setText("局域网拓扑图")
    window.search_box.setPlaceholderText("")
    window.text_display_area.setText("正在生成拓扑图，请稍候...")
    window._start_loading("正在生成局域网拓扑图...")
    window.current_text_data = ""

    def do():
        devices = window.wifi_manager.get_lan_devices()
        return utils.generate_lan_topology_html(devices)

    def done(html_content):
        # 保存 HTML 到临时文件并用浏览器打开
        try:
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, "wintool_topo.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            window.text_display_area.setText(
                f"拓扑图已生成并在浏览器中打开。\n\n"
                f"文件位置: {filepath}\n\n"
                f"共检测到的设备请参见左侧「局域网设备」列表。\n"
                f"拓扑图使用 SVG 渲染，支持缩放，无需安装额外工具。"
            )
            window.current_text_data = html_content
            window._stop_loading("拓扑图已打开")
            window.log.append("局域网拓扑图已生成并在浏览器中打开")
        except Exception as e:
            window.text_display_area.setText(f"生成拓扑图失败: {e}")
            window._stop_loading("生成失败")
            window.log.append(f"拓扑图生成失败: {e}")

    window._run_worker(do, done)

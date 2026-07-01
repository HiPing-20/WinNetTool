from PyQt6.QtWidgets import QMessageBox, QInputDialog

from ..dialogs import make_dialog


def show_local_ports(window):
    window._show_table_view()
    window.label_title.setText("本地端口查询")
    window.search_box.setPlaceholderText("🔍  搜索端口/程序名/PID")
    window._setup_table(["协议", "端口", "状态", "PID", "程序名"])
    window._start_loading("正在获取本地端口...")
    window.current_table_data = []

    def do():
        return window.manager.get_local_ports()

    def done(ports):
        window.current_table_data = ports
        window.table.setRowCount(len(ports))
        for i, p in enumerate(ports):
            window._set_row(i, [p['protocol'], str(p['port']), p['status'], p['pid'], p['name']])
        window._stop_loading(f"共 {len(ports)} 条端口信息")
        window.log.append(f"✅  本地端口获取完成，共 {len(ports)} 条")

    window._run_worker(do, done)


def show_firewall_rules(window):
    window._show_table_view()
    window.label_title.setText("防火墙入站规则")
    window.search_box.setPlaceholderText("🔍  搜索规则名/端口/状态")
    window._setup_table(["规则名", "端口", "已启用", "操作"])
    window._start_loading("正在获取防火墙规则...")
    window.current_table_data = []

    def do():
        return window.manager.get_firewall_rules()

    def done(rules):
        window.current_table_data = rules
        window.table.setRowCount(len(rules))
        for i, r in enumerate(rules):
            window._set_row(i, [r.get('name', ''), r.get('port', ''), r.get('enabled', ''), r.get('action', '')])
        window._stop_loading(f"共 {len(rules)} 条规则")
        window.log.append(f"✅  防火墙规则获取完成，共 {len(rules)} 条")

    window._run_worker(do, done)


def show_port_distribution(window):
    window._show_text_view()
    window.label_title.setText("本地端口使用分布图")
    window.search_box.setPlaceholderText("")
    window.text_display_area.setText("")
    window._start_loading("正在统计端口使用分布...")
    window.current_text_data = ""

    def do():
        from utils import generate_ascii_port_histogram
        port_data = window.manager.get_port_distribution_data()
        return generate_ascii_port_histogram(port_data)

    def done(chart_str):
        window.text_display_area.setText(chart_str)
        window.current_text_data = chart_str
        window._stop_loading("端口分布图生成完成")
        window.log.append("✅  端口使用分布图生成完成")

    window._run_worker(do, done)


def open_port_dialog(window):
    window._show_table_view()
    window.label_title.setText("开放端口")
    dialog_result = make_dialog(window, "开放端口", [("规则名:", ""), ("端口:", "")], window.styleSheet())
    if dialog_result is None:
        window.log.append("📋  开放端口操作已取消。")
        return

    name, port_text = dialog_result
    if not name or not port_text:
        QMessageBox.warning(window, "输入错误", "规则名和端口不能为空！")
        window.log.append("❌  开放端口失败: 规则名或端口为空。")
        return

    try:
        port = int(port_text)
    except ValueError:
        QMessageBox.warning(window, "输入错误", "端口号必须是数字！")
        window.log.append(f"❌  开放端口失败: 端口号 '{port_text}' 无效。")
        return

    window._start_loading(f"正在开放端口 {port} ({name})...")

    def do():
        window.manager.open_port(port, name)
        return True

    def done(success):
        window._stop_loading()
        window.log.append(f"✅  端口 {port} 已开放，规则名: {name}")
        QMessageBox.information(window, "成功", f"端口 {port} 已开放，规则名: {name}")
        window._dispatch("firewall_rules")

    def err(msg):
        window._stop_loading("操作失败")
        window.log.append(f"❌  开放端口失败: {msg}")
        QMessageBox.warning(window, "失败", f"开放端口失败: {msg}")

    window._run_worker(do, done, err)


def close_port_dialog(window):
    window._show_table_view()
    window.label_title.setText("关闭端口规则")
    text, ok = QInputDialog.getText(window, "关闭端口规则", "请输入要禁用的规则名（英文名）:")
    if ok and text:
        reply = QMessageBox.question(
            window, "确认操作",
            f"确定要禁用防火墙规则 '{text.strip()}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            window._start_loading(f"正在禁用端口规则 {text}...")

            def do():
                window.manager.close_port(text.strip())
                return True

            def done(success):
                window._stop_loading()
                window.log.append(f"✅  端口规则 {text} 已禁用")
                QMessageBox.information(window, "成功", f"端口规则 {text} 已禁用")
                window._dispatch("firewall_rules")

            def err(msg):
                window._stop_loading("操作失败")
                window.log.append(f"❌  禁用端口规则失败: {msg}")
                QMessageBox.warning(window, "失败", f"禁用端口规则失败: {msg}")

            window._run_worker(do, done, err)
        else:
            window.log.append("📋  禁用端口规则操作已取消。")
    else:
        window.log.append("📋  禁用端口规则操作已取消。")


def delete_port_dialog(window):
    window._show_table_view()
    window.label_title.setText("删除端口规则")
    text, ok = QInputDialog.getText(window, "删除端口规则", "请输入要删除的规则名（英文名）:")
    if ok and text:
        reply = QMessageBox.question(
            window, "确认操作",
            f"确定要删除防火墙规则 '{text.strip()}' 吗？\n删除后不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            window._start_loading(f"正在删除端口规则 {text}...")

            def do():
                window.manager.delete_port(text.strip())
                return True

            def done(success):
                window._stop_loading()
                window.log.append(f"✅  端口规则 {text} 已删除")
                QMessageBox.information(window, "成功", f"端口规则 {text} 已删除")
                window._dispatch("firewall_rules")

            def err(msg):
                window._stop_loading("操作失败")
                window.log.append(f"❌  删除端口规则失败: {msg}")
                QMessageBox.warning(window, "失败", f"删除端口规则失败: {msg}")

            window._run_worker(do, done, err)
        else:
            window.log.append("📋  删除端口规则操作已取消。")
    else:
        window.log.append("📋  删除端口规则操作已取消。")


def scan_lan_dialog(window):
    window._show_table_view()
    ip_range, ok = QInputDialog.getText(
        window, "局域网端口扫描",
        "请输入IP范围或单个IP（支持CIDR，逗号分隔）\n示例: 192.168.1.1-192.168.1.254, 192.168.1.10/24"
    )
    if ok and ip_range:
        window.label_title.setText("局域网端口扫描")
        window.search_box.setPlaceholderText("🔍  搜索IP/端口")
        window._setup_table(["IP", "端口", "状态"])
        window._start_loading("正在扫描局域网端口（可能较慢）...", indefinite=False)
        window.progress.setValue(0)
        window.btn_scan_lan_port.setEnabled(False)
        window.current_table_data = []

        def do(progress_callback):
            progress_callback(10, "正在初始化扫描...")
            results = window.scanner.scan_range(ip_range)
            progress_callback(100, "扫描完成")
            return results

        def done(results):
            window.current_table_data = results
            window.table.setRowCount(len(results))
            for i, r in enumerate(results):
                window._set_row(i, [r['ip'], str(r['port']), r['status']])
            window._stop_loading(f"扫描完成，共 {len(results)} 条记录")
            window.log.append(f"✅  扫描完成，共 {len(results)} 条")
            window.btn_scan_lan_port.setEnabled(True)

        def err(msg):
            window._stop_loading("扫描失败")
            window.log.append(f"❌  局域网端口扫描失败: {msg}")
            QMessageBox.warning(window, "扫描失败", f"局域网端口扫描失败: {msg}")
            window.btn_scan_lan_port.setEnabled(True)

        window._run_worker(do, done, err, progress_callback=window._update_progress)
    else:
        window.log.append("📋  局域网端口扫描操作已取消。")

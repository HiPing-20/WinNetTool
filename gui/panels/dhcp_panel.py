from PyQt6.QtWidgets import QMessageBox


def show_dhcp_info(window):
    window._show_table_view()
    window.label_title.setText("DHCP 信息")
    window.search_box.setPlaceholderText("🔍  搜索适配器/IP/DHCP服务器")
    window._setup_table(["适配器", "IP地址", "DHCP启用", "DHCP服务器", "状态"])
    window._start_loading("正在获取DHCP信息...")
    window.current_table_data = []

    def do():
        return window.dhcp_manager.get_dhcp_info()

    def done(info):
        window.current_table_data = info
        window.table.setRowCount(len(info))
        for i, r in enumerate(info):
            window._set_row(i, [
                r.get('name', ''), r.get('ip', ''), r.get('dhcp_enabled', ''),
                r.get('dhcp_server', ''), r.get('status', '')
            ])
        window._stop_loading("DHCP信息获取完成")
        window.log.append("✅  DHCP信息获取完成")

    window._run_worker(do, done)


def show_dhcp_server(window):
    window._show_table_view()
    window.label_title.setText("DHCP 服务器")
    window.search_box.setPlaceholderText("🔍  搜索DHCP服务器")
    window._setup_table(["服务器地址", "状态"])
    window._start_loading("正在获取DHCP服务器信息...")
    window.current_table_data = []

    def do():
        return window.dhcp_manager.get_dhcp_server_info()

    def done(servers):
        window.current_table_data = servers
        window.table.setRowCount(len(servers))
        for i, r in enumerate(servers):
            window._set_row(i, [r.get('server', ''), r.get('status', '')])
        window._stop_loading("DHCP服务器信息获取完成")
        window.log.append("✅  DHCP服务器信息获取完成")

    window._run_worker(do, done)


def release_ip(window):
    window._show_table_view()
    window.label_title.setText("释放IP地址")
    reply = QMessageBox.question(
        window, "确认操作", "确定要释放当前IP地址吗？\n此操作可能导致网络暂时中断！",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        window._start_loading("正在释放IP地址...")

        def do():
            return window.dhcp_manager.release_ip()

        def done(success):
            window._stop_loading()
            if success:
                window.log.append("✅  IP地址释放成功")
                QMessageBox.information(window, "成功", "IP地址已释放")
            else:
                window.log.append("❌  IP地址释放失败")
                QMessageBox.warning(window, "失败", "IP地址释放失败")
            window._dispatch("dhcp_info")

        window._run_worker(do, done)
    else:
        window.log.append("📋  释放IP地址操作已取消。")


def renew_ip(window):
    window._show_table_view()
    window.label_title.setText("续订IP地址")
    reply = QMessageBox.question(
        window, "确认操作", "确定要续订IP地址吗？\n此操作可能导致网络暂时中断！",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        window._start_loading("正在续订IP地址...")

        def do():
            return window.dhcp_manager.renew_ip()

        def done(success):
            window._stop_loading()
            if success:
                window.log.append("✅  IP地址续订成功")
                QMessageBox.information(window, "成功", "IP地址已续订")
            else:
                window.log.append("❌  IP地址续订失败")
                QMessageBox.warning(window, "失败", "IP地址续订失败")
            window._dispatch("dhcp_info")

        window._run_worker(do, done)
    else:
        window.log.append("📋  续订IP地址操作已取消。")

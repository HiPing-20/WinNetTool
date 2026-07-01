from PyQt6.QtWidgets import QMessageBox, QInputDialog

from ..dialogs import make_dialog


def show_host(window):
    window._show_table_view()
    window.label_title.setText("Hosts 管理")
    window.search_box.setPlaceholderText("🔍  搜索IP/域名")
    window._setup_table(["IP", "域名"])
    window._start_loading("正在获取Hosts信息...")
    window.current_table_data = []

    def do():
        return window.host_manager.get_hosts()

    def done(hosts):
        window.current_table_data = hosts
        window.table.setRowCount(len(hosts))
        for i, r in enumerate(hosts):
            window._set_row(i, [r.get('ip', ''), r.get('domain', '')])
        window._stop_loading(f"共 {len(hosts)} 条Host记录")
        window.log.append(f"✅  Hosts信息获取完成，共 {len(hosts)} 条")

    window._run_worker(do, done)


def add_host_dialog(window):
    window._show_table_view()
    window.label_title.setText("添加 Host 记录")
    result = make_dialog(window, "添加Host记录", [("IP地址:", ""), ("域名:", "")], window.styleSheet())
    if result is None:
        window.log.append("📋  添加Host记录操作已取消。")
        return

    ip, domain = result
    if not ip or not domain:
        QMessageBox.warning(window, "输入错误", "IP地址和域名不能为空！")
        window.log.append("❌  Host记录添加失败: IP地址或域名为空。")
        return

    window._start_loading(f"正在添加Host记录: {ip} → {domain}...")

    def do():
        return window.host_manager.add_host(ip, domain)

    def done(success_msg_tuple):
        window._stop_loading()
        success, msg = success_msg_tuple
        if success:
            window.log.append(f"✅  Host记录添加成功: {ip} → {domain}")
            QMessageBox.information(window, "成功", msg)
            show_host(window)
        else:
            window.log.append(f"❌  Host记录添加失败: {msg}")
            QMessageBox.warning(window, "失败", msg)

    window._run_worker(do, done)


def edit_host_dialog(window):
    window._show_table_view()
    window.label_title.setText("修改 Host 记录")
    domain, ok = QInputDialog.getText(window, "修改Host记录", "请输入要修改的域名:")
    if not ok or not domain:
        window.log.append("📋  修改Host记录操作已取消。")
        return

    domain = domain.strip()
    hosts = window.host_manager.get_hosts()
    current_host = next((h for h in hosts if h['domain'].lower() == domain.lower()), None)

    if not current_host:
        QMessageBox.warning(window, "域名不存在", f"域名 '{domain}' 不存在。")
        window.log.append(f"❌  修改Host记录失败: 域名 '{domain}' 不存在。")
        return

    result = make_dialog(
        window, f"修改Host - {domain}",
        [("新IP地址:", current_host['ip']), ("新域名:", current_host['domain'])],
        window.styleSheet()
    )
    if result is None:
        window.log.append("📋  修改Host记录操作已取消。")
        return

    new_ip, new_domain = result
    if not new_ip or not new_domain:
        QMessageBox.warning(window, "输入错误", "新IP地址和新域名不能为空！")
        window.log.append("❌  Host记录修改失败: 新IP地址或新域名为空。")
        return

    window._start_loading(f"正在修改Host记录: {domain} → {new_ip} {new_domain}...")

    def do():
        return window.host_manager.update_host(domain, new_ip, new_domain)

    def done(success_msg_tuple):
        window._stop_loading()
        success, msg = success_msg_tuple
        if success:
            window.log.append(f"✅  Host记录修改成功: {domain} → {new_ip} {new_domain}")
            QMessageBox.information(window, "成功", msg)
            show_host(window)
        else:
            window.log.append(f"❌  Host记录修改失败: {msg}")
            QMessageBox.warning(window, "失败", msg)

    window._run_worker(do, done)


def delete_host_dialog(window):
    window._show_table_view()
    window.label_title.setText("删除 Host 记录")
    domain, ok = QInputDialog.getText(window, "删除Host记录", "请输入要删除的域名:")
    if ok and domain:
        reply = QMessageBox.question(
            window, "确认删除",
            f"确定要删除域名 '{domain.strip()}' 的记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            window._start_loading(f"正在删除Host记录: {domain}...")

            def do():
                return window.host_manager.delete_host(domain.strip())

            def done(success_msg_tuple):
                window._stop_loading()
                success, msg = success_msg_tuple
                if success:
                    window.log.append(f"✅  Host记录删除成功: {domain}")
                    QMessageBox.information(window, "成功", msg)
                    show_host(window)
                else:
                    window.log.append(f"❌  Host记录删除失败: {msg}")
                    QMessageBox.warning(window, "失败", msg)

            window._run_worker(do, done)
        else:
            window.log.append("📋  删除Host记录操作已取消。")
    else:
        window.log.append("📋  删除Host记录操作已取消。")


def backup_hosts(window):
    window._show_table_view()
    window.label_title.setText("备份 Hosts 文件")
    reply = QMessageBox.question(
        window, "确认备份", "确定要备份 Hosts 文件吗？",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        window._start_loading("正在备份Hosts文件...")

        def do():
            return window.host_manager.backup_hosts()

        def done(success_msg_tuple):
            window._stop_loading()
            success, message = success_msg_tuple
            if success:
                window.log.append(f"✅  Hosts文件备份成功: {message}")
                QMessageBox.information(window, "成功", f"Hosts文件已备份到:\n{message}")
            else:
                window.log.append(f"❌  Hosts文件备份失败: {message}")
                QMessageBox.warning(window, "失败", f"备份失败: {message}")

        window._run_worker(do, done)
    else:
        window.log.append("📋  备份Hosts文件操作已取消。")

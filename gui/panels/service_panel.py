from PyQt6.QtWidgets import QMessageBox, QInputDialog
from PyQt6.QtGui import QColor


def show_service_list(window):
    window._show_table_view()
    window.label_title.setText("系统服务列表")
    window.search_box.setPlaceholderText("🔍  搜索服务名/显示名/状态")
    window._setup_table(["服务名", "显示名", "状态", "启动类型", "PID"])
    window._start_loading("正在获取系统服务列表...")
    window.current_table_data = []

    def do():
        return window.service_manager.get_services()

    def done(services):
        window.current_table_data = services
        window.table.setRowCount(len(services))
        status_colors = {
            'running': '#a6e3a1',
            'stopped': '#f38ba8',
            'paused': '#f9e2af',
            'start_pending': '#89b4fa',
            'stop_pending': '#fab387',
            'error': '#f38ba8',
        }
        for i, s in enumerate(services):
            window._set_row(i, [
                s.get('name', ''), s.get('display_name', ''),
                s.get('status', ''), s.get('start_type', ''), s.get('pid', '')
            ])
            status_item = window.table.item(i, 2)
            if status_item:
                color = status_colors.get(s.get('status', '').lower(), '#cdd6f4')
                status_item.setForeground(QColor(color))

        window._stop_loading(f"共 {len(services)} 个服务")
        window.log.append(f"✅  系统服务列表获取完成，共 {len(services)} 个")

    window._run_worker(do, done)


def service_start_dialog(window):
    window._show_table_view()
    window.label_title.setText("启动服务")
    name, ok = QInputDialog.getText(window, "启动服务", "请输入服务名（英文名）:")
    if ok and name:
        window._start_loading(f"正在启动服务 {name}...")

        def do():
            return window.service_manager.start_service(name.strip())

        def done(success_msg_tuple):
            window._stop_loading()
            success, msg = success_msg_tuple
            icon = "✅" if success else "❌"
            window.log.append(f"{icon}  {msg}")
            if success:
                QMessageBox.information(window, "成功", msg)
            else:
                QMessageBox.warning(window, "失败", msg)
            window._dispatch("service_list")

        window._run_worker(do, done)
    else:
        window.log.append("📋  启动服务操作已取消。")


def service_stop_dialog(window):
    window._show_table_view()
    window.label_title.setText("停止服务")
    name, ok = QInputDialog.getText(window, "停止服务", "请输入服务名（英文名）:")
    if ok and name:
        reply = QMessageBox.question(
            window, "确认操作",
            f"确定要停止服务 '{name.strip()}' 吗？\n停止关键服务可能影响系统稳定性！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            window._start_loading(f"正在停止服务 {name}...")

            def do():
                return window.service_manager.stop_service(name.strip())

            def done(success_msg_tuple):
                window._stop_loading()
                success, msg = success_msg_tuple
                icon = "✅" if success else "❌"
                window.log.append(f"{icon}  {msg}")
                if success:
                    QMessageBox.information(window, "成功", msg)
                else:
                    QMessageBox.warning(window, "失败", msg)
                window._dispatch("service_list")

            window._run_worker(do, done)
        else:
            window.log.append("📋  停止服务操作已取消。")
    else:
        window.log.append("📋  停止服务操作已取消。")


def service_restart_dialog(window):
    window._show_table_view()
    window.label_title.setText("重启服务")
    name, ok = QInputDialog.getText(window, "重启服务", "请输入服务名（英文名）:")
    if ok and name:
        reply = QMessageBox.question(
            window, "确认操作",
            f"确定要重启服务 '{name.strip()}' 吗？\n此操作会短暂停止服务！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            window._start_loading(f"正在重启服务 {name}...")

            def do():
                return window.service_manager.restart_service(name.strip())

            def done(success_msg_tuple):
                window._stop_loading()
                success, msg = success_msg_tuple
                icon = "✅" if success else "❌"
                window.log.append(f"{icon}  {msg}")
                if success:
                    QMessageBox.information(window, "成功", msg)
                else:
                    QMessageBox.warning(window, "失败", msg)
                window._dispatch("service_list")

            window._run_worker(do, done)
        else:
            window.log.append("📋  重启服务操作已取消。")
    else:
        window.log.append("📋  重启服务操作已取消。")


def show_service_log(window):
    window._show_table_view()
    window.label_title.setText("服务操作日志")
    window.search_box.setPlaceholderText("🔍  搜索服务/操作/结果")
    window._setup_table(["时间", "服务名", "操作", "结果"])
    window._start_loading("正在加载服务操作日志...")
    window.current_table_data = []

    def do():
        return window.service_manager.get_operation_logs()

    def done(logs):
        if not logs:
            window.log.append("📋  暂无操作记录，请先对服务执行启动/停止/重启操作")
            window._stop_loading("无操作日志")
            window.current_table_data = []
            window.table.setRowCount(0)
            return

        window.current_table_data = logs
        window.table.setRowCount(len(logs))
        for i, entry in enumerate(reversed(logs)):
            window._set_row(i, [entry['time'], entry['service'], entry['action'], entry['result']])
        window._stop_loading(f"共 {len(logs)} 条日志")
        window.log.append(f"✅  操作日志加载完成，共 {len(logs)} 条")

    window._run_worker(do, done)

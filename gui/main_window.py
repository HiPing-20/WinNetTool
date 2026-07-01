import sys
import os
import platform

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextEdit, QLineEdit,
    QMessageBox, QFrame, QProgressBar, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QDesktopServices, QFont

from network import (
    LocalPortManager, PortScanner, DHCPManager,
    HostManager, ServiceManager, WifiManager, VersionChecker
)
from gui.styles import DARK_STYLE
from gui.workers import WorkerThread
from gui import panels
from utils import get_resource_path


class MainWindow(QWidget):
    CURRENT_VERSION = "1.0.0"
    UPDATE_CHECK_URL = "https://api.github.com/repos/HiPing-20/WinNetTool/releases/latest"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"WinNetTool - 网络工具箱 v{self.CURRENT_VERSION}")

        # 图标：兼容 exe 和源码运行
        icon_path = get_resource_path('app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 自适应屏幕大小
        screen = self.screen()
        if screen:
            screen_geo = screen.availableGeometry()
            sw, sh = screen_geo.width(), screen_geo.height()
            # 窗口占屏幕 70% 宽度、75% 高度
            w = int(sw * 0.70)
            h = int(sh * 0.75)
            x = screen_geo.x() + (sw - w) // 2
            y = screen_geo.y() + (sh - h) // 2
            self.setGeometry(x, y, w, h)
        else:
            self.setGeometry(200, 100, 1100, 700)

        self.setMinimumSize(900, 550)
        self.setStyleSheet(DARK_STYLE)

        self.manager = LocalPortManager()
        self.dhcp_manager = DHCPManager()
        self.host_manager = HostManager()
        self.scanner = PortScanner()
        self.service_manager = ServiceManager()
        self.wifi_manager = WifiManager()
        self.version_checker = VersionChecker(self.CURRENT_VERSION, self.UPDATE_CHECK_URL)

        if not self.manager.is_admin():
            QMessageBox.critical(self, "管理员权限", "请使用管理员权限运行软件")
            sys.exit(1)

        self.current_feature = None
        self.active_main_btn = None
        self.active_sub_btn = None
        self._worker = None
        self.current_table_data = []
        self.current_text_data = ""

        self.port_expanded = False
        self.dhcp_expanded = False
        self.host_expanded = False
        self.service_expanded = False
        self.wifi_expanded = False
        self.update_expanded = False

        self._setup_ui()
        panels.show_welcome(self)
        panels.check_for_updates_on_startup(self)

    def _setup_ui(self):
        root = QHBoxLayout()
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)

        self._build_sidebar(root)
        self._build_content_area(root)
        self._bind_events()

    def _build_sidebar(self, root):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 12)
        sidebar_layout.setSpacing(0)
        root.addWidget(self.sidebar)

        # Logo 区域
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 20, 16, 8)
        logo_layout.setSpacing(2)

        app_title = QLabel("WinNetTool")
        app_title.setObjectName("app_title")
        logo_layout.addWidget(app_title)

        app_subtitle = QLabel("网络工具箱")
        app_subtitle.setStyleSheet("color: #565f89; font-size: 8pt; padding-left: 2px; background: transparent;")
        logo_layout.addWidget(app_subtitle)

        sidebar_layout.addWidget(logo_widget)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(sep)

        # 菜单分组标签
        def add_section_label(text, layout):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #565f89; font-size: 8pt; font-weight: bold; padding: 8px 20px 2px 20px; background: transparent; letter-spacing: 1px;")
            layout.addWidget(lbl)

        add_section_label("网络工具", sidebar_layout)

        self.btn_port_manage = self._make_main_btn("  端口管理")
        sidebar_layout.addWidget(self.btn_port_manage)
        self.btn_local_ports = self._make_sub_btn("本地端口查询")
        self.btn_firewall_rules = self._make_sub_btn("防火墙规则")
        self.btn_open_port = self._make_sub_btn("开放端口")
        self.btn_close_port = self._make_sub_btn("关闭端口")
        self.btn_delete_port = self._make_sub_btn("删除端口规则")
        self.btn_scan_lan_port = self._make_sub_btn("局域网端口扫描")
        self.btn_port_dist = self._make_sub_btn("端口分布图")
        self.port_sub_btns = [
            self.btn_local_ports, self.btn_firewall_rules,
            self.btn_open_port, self.btn_close_port,
            self.btn_delete_port, self.btn_scan_lan_port, self.btn_port_dist
        ]
        for b in self.port_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        self.btn_dhcp = self._make_main_btn("  DHCP 管理")
        sidebar_layout.addWidget(self.btn_dhcp)
        self.btn_dhcp_info = self._make_sub_btn("DHCP 信息")
        self.btn_dhcp_server = self._make_sub_btn("DHCP 服务器")
        self.btn_release_ip = self._make_sub_btn("释放 IP")
        self.btn_renew_ip = self._make_sub_btn("续订 IP")
        self.dhcp_sub_btns = [self.btn_dhcp_info, self.btn_dhcp_server, self.btn_release_ip, self.btn_renew_ip]
        for b in self.dhcp_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        self.btn_host = self._make_main_btn("  Hosts 管理")
        sidebar_layout.addWidget(self.btn_host)
        self.btn_view_hosts = self._make_sub_btn("查看 Hosts")
        self.btn_add_host = self._make_sub_btn("添加 Host")
        self.btn_edit_host = self._make_sub_btn("修改 Host")
        self.btn_delete_host = self._make_sub_btn("删除 Host")
        self.btn_backup_hosts = self._make_sub_btn("备份 Hosts")
        self.host_sub_btns = [
            self.btn_view_hosts, self.btn_add_host,
            self.btn_edit_host, self.btn_delete_host, self.btn_backup_hosts
        ]
        for b in self.host_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        add_section_label("系统工具", sidebar_layout)

        self.btn_service = self._make_main_btn("  系统服务")
        sidebar_layout.addWidget(self.btn_service)
        self.btn_service_list = self._make_sub_btn("服务列表")
        self.btn_service_start = self._make_sub_btn("启动服务")
        self.btn_service_stop = self._make_sub_btn("停止服务")
        self.btn_service_restart = self._make_sub_btn("重启服务")
        self.btn_service_log = self._make_sub_btn("操作日志")
        self.service_sub_btns = [
            self.btn_service_list, self.btn_service_start,
            self.btn_service_stop, self.btn_service_restart, self.btn_service_log
        ]
        for b in self.service_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        self.btn_wifi = self._make_main_btn("  Wi-Fi / 局域网")
        sidebar_layout.addWidget(self.btn_wifi)
        self.btn_wifi_list = self._make_sub_btn("周边 Wi-Fi")
        self.btn_wifi_current = self._make_sub_btn("当前连接")
        self.btn_lan_devices = self._make_sub_btn("局域网设备")
        self.btn_lan_topology = self._make_sub_btn("局域网拓扑图")
        self.wifi_sub_btns = [
            self.btn_wifi_list, self.btn_wifi_current,
            self.btn_lan_devices, self.btn_lan_topology
        ]
        for b in self.wifi_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        add_section_label("其他", sidebar_layout)

        self.btn_update = self._make_main_btn("  检查更新")
        sidebar_layout.addWidget(self.btn_update)
        self.btn_check_update_now = self._make_sub_btn("手动检查更新")
        self.update_sub_btns = [self.btn_check_update_now]
        for b in self.update_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        sidebar_layout.addStretch()

        # 底部版本信息
        version_label = QLabel(f"v{self.CURRENT_VERSION}")
        version_label.setStyleSheet("color: #3b4261; font-size: 8pt; padding: 4px 16px; background: transparent;")
        sidebar_layout.addWidget(version_label)

    def _build_content_area(self, root):
        self.content_widget = QWidget()
        content_root = QVBoxLayout(self.content_widget)
        content_root.setContentsMargins(0, 0, 0, 0)
        content_root.setSpacing(0)
        root.addWidget(self.content_widget, 1)

        # 顶部栏
        top_bar = QWidget()
        top_bar.setObjectName("top_bar")
        top_layout = QVBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 4, 16, 0)
        top_layout.setSpacing(0)

        self.label_title = QLabel()
        self.label_title.setObjectName("title_label")
        top_layout.addWidget(self.label_title)

        self.label_status = QLabel("")
        self.label_status.setObjectName("status_label")
        top_layout.addWidget(self.label_status)
        content_root.addWidget(top_bar)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(4)
        content_root.addWidget(self.progress)

        # 搜索和保存
        toolbar = QWidget()
        toolbar.setStyleSheet("background: transparent; margin: 4px 0;")
        self.search_and_save_layout = QHBoxLayout(toolbar)
        self.search_and_save_layout.setContentsMargins(16, 4, 16, 4)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索...")
        self.search_box.textChanged.connect(self._filter_table)
        self.search_and_save_layout.addWidget(self.search_box)

        self.btn_save_result = QPushButton("保存结果")
        self.btn_save_result.setObjectName("save_btn")
        self.btn_save_result.setFixedWidth(90)
        self.btn_save_result.clicked.connect(self._save_current_display_data)
        self.search_and_save_layout.addWidget(self.btn_save_result)
        content_root.addWidget(toolbar)

        # 主显示区
        self.main_display_area = QWidget()
        self.main_display_layout = QVBoxLayout(self.main_display_area)
        self.main_display_layout.setContentsMargins(0, 0, 0, 0)
        self.main_display_layout.setSpacing(0)
        content_root.addWidget(self.main_display_area, 1)

        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + "QTableWidget { alternate-background-color: #1a1b26; }")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.main_display_layout.addWidget(self.table)

        self.text_display_area = QTextEdit()
        self.text_display_area.setReadOnly(True)
        self.text_display_area.setObjectName("text_display_area")
        self.text_display_area.setVisible(False)
        self.main_display_layout.addWidget(self.text_display_area)

        # 底部日志区
        log_container = QWidget()
        log_container.setStyleSheet("background: transparent;")
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(8, 0, 8, 8)
        log_layout.setSpacing(0)

        log_header = QLabel("  运行日志")
        log_header.setStyleSheet("color: #565f89; font-size: 8pt; font-weight: bold; padding: 4px 8px; background: transparent;")
        log_layout.addWidget(log_header)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        self.log.setStyleSheet(self.log.styleSheet() + "font-size: 8pt;")
        log_layout.addWidget(self.log)
        content_root.addWidget(log_container)

    def _bind_events(self):
        self.btn_port_manage.clicked.connect(lambda: self._toggle_group('port', self.port_sub_btns, self.btn_port_manage))
        self.btn_dhcp.clicked.connect(lambda: self._toggle_group('dhcp', self.dhcp_sub_btns, self.btn_dhcp))
        self.btn_host.clicked.connect(lambda: self._toggle_group('host', self.host_sub_btns, self.btn_host))
        self.btn_service.clicked.connect(lambda: self._toggle_group('service', self.service_sub_btns, self.btn_service))
        self.btn_wifi.clicked.connect(lambda: self._toggle_group('wifi', self.wifi_sub_btns, self.btn_wifi))
        self.btn_update.clicked.connect(lambda: self._toggle_group('update', self.update_sub_btns, self.btn_update))

        self.btn_local_ports.clicked.connect(lambda: self._dispatch("local_ports"))
        self.btn_firewall_rules.clicked.connect(lambda: self._dispatch("firewall_rules"))
        self.btn_open_port.clicked.connect(lambda: self._dispatch("open_port"))
        self.btn_close_port.clicked.connect(lambda: self._dispatch("close_port"))
        self.btn_delete_port.clicked.connect(lambda: self._dispatch("delete_port"))
        self.btn_scan_lan_port.clicked.connect(lambda: self._dispatch("lan_scan"))
        self.btn_port_dist.clicked.connect(lambda: self._dispatch("port_distribution"))

        self.btn_dhcp_info.clicked.connect(lambda: self._dispatch("dhcp_info"))
        self.btn_dhcp_server.clicked.connect(lambda: self._dispatch("dhcp_server"))
        self.btn_release_ip.clicked.connect(lambda: self._dispatch("release_ip"))
        self.btn_renew_ip.clicked.connect(lambda: self._dispatch("renew_ip"))

        self.btn_view_hosts.clicked.connect(lambda: self._dispatch("view_hosts"))
        self.btn_add_host.clicked.connect(lambda: self._dispatch("add_host"))
        self.btn_edit_host.clicked.connect(lambda: self._dispatch("edit_host"))
        self.btn_delete_host.clicked.connect(lambda: self._dispatch("delete_host"))
        self.btn_backup_hosts.clicked.connect(lambda: self._dispatch("backup_hosts"))

        self.btn_service_list.clicked.connect(lambda: self._dispatch("service_list"))
        self.btn_service_start.clicked.connect(lambda: self._dispatch("service_start"))
        self.btn_service_stop.clicked.connect(lambda: self._dispatch("service_stop"))
        self.btn_service_restart.clicked.connect(lambda: self._dispatch("service_restart"))
        self.btn_service_log.clicked.connect(lambda: self._dispatch("service_log"))

        self.btn_wifi_list.clicked.connect(lambda: self._dispatch("wifi_list"))
        self.btn_wifi_current.clicked.connect(lambda: self._dispatch("wifi_current"))
        self.btn_lan_devices.clicked.connect(lambda: self._dispatch("lan_devices"))
        self.btn_lan_topology.clicked.connect(lambda: self._dispatch("lan_topology"))

        self.btn_check_update_now.clicked.connect(lambda: self._dispatch("check_update"))

    # ==================== Button factories ====================
    def _make_main_btn(self, text):
        btn = QPushButton(text)
        btn.setObjectName("main_btn")
        btn.setCheckable(False)
        return btn

    def _make_sub_btn(self, text):
        btn = QPushButton(text)
        btn.setObjectName("sub_btn")
        return btn

    # ==================== Sidebar toggle ====================
    def _toggle_group(self, group_name, sub_btns, main_btn):
        all_groups = {
            'port': (self.port_sub_btns, self.btn_port_manage, 'port_expanded'),
            'dhcp': (self.dhcp_sub_btns, self.btn_dhcp, 'dhcp_expanded'),
            'host': (self.host_sub_btns, self.btn_host, 'host_expanded'),
            'service': (self.service_sub_btns, self.btn_service, 'service_expanded'),
            'wifi': (self.wifi_sub_btns, self.btn_wifi, 'wifi_expanded'),
            'update': (self.update_sub_btns, self.btn_update, 'update_expanded'),
        }

        for name, (g_sub_btns, g_main_btn, g_expanded_attr) in all_groups.items():
            if name != group_name and getattr(self, g_expanded_attr):
                setattr(self, g_expanded_attr, False)
                for b in g_sub_btns:
                    b.setVisible(False)
                g_main_btn.setProperty("active", False)
                g_main_btn.style().unpolish(g_main_btn)
                g_main_btn.style().polish(g_main_btn)

        expanded_attr = f"{group_name}_expanded"
        current = getattr(self, expanded_attr)
        new_state = not current
        setattr(self, expanded_attr, new_state)
        for b in sub_btns:
            b.setVisible(new_state)

        self._set_main_active(main_btn if new_state else None)

        if new_state and sub_btns:
            sub_btns[0].click()

    # ==================== Active state ====================
    def _set_main_active(self, btn):
        all_main_btns = [
            self.btn_port_manage, self.btn_dhcp, self.btn_host,
            self.btn_service, self.btn_wifi, self.btn_update
        ]
        for b in all_main_btns:
            b.setProperty("active", b is btn)
            b.style().unpolish(b)
            b.style().polish(b)
        self.active_main_btn = btn

    def _set_sub_active(self, btn):
        all_sub = (
            self.port_sub_btns + self.dhcp_sub_btns + self.host_sub_btns
            + self.service_sub_btns + self.wifi_sub_btns + self.update_sub_btns
        )
        for b in all_sub:
            b.setProperty("active", b is btn)
            b.style().unpolish(b)
            b.style().polish(b)
        self.active_sub_btn = btn

    # ==================== Feature dispatch ====================
    def _dispatch(self, feature):
        btn_map = {
            "local_ports": self.btn_local_ports,
            "firewall_rules": self.btn_firewall_rules,
            "open_port": self.btn_open_port,
            "close_port": self.btn_close_port,
            "delete_port": self.btn_delete_port,
            "lan_scan": self.btn_scan_lan_port,
            "port_distribution": self.btn_port_dist,
            "dhcp_info": self.btn_dhcp_info,
            "dhcp_server": self.btn_dhcp_server,
            "release_ip": self.btn_release_ip,
            "renew_ip": self.btn_renew_ip,
            "view_hosts": self.btn_view_hosts,
            "add_host": self.btn_add_host,
            "edit_host": self.btn_edit_host,
            "delete_host": self.btn_delete_host,
            "backup_hosts": self.btn_backup_hosts,
            "service_list": self.btn_service_list,
            "service_start": self.btn_service_start,
            "service_stop": self.btn_service_stop,
            "service_restart": self.btn_service_restart,
            "service_log": self.btn_service_log,
            "wifi_list": self.btn_wifi_list,
            "wifi_current": self.btn_wifi_current,
            "lan_devices": self.btn_lan_devices,
            "lan_topology": self.btn_lan_topology,
            "check_update": self.btn_check_update_now,
        }
        self._set_sub_active(btn_map.get(feature))

        actions = {
            "local_ports": panels.show_local_ports,
            "firewall_rules": panels.show_firewall_rules,
            "open_port": panels.open_port_dialog,
            "close_port": panels.close_port_dialog,
            "delete_port": panels.delete_port_dialog,
            "lan_scan": panels.scan_lan_dialog,
            "port_distribution": panels.show_port_distribution,
            "dhcp_info": panels.show_dhcp_info,
            "dhcp_server": panels.show_dhcp_server,
            "release_ip": panels.release_ip,
            "renew_ip": panels.renew_ip,
            "view_hosts": panels.show_host,
            "add_host": panels.add_host_dialog,
            "edit_host": panels.edit_host_dialog,
            "delete_host": panels.delete_host_dialog,
            "backup_hosts": panels.backup_hosts,
            "service_list": panels.show_service_list,
            "service_start": panels.service_start_dialog,
            "service_stop": panels.service_stop_dialog,
            "service_restart": panels.service_restart_dialog,
            "service_log": panels.show_service_log,
            "wifi_list": panels.show_wifi_list,
            "wifi_current": panels.show_wifi_current,
            "lan_devices": panels.show_lan_devices,
            "lan_topology": panels.show_lan_topology,
            "check_update": panels.check_for_updates,
        }
        if feature in actions:
            actions[feature](self)

    # ==================== Progress ====================
    def _start_loading(self, msg="加载中...", indefinite=True):
        self.progress.setRange(0, 0) if indefinite else self.progress.setRange(0, 100)
        self.progress.setVisible(True)
        self.label_status.setText(msg)

    def _update_progress(self, value, msg=""):
        if self.progress.maximum() > 0:
            self.progress.setValue(value)
        if msg:
            self.label_status.setText(msg)

    def _stop_loading(self, msg="就绪"):
        self.progress.setVisible(False)
        self.label_status.setText(msg)

    # ==================== View switching ====================
    def _show_table_view(self):
        self.table.setVisible(True)
        self.text_display_area.setVisible(False)
        self.search_box.setVisible(True)
        self.btn_save_result.setVisible(True)

    def _show_text_view(self):
        self.table.setVisible(False)
        self.text_display_area.setVisible(True)
        self.search_box.setVisible(False)
        self.btn_save_result.setVisible(True)

    # ==================== Search ====================
    def _filter_table(self):
        if not self.table.isVisible() or not self.table.rowCount():
            return
        text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                (self.table.item(row, col) and text in self.table.item(row, col).text().lower())
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    # ==================== Save ====================
    def _save_current_display_data(self):
        import utils
        filename_prefix = self.label_title.text().replace(" ", "_").replace(":", "")

        if self.table.isVisible() and self.current_table_data:
            success, filepath = utils.save_data_to_temp_file(self.current_table_data, filename_prefix, "json")
            if success:
                self.log.append(f"表格数据已保存到临时文件: {filepath}")
                QMessageBox.information(self, "保存成功", f"当前表格数据已保存到:\n{filepath}")
                QDesktopServices.openUrl(filepath)
            else:
                self.log.append(f"表格数据保存失败: {filepath}")
                QMessageBox.warning(self, "保存失败", f"表格数据保存失败: {filepath}")
        elif self.text_display_area.isVisible() and self.current_text_data:
            success, filepath = utils.save_data_to_temp_file(self.current_text_data, filename_prefix, "txt")
            if success:
                self.log.append(f"文本数据已保存到临时文件: {filepath}")
                QMessageBox.information(self, "保存成功", f"当前文本数据已保存到:\n{filepath}")
                QDesktopServices.openUrl(filepath)
            else:
                self.log.append(f"文本数据保存失败: {filepath}")
                QMessageBox.warning(self, "保存失败", f"文本数据保存失败: {filepath}")
        else:
            self.log.append("当前无数据可保存或未选中任何功能。")
            QMessageBox.information(self, "提示", "当前无可保存的数据。")

    # ==================== Table helpers ====================
    def _setup_table(self, headers):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(0)

    def _set_row(self, row, values):
        for col, val in enumerate(values):
            item = QTableWidgetItem(str(val) if val is not None else '')
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, col, item)

    # ==================== Worker thread ====================
    def _run_worker(self, func, on_done, on_error=None, **kwargs):
        if self._worker and self._worker.isRunning():
            self.log.append("上一个任务正在运行中，请稍后再试。")
            QMessageBox.warning(self, "任务繁忙", "上一个任务正在运行中，请稍后再试。")
            return

        self._worker = WorkerThread(func, **kwargs)

        def _done(result):
            on_done(result)
            self._worker = None

        def _err(msg):
            self._stop_loading("发生错误")
            self.log.append(f"错误: {msg}")
            if on_error:
                on_error(msg)
            else:
                QMessageBox.warning(self, "错误", f"操作过程中发生错误:\n{msg}")
            self._worker = None

        self._worker.result_signal.connect(_done)
        self._worker.error_signal.connect(_err)
        if 'progress_callback' in kwargs:
            self._worker.progress_signal.connect(kwargs['progress_callback'])
        self._worker.start()

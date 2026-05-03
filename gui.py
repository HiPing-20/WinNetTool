import sys
import os
import re
import platform
import utils # 引入新的 utils 工具模块

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextEdit, QLineEdit,
    QInputDialog, QMessageBox, QDialog, QProgressBar, QHeaderView,
    QSizePolicy, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QDesktopServices, QIcon # 导入 QIcon
from network import PortScanner, LocalPortManager, DHCPManager, HostManager, ServiceManager, WifiManager, VersionChecker


# ==================== 工作线程（防止UI卡死） ====================
class WorkerThread(QThread):
    result_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)
    # 新增进度信号，用于显示更细致的扫描进度
    progress_signal = pyqtSignal(int, str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # 如果函数支持进度回调，则传递 progress_callback
            if 'progress_callback' in self.kwargs:
                result = self.func(*self.args, progress_callback=self.progress_signal.emit, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


# ==================== 主窗口 ====================
class MainWindow(QWidget):
    # ==================== 版本信息与更新URL ====================
    CURRENT_VERSION = "1.0.0" # 你的应用当前版本
    # 请修改为你的 GitHub 仓库 Releases API 地址
    # 例如: https://api.github.com/repos/你的GitHub用户/你的仓库名/releases/latest
    UPDATE_CHECK_URL = "https://api.github.com/repos/YourGitHubUser/WinNetTool/releases/latest"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"WinNetTool - 网络工具箱 v{self.CURRENT_VERSION}")
        self.setWindowIcon(QIcon('app_icon.ico')) # 设置窗口图标
        self.setGeometry(200, 100, 1280, 780)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                font-size: 10pt;
                color: #cdd6f4;
            }

            /* 侧边栏容器 */
            QWidget#sidebar {
                background-color: #181825;
                border-right: 1px solid #313244;
                min-width: 180px;
                max-width: 220px;
            }

            /* 主功能按钮 */
            QPushButton#main_btn {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                font-weight: bold;
                font-size: 10pt;
                text-align: left;
                margin: 3px 8px;
            }
            QPushButton#main_btn:hover {
                background-color: #45475a;
            }
            QPushButton#main_btn[active="true"] {
                background-color: #89b4fa;
                color: #1e1e2e;
            }

            /* 子功能按钮 */
            QPushButton#sub_btn {
                background-color: transparent;
                color: #a6adc8;
                border: none;
                border-radius: 6px;
                padding: 7px 10px 7px 26px;
                font-size: 9pt;
                text-align: left;
                margin: 1px 8px;
            }
            QPushButton#sub_btn:hover {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton#sub_btn[active="true"] {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
            }

            /* 标题 */
            QLabel#title_label {
                font-size: 15pt;
                font-weight: bold;
                color: #89b4fa;
                padding: 8px 12px 4px 12px;
                background: transparent;
            }

            /* 状态标签 */
            QLabel#status_label {
                color: #a6e3a1;
                font-size: 9pt;
                padding: 2px 12px;
                background: transparent;
            }

            /* 搜索框 */
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 7px 12px;
                color: #cdd6f4;
                font-size: 10pt;
                margin: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
                background-color: #363649;
            }

            /* 表格 */
            QTableWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                gridline-color: #313244;
                color: #cdd6f4;
                margin: 4px 8px;
            }
            QTableWidget::item {
                padding: 7px 10px;
                border-bottom: 1px solid #252535;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #89b4fa;
                padding: 8px 10px;
                border: none;
                border-right: 1px solid #45475a;
                font-weight: bold;
                font-size: 9pt;
            }

            /* 日志 */
            QTextEdit {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #a6e3a1; /* 默认绿色 */
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9pt;
                padding: 8px;
                margin: 4px 8px;
            }
            /* 用于显示更新信息的TextEdit */
            QTextEdit#update_info_text {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #cdd6f4; /* 正常文本颜色 */
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                font-size: 10pt;
                padding: 15px;
                margin: 4px 8px;
            }


            /* 进度条 */
            QProgressBar {
                background-color: #313244;
                border: none;
                border-radius: 4px;
                height: 6px;
                text-align: center;
                margin: 0 8px;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 4px;
            }

            /* 滚动条 */
            QScrollBar:vertical {
                background: #1e1e2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #89b4fa;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background: #1e1e2e;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #45475a;
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #89b4fa;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
            }


            /* 对话框 */
            QDialog {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 10px;
            }
            QMessageBox {
                background-color: #1e1e2e;
            }
            QInputDialog {
                background-color: #1e1e2e;
            }

            /* 对话框内按钮 */
            QPushButton#dialog_ok {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton#dialog_ok:hover {
                background-color: #b4befe;
            }
            QPushButton#dialog_cancel {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton#dialog_cancel:hover {
                background-color: #585b70;
            }

            /* 分割线 */
            QFrame#separator {
                background-color: #313244;
                max-height: 1px;
                margin: 6px 8px;
            }

            /* 应用标题 */
            QLabel#app_title {
                font-size: 13pt;
                font-weight: bold;
                color: #89b4fa;
                padding: 14px 12px 8px 12px;
                background: transparent;
                letter-spacing: 1px;
            }

            /* 保存按钮 */
            QPushButton#save_btn {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: normal;
                font-size: 9pt;
                margin: 4px 0px 4px 8px; /* 调整与搜索框的间距 */
            }
            QPushButton#save_btn:hover {
                background-color: #585b70;
            }
            
            /* 链接按钮，用于更新 */
            QPushButton#link_btn {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 10pt;
                margin-top: 15px;
            }
            QPushButton#link_btn:hover {
                background-color: #b4befe;
            }

        """)

        # 管理器
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

        # 状态
        self.current_feature = None
        self.active_main_btn = None
        self.active_sub_btn = None
        self._worker = None
        self.current_table_data = [] # 用于保存当前表格的数据，方便导出
        self.current_text_data = "" # 用于保存当前文本显示区的数据，方便导出

        # 子按钮展开状态
        self.port_expanded = False
        self.dhcp_expanded = False
        self.host_expanded = False
        self.service_expanded = False
        self.wifi_expanded = False
        self.update_expanded = False # 新增更新菜单的展开状态

        self.setup_ui()
        self.show_welcome()
        self.check_for_updates_on_startup() # 启动时自动检查更新

    # ==================== UI 构建 ====================
    def setup_ui(self):
        root = QHBoxLayout()
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)

        # ---------- 侧边栏 ----------
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 12)
        sidebar_layout.setSpacing(0)
        root.addWidget(self.sidebar)

        app_title = QLabel("⚙ WinNetTool")
        app_title.setObjectName("app_title")
        sidebar_layout.addWidget(app_title)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(sep)

        # 端口管理
        self.btn_port_manage = self._make_main_btn("🔌  端口管理")
        sidebar_layout.addWidget(self.btn_port_manage)
        self.btn_local_ports   = self._make_sub_btn("本地端口查询")
        self.btn_firewall_rules= self._make_sub_btn("防火墙规则")
        self.btn_open_port     = self._make_sub_btn("开放端口")
        self.btn_close_port    = self._make_sub_btn("关闭端口")
        self.btn_delete_port   = self._make_sub_btn("删除端口规则")
        self.btn_scan_lan_port = self._make_sub_btn("局域网端口扫描")
        self.btn_port_dist     = self._make_sub_btn("端口分布图") # 新增端口分布
        self.port_sub_btns = [self.btn_local_ports, self.btn_firewall_rules,
                              self.btn_open_port, self.btn_close_port,
                              self.btn_delete_port, self.btn_scan_lan_port,
                              self.btn_port_dist]
        for b in self.port_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        # DHCP管理
        self.btn_dhcp = self._make_main_btn("🌐  DHCP管理")
        sidebar_layout.addWidget(self.btn_dhcp)
        self.btn_dhcp_info   = self._make_sub_btn("DHCP信息")
        self.btn_dhcp_server = self._make_sub_btn("DHCP服务器")
        self.btn_release_ip  = self._make_sub_btn("释放IP")
        self.btn_renew_ip    = self._make_sub_btn("续订IP")
        self.dhcp_sub_btns = [self.btn_dhcp_info, self.btn_dhcp_server,
                              self.btn_release_ip, self.btn_renew_ip]
        for b in self.dhcp_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        # Hosts管理
        self.btn_host = self._make_main_btn("📝  Hosts管理")
        sidebar_layout.addWidget(self.btn_host)
        self.btn_view_hosts   = self._make_sub_btn("查看Hosts")
        self.btn_add_host     = self._make_sub_btn("添加Host")
        self.btn_edit_host    = self._make_sub_btn("修改Host")
        self.btn_delete_host  = self._make_sub_btn("删除Host")
        self.btn_backup_hosts = self._make_sub_btn("备份Hosts")
        self.host_sub_btns = [self.btn_view_hosts, self.btn_add_host,
                              self.btn_edit_host, self.btn_delete_host,
                              self.btn_backup_hosts]
        for b in self.host_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        # 系统服务（阶段三新增）
        self.btn_service = self._make_main_btn("🛠  系统服务")
        sidebar_layout.addWidget(self.btn_service)
        self.btn_service_list    = self._make_sub_btn("服务列表")
        self.btn_service_start   = self._make_sub_btn("启动服务")
        self.btn_service_stop    = self._make_sub_btn("停止服务")
        self.btn_service_restart = self._make_sub_btn("重启服务")
        self.btn_service_log     = self._make_sub_btn("操作日志")
        self.service_sub_btns = [self.btn_service_list, self.btn_service_start,
                                 self.btn_service_stop, self.btn_service_restart,
                                 self.btn_service_log]
        for b in self.service_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        # Wi-Fi / 局域网（阶段四新增）
        self.btn_wifi = self._make_main_btn("📶  Wi-Fi / 局域网")
        sidebar_layout.addWidget(self.btn_wifi)
        self.btn_wifi_list    = self._make_sub_btn("周边Wi-Fi")
        self.btn_wifi_current = self._make_sub_btn("当前连接")
        self.btn_lan_devices  = self._make_sub_btn("局域网设备")
        self.btn_lan_topology = self._make_sub_btn("局域网拓扑图") # 新增局域网拓扑图
        self.wifi_sub_btns = [self.btn_wifi_list, self.btn_wifi_current,
                              self.btn_lan_devices, self.btn_lan_topology]
        for b in self.wifi_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        # 检查更新（阶段七相关）
        self.btn_update = self._make_main_btn("✨  检查更新")
        sidebar_layout.addWidget(self.btn_update)
        self.btn_check_update_now = self._make_sub_btn("手动检查更新")
        self.update_sub_btns = [self.btn_check_update_now]
        for b in self.update_sub_btns:
            sidebar_layout.addWidget(b)
            b.setVisible(False)

        sidebar_layout.addStretch()

        # ---------- 右侧内容区 ----------
        self.content_widget = QWidget()
        content_root = QVBoxLayout(self.content_widget)
        content_root.setContentsMargins(0, 0, 0, 0)
        content_root.setSpacing(0)
        root.addWidget(self.content_widget, 1)

        # 顶部标题 + 状态
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        top_layout = QVBoxLayout(top_bar)
        top_layout.setContentsMargins(4, 0, 12, 0)
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
        self.progress.setRange(0, 0)  # 不定进度
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        content_root.addWidget(self.progress)

        # 搜索框 和 保存按钮
        self.search_and_save_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  搜索...")
        self.search_box.textChanged.connect(self.filter_table)
        self.search_and_save_layout.addWidget(self.search_box)

        self.btn_save_result = QPushButton("💾  保存结果")
        self.btn_save_result.setObjectName("save_btn")
        self.btn_save_result.setFixedWidth(100)
        self.btn_save_result.clicked.connect(self.save_current_display_data)
        self.search_and_save_layout.addWidget(self.btn_save_result)

        content_root.addLayout(self.search_and_save_layout)

        # 主要内容区：包含表格或文本显示区
        self.main_display_area = QWidget()
        self.main_display_layout = QVBoxLayout(self.main_display_area)
        self.main_display_layout.setContentsMargins(0,0,0,0)
        self.main_display_layout.setSpacing(0)
        content_root.addWidget(self.main_display_area, 1) # 占据主要空间

        # 表格
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() +
                                 "QTableWidget { alternate-background-color: #1e1e2e; }")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.main_display_layout.addWidget(self.table)

        # 文本显示区（用于拓扑图、端口分布图、更新信息等）
        self.text_display_area = QTextEdit()
        self.text_display_area.setReadOnly(True)
        self.text_display_area.setObjectName("text_display_area") # 可用于特定样式
        self.text_display_area.setVisible(False) # 默认隐藏
        self.main_display_layout.addWidget(self.text_display_area)

        # 底部日志
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        content_root.addWidget(self.log)

        # ---------- 绑定事件 ----------
        self.btn_port_manage.clicked.connect(lambda: self._toggle_group(
            'port', self.port_sub_btns, self.btn_port_manage))
        self.btn_dhcp.clicked.connect(lambda: self._toggle_group(
            'dhcp', self.dhcp_sub_btns, self.btn_dhcp))
        self.btn_host.clicked.connect(lambda: self._toggle_group(
            'host', self.host_sub_btns, self.btn_host))
        self.btn_service.clicked.connect(lambda: self._toggle_group(
            'service', self.service_sub_btns, self.btn_service))
        self.btn_wifi.clicked.connect(lambda: self._toggle_group(
            'wifi', self.wifi_sub_btns, self.btn_wifi))
        self.btn_update.clicked.connect(lambda: self._toggle_group(
            'update', self.update_sub_btns, self.btn_update))

        # 端口
        self.btn_local_ports.clicked.connect(lambda: self._dispatch("local_ports"))
        self.btn_firewall_rules.clicked.connect(lambda: self._dispatch("firewall_rules"))
        self.btn_open_port.clicked.connect(lambda: self._dispatch("open_port"))
        self.btn_close_port.clicked.connect(lambda: self._dispatch("close_port"))
        self.btn_delete_port.clicked.connect(lambda: self._dispatch("delete_port"))
        self.btn_scan_lan_port.clicked.connect(lambda: self._dispatch("lan_scan"))
        self.btn_port_dist.clicked.connect(lambda: self._dispatch("port_distribution")) # 绑定新功能
        # DHCP
        self.btn_dhcp_info.clicked.connect(lambda: self._dispatch("dhcp_info"))
        self.btn_dhcp_server.clicked.connect(lambda: self._dispatch("dhcp_server"))
        self.btn_release_ip.clicked.connect(lambda: self._dispatch("release_ip"))
        self.btn_renew_ip.clicked.connect(lambda: self._dispatch("renew_ip"))
        # Hosts
        self.btn_view_hosts.clicked.connect(lambda: self._dispatch("view_hosts"))
        self.btn_add_host.clicked.connect(lambda: self._dispatch("add_host"))
        self.btn_edit_host.clicked.connect(lambda: self._dispatch("edit_host"))
        self.btn_delete_host.clicked.connect(lambda: self._dispatch("delete_host"))
        self.btn_backup_hosts.clicked.connect(lambda: self._dispatch("backup_hosts"))
        # 服务
        self.btn_service_list.clicked.connect(lambda: self._dispatch("service_list"))
        self.btn_service_start.clicked.connect(lambda: self._dispatch("service_start"))
        self.btn_service_stop.clicked.connect(lambda: self._dispatch("service_stop"))
        self.btn_service_restart.clicked.connect(lambda: self._dispatch("service_restart"))
        self.btn_service_log.clicked.connect(lambda: self._dispatch("service_log"))
        # Wi-Fi
        self.btn_wifi_list.clicked.connect(lambda: self._dispatch("wifi_list"))
        self.btn_wifi_current.clicked.connect(lambda: self._dispatch("wifi_current"))
        self.btn_lan_devices.clicked.connect(lambda: self._dispatch("lan_devices"))
        self.btn_lan_topology.clicked.connect(lambda: self._dispatch("lan_topology")) # 绑定新功能
        # 更新
        self.btn_check_update_now.clicked.connect(lambda: self._dispatch("check_update"))


    # ==================== 按钮工厂 ====================
    def _make_main_btn(self, text):
        btn = QPushButton(text)
        btn.setObjectName("main_btn")
        btn.setCheckable(False)
        return btn

    def _make_sub_btn(self, text):
        btn = QPushButton("· " + text)
        btn.setObjectName("sub_btn")
        return btn

    # ==================== 折叠组 ====================
    def _toggle_group(self, group_name, sub_btns, main_btn):
        # 遍历所有组，关闭其他已展开的组
        all_groups = {
            'port': (self.port_sub_btns, self.btn_port_manage, 'port_expanded'),
            'dhcp': (self.dhcp_sub_btns, self.btn_dhcp, 'dhcp_expanded'),
            'host': (self.host_sub_btns, self.btn_host, 'host_expanded'),
            'service': (self.service_sub_btns, self.btn_service, 'service_expanded'),
            'wifi': (self.wifi_sub_btns, self.btn_wifi, 'wifi_expanded'),
            'update': (self.update_sub_btns, self.btn_update, 'update_expanded'),
        }

        for name, (g_sub_btns, g_main_btn, g_expanded_attr) in all_groups.items():
            if name != group_name and getattr(self, g_expanded_attr): # 如果不是当前组且已展开
                setattr(self, g_expanded_attr, False) # 关闭
                for b in g_sub_btns:
                    b.setVisible(False)
                g_main_btn.setProperty("active", False)
                g_main_btn.style().unpolish(g_main_btn)
                g_main_btn.style().polish(g_main_btn)

        # 切换当前组的展开状态
        expanded_attr = f"{group_name}_expanded"
        current = getattr(self, expanded_attr)
        new_state = not current
        setattr(self, expanded_attr, new_state)
        for b in sub_btns:
            b.setVisible(new_state)

        # 更新主按钮激活态
        self._set_main_active(main_btn if new_state else None)

        # 激活主按钮时，自动点击第一个子按钮（如果存在）
        if new_state and sub_btns:
            sub_btns[0].click()

    # ==================== 高亮管理 ====================
    def _set_main_active(self, btn):
        all_main_btns = [self.btn_port_manage, self.btn_dhcp, self.btn_host,
                         self.btn_service, self.btn_wifi, self.btn_update]
        for b in all_main_btns:
            b.setProperty("active", b is btn)
            b.style().unpolish(b)
            b.style().polish(b)
        self.active_main_btn = btn

    def _set_sub_active(self, btn):
        all_sub = (self.port_sub_btns + self.dhcp_sub_btns + self.host_sub_btns
                   + self.service_sub_btns + self.wifi_sub_btns + self.update_sub_btns)
        for b in all_sub:
            b.setProperty("active", b is btn)
            b.style().unpolish(b)
            b.style().polish(b)
        self.active_sub_btn = btn

    # ==================== 功能路由 ====================
    def _dispatch(self, feature):
        btn_map = {
            "local_ports":    self.btn_local_ports,
            "firewall_rules": self.btn_firewall_rules,
            "open_port":      self.btn_open_port,
            "close_port":     self.btn_close_port,
            "delete_port":    self.btn_delete_port,
            "lan_scan":       self.btn_scan_lan_port,
            "port_distribution": self.btn_port_dist, # 新增
            "dhcp_info":      self.btn_dhcp_info,
            "dhcp_server":    self.btn_dhcp_server,
            "release_ip":     self.btn_release_ip,
            "renew_ip":       self.btn_renew_ip,
            "view_hosts":     self.btn_view_hosts,
            "add_host":       self.btn_add_host,
            "edit_host":      self.btn_edit_host,
            "delete_host":    self.btn_delete_host,
            "backup_hosts":   self.btn_backup_hosts,
            "service_list":   self.btn_service_list,
            "service_start":  self.btn_service_start,
            "service_stop":   self.btn_service_stop,
            "service_restart":self.btn_service_restart,
            "service_log":    self.btn_service_log,
            "wifi_list":      self.btn_wifi_list,
            "wifi_current":   self.btn_wifi_current,
            "lan_devices":    self.btn_lan_devices,
            "lan_topology":   self.btn_lan_topology, # 新增
            "check_update":   self.btn_check_update_now, # 新增
        }
        self._set_sub_active(btn_map.get(feature))

        actions = {
            "local_ports":    self.show_local_ports,
            "firewall_rules": self.show_firewall_rules,
            "open_port":      self.open_port_dialog,
            "close_port":     self.close_port_dialog,
            "delete_port":    self.delete_port_dialog,
            "lan_scan":       self.scan_lan_dialog,
            "port_distribution": self.show_port_distribution, # 新增
            "dhcp_info":      self.show_dhcp_info,
            "dhcp_server":    self.show_dhcp_server,
            "release_ip":     self.release_ip,
            "renew_ip":       self.renew_ip,
            "view_hosts":     self.show_host,
            "add_host":       self.add_host_dialog,
            "edit_host":      self.edit_host_dialog,
            "delete_host":    self.delete_host_dialog,
            "backup_hosts":   self.backup_hosts,
            "service_list":   self.show_service_list,
            "service_start":  self.service_start_dialog,
            "service_stop":   self.service_stop_dialog,
            "service_restart":self.service_restart_dialog,
            "service_log":    self.show_service_log,
            "wifi_list":      self.show_wifi_list,
            "wifi_current":   self.show_wifi_current,
            "lan_devices":    self.show_lan_devices,
            "lan_topology":   self.show_lan_topology, # 新增
            "check_update":   self.check_for_updates, # 新增
        }
        if feature in actions:
            actions[feature]()

    # ==================== 进度条控制 ====================
    def _start_loading(self, msg="加载中...", indefinite=True):
        self.progress.setRange(0, 0) if indefinite else self.progress.setRange(0, 100)
        self.progress.setVisible(True)
        self.label_status.setText(msg)

    def _update_progress(self, value, msg=""):
        if self.progress.maximum() > 0: # 如果不是不定进度
            self.progress.setValue(value)
        if msg:
            self.label_status.setText(msg)

    def _stop_loading(self, msg="就绪"):
        self.progress.setVisible(False)
        self.label_status.setText(msg)

    # ==================== 显示内容区切换 ====================
    def _show_table_view(self):
        self.table.setVisible(True)
        self.text_display_area.setVisible(False)
        self.search_box.setVisible(True)
        self.btn_save_result.setVisible(True) # 表格数据通常可保存

    def _show_text_view(self):
        self.table.setVisible(False)
        self.text_display_area.setVisible(True)
        self.search_box.setVisible(False) # 文本视图通常不需要搜索框
        self.btn_save_result.setVisible(True) # 文本内容也可以保存

    # ==================== 搜索过滤 ====================
    def filter_table(self):
        if not self.table.isVisible() or not self.table.rowCount():
            return
        text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                (self.table.item(row, col) and text in self.table.item(row, col).text().lower())
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    # ==================== 保存当前显示数据 ====================
    def save_current_display_data(self):
        filename_prefix = self.label_title.text().replace(" ", "_").replace(":", "")

        if self.table.isVisible() and self.current_table_data:
            success, filepath = utils.save_data_to_temp_file(self.current_table_data, filename_prefix, "json")
            if success:
                self.log.append(f"✅  表格数据已保存到临时文件: {filepath}")
                QMessageBox.information(self, "保存成功", f"当前表格数据已保存到:\n{filepath}")
                QDesktopServices.openUrl(filepath) # 尝试打开文件或所在目录
            else:
                self.log.append(f"❌  表格数据保存失败: {filepath}")
                QMessageBox.warning(self, "保存失败", f"表格数据保存失败: {filepath}")
        elif self.text_display_area.isVisible() and self.current_text_data:
            success, filepath = utils.save_data_to_temp_file(self.current_text_data, filename_prefix, "txt")
            if success:
                self.log.append(f"✅  文本数据已保存到临时文件: {filepath}")
                QMessageBox.information(self, "保存成功", f"当前文本数据已保存到:\n{filepath}")
                QDesktopServices.openUrl(filepath) # 尝试打开文件或所在目录
            else:
                self.log.append(f"❌  文本数据保存失败: {filepath}")
                QMessageBox.warning(self, "保存失败", f"文本数据保存失败: {filepath}")
        else:
            self.log.append("📋  当前无数据可保存或未选中任何功能。")
            QMessageBox.information(self, "提示", "当前无可保存的数据。")


    # ==================== 欢迎页 ====================
    def show_welcome(self):
        self._show_text_view() # 欢迎页显示文本
        self.text_display_area.setText("") # 清空旧数据
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        self.label_title.setText("欢迎使用 WinNetTool")
        self.label_status.setText(f"版本: v{self.CURRENT_VERSION} | 系统: {platform.system()} {platform.release()}")
        self.search_box.setPlaceholderText("🔍  搜索...")

        self.text_display_area.setHtml(
            """
            <div style="padding: 20px; font-size: 11pt; color: #cdd6f4;">
                <h2 style="color: #89b4fa; font-size: 18pt;">✅ WinNetTool 已就绪</h2>
                <p>📌 功能包含：端口管理 / DHCP / Hosts / 系统服务 / Wi-Fi & 局域网 / 检查更新</p>
                <p>💡 点击左侧菜单展开功能列表</p>
                <br>
                <p style="font-size: 9pt; color: #a6adc8;">
                    <b>当前版本:</b> <span style="color: #a6e3a1;">v{}</span><br>
                    <b>运行系统:</b> {} {}<br>
                    <b>Python:</b> {}
                </p>
            </div>
            """.format(self.CURRENT_VERSION, platform.system(), platform.release(), sys.version.split(' ')[0])
        )
        self.current_text_data = self.text_display_area.toPlainText() # 保存文本内容到变量
        self.log.append(
            "✅  WinNetTool 已就绪\n"
            "📌  功能包含：端口管理 / DHCP / Hosts / 系统服务 / Wi-Fi & 局域网 / 检查更新\n"
            "💡  点击左侧菜单展开功能列表"
        )


    # ==================== 本地端口 ====================
    def show_local_ports(self):
        self._show_table_view()
        self.label_title.setText("本地端口查询")
        self.search_box.setPlaceholderText("🔍  搜索端口/程序名/PID")
        self._setup_table(["协议", "端口", "状态", "PID", "程序名"])
        self._start_loading("正在获取本地端口...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.manager.get_local_ports()

        def done(ports):
            self.current_table_data = ports # 保存原始数据
            self.table.setRowCount(len(ports))
            for i, p in enumerate(ports):
                self._set_row(i, [p['protocol'], str(p['port']), p['status'], p['pid'], p['name']])
            self._stop_loading(f"共 {len(ports)} 条端口信息")
            self.log.append(f"✅  本地端口获取完成，共 {len(ports)} 条")

        self._run_worker(do, done)

    # ==================== 防火墙规则 ====================
    def show_firewall_rules(self):
        self._show_table_view()
        self.label_title.setText("防火墙入站规则")
        self.search_box.setPlaceholderText("🔍  搜索规则名/端口/状态")
        self._setup_table(["规则名", "端口", "已启用", "操作"])
        self._start_loading("正在获取防火墙规则...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.manager.get_firewall_rules()

        def done(rules):
            self.current_table_data = rules # 保存原始数据
            self.table.setRowCount(len(rules))
            for i, r in enumerate(rules):
                self._set_row(i, [r.get('name',''), r.get('port',''), r.get('enabled',''), r.get('action','')])
            self._stop_loading(f"共 {len(rules)} 条规则")
            self.log.append(f"✅  防火墙规则获取完成，共 {len(rules)} 条")

        self._run_worker(do, done)

    # ==================== 端口分布图（新增） ====================
    def show_port_distribution(self):
        self._show_text_view()
        self.label_title.setText("本地端口使用分布图")
        self.search_box.setPlaceholderText("") # 文本视图不显示搜索框
        self.text_display_area.setText("") # 清空旧数据
        self._start_loading("正在统计端口使用分布...")
        self.current_text_data = "" # 清空旧数据

        def do():
            # 获取原始端口连接，然后计数
            port_data = self.manager.get_port_distribution_data()
            return utils.generate_ascii_port_histogram(port_data)

        def done(chart_str):
            self.text_display_area.setText(chart_str)
            self.current_text_data = chart_str # 保存文本内容到变量
            self._stop_loading("端口分布图生成完成")
            self.log.append("✅  端口使用分布图生成完成")

        self._run_worker(do, done)

    # ==================== 端口操作 ====================
    def open_port_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("开放端口")
        dialog_result = self._make_dialog("开放端口", [("规则名:", ""), ("端口:", "")])
        if dialog_result is None:
            self.log.append("📋  开放端口操作已取消。")
            return

        name, port_text = dialog_result
        if not name or not port_text:
            QMessageBox.warning(self, "输入错误", "规则名和端口不能为空！")
            self.log.append("❌  开放端口失败: 规则名或端口为空。")
            return

        try:
            port = int(port_text)
            self._start_loading(f"正在开放端口 {port} ({name})...")

            def do():
                self.manager.open_port(port, name)
                return True

            def done(success):
                self._stop_loading()
                if success:
                    self.log.append(f"✅  端口 {port} 已开放，规则名: {name}")
                    QMessageBox.information(self, "成功", f"端口 {port} 已开放，规则名: {name}")
                self._dispatch("firewall_rules") # 刷新防火墙规则列表

            def err(msg):
                self._stop_loading("操作失败")
                self.log.append(f"❌  开放端口失败: {msg}")
                QMessageBox.warning(self, "失败", f"开放端口失败: {msg}")

            self._run_worker(do, done, err)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "端口号必须是数字！")
            self.log.append(f"❌  开放端口失败: 端口号 '{port_text}' 无效。")
        except Exception as e:
            self.log.append(f"❌  开放端口失败: {e}")
            QMessageBox.warning(self, "失败", f"开放端口失败: {e}")


    def close_port_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("关闭端口规则")
        text, ok = QInputDialog.getText(self, "关闭端口规则", "请输入要禁用的规则名（英文名）:")
        if ok and text:
            reply = QMessageBox.question(self, "确认操作", f"确定要禁用防火墙规则 '{text.strip()}' 吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._start_loading(f"正在禁用端口规则 {text}...")

                def do():
                    self.manager.close_port(text.strip())
                    return True

                def done(success):
                    self._stop_loading()
                    if success:
                        self.log.append(f"✅  端口规则 {text} 已禁用")
                        QMessageBox.information(self, "成功", f"端口规则 {text} 已禁用")
                    self._dispatch("firewall_rules") # 刷新防火墙规则列表

                def err(msg):
                    self._stop_loading("操作失败")
                    self.log.append(f"❌  禁用端口规则失败: {msg}")
                    QMessageBox.warning(self, "失败", f"禁用端口规则失败: {msg}")

                self._run_worker(do, done, err)
            else:
                self.log.append("📋  禁用端口规则操作已取消。")
        else:
            self.log.append("📋  禁用端口规则操作已取消。")


    def delete_port_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("删除端口规则")
        text, ok = QInputDialog.getText(self, "删除端口规则", "请输入要删除的规则名（英文名）:")
        if ok and text:
            reply = QMessageBox.question(self, "确认操作", f"确定要删除防火墙规则 '{text.strip()}' 吗？\n删除后不可恢复！",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No) # 默认不删除
            if reply == QMessageBox.StandardButton.Yes:
                self._start_loading(f"正在删除端口规则 {text}...")

                def do():
                    self.manager.delete_port(text.strip())
                    return True

                def done(success):
                    self._stop_loading()
                    if success:
                        self.log.append(f"✅  端口规则 {text} 已删除")
                        QMessageBox.information(self, "成功", f"端口规则 {text} 已删除")
                    self._dispatch("firewall_rules") # 刷新防火墙规则列表

                def err(msg):
                    self._stop_loading("操作失败")
                    self.log.append(f"❌  删除端口规则失败: {msg}")
                    QMessageBox.warning(self, "失败", f"删除端口规则失败: {msg}")

                self._run_worker(do, done, err)
            else:
                self.log.append("📋  删除端口规则操作已取消。")
        else:
            self.log.append("📋  删除端口规则操作已取消。")


    # ==================== 局域网端口扫描 ====================
    def scan_lan_dialog(self):
        self._show_table_view()
        ip_range, ok = QInputDialog.getText(self, "局域网端口扫描",
                                            "请输入IP范围或单个IP（支持CIDR，逗号分隔）\n示例: 192.168.1.1-192.168.1.254, 192.168.1.10/24")
        if ok and ip_range:
            self.label_title.setText("局域网端口扫描")
            self.search_box.setPlaceholderText("🔍  搜索IP/端口")
            self._setup_table(["IP", "端口", "状态"])
            self._start_loading("正在扫描局域网端口（可能较慢）...", indefinite=False) # 设为有进度
            self.progress.setValue(0)
            self.btn_scan_lan_port.setEnabled(False)
            self.current_table_data = [] # 清空旧数据

            def do(progress_callback):
                # 扫描器现在接受 progress_callback
                # 这里为了简化，Nmap 库本身没有直接的进度回调，
                # 如果要实现精确进度，需要对 Nmap 模块进行包装或替换底层实现
                # 暂时用一个简单的模拟进度
                progress_callback(10, "正在初始化扫描...")
                results = self.scanner.scan_range(ip_range)
                progress_callback(100, "扫描完成")
                return results

            def done(results):
                self.current_table_data = results # 保存原始数据
                self.table.setRowCount(len(results))
                for i, r in enumerate(results):
                    self._set_row(i, [r['ip'], str(r['port']), r['status']])
                self._stop_loading(f"扫描完成，共 {len(results)} 条记录")
                self.log.append(f"✅  扫描完成，共 {len(results)} 条")
                self.btn_scan_lan_port.setEnabled(True)

            def err(msg):
                self._stop_loading("扫描失败")
                self.log.append(f"❌  局域网端口扫描失败: {msg}")
                QMessageBox.warning(self, "扫描失败", f"局域网端口扫描失败: {msg}")
                self.btn_scan_lan_port.setEnabled(True)

            self._run_worker(do, done, err, progress_callback=self._update_progress)
        else:
            self.log.append("📋  局域网端口扫描操作已取消。")


    # ==================== DHCP ====================
    def show_dhcp_info(self):
        self._show_table_view()
        self.label_title.setText("DHCP 信息")
        self.search_box.setPlaceholderText("🔍  搜索适配器/IP/DHCP服务器")
        self._setup_table(["适配器", "IP地址", "DHCP启用", "DHCP服务器", "状态"])
        self._start_loading("正在获取DHCP信息...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.dhcp_manager.get_dhcp_info()

        def done(info):
            self.current_table_data = info # 保存原始数据
            self.table.setRowCount(len(info))
            for i, r in enumerate(info):
                self._set_row(i, [r.get('name',''), r.get('ip',''), r.get('dhcp_enabled',''), r.get('dhcp_server',''), r.get('status','')])
            self._stop_loading("DHCP信息获取完成")
            self.log.append("✅  DHCP信息获取完成")

        self._run_worker(do, done)

    def show_dhcp_server(self):
        self._show_table_view()
        self.label_title.setText("DHCP 服务器")
        self.search_box.setPlaceholderText("🔍  搜索DHCP服务器")
        self._setup_table(["服务器地址", "状态"])
        self._start_loading("正在获取DHCP服务器信息...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.dhcp_manager.get_dhcp_server_info()

        def done(servers):
            self.current_table_data = servers # 保存原始数据
            self.table.setRowCount(len(servers))
            for i, r in enumerate(servers):
                self._set_row(i, [r.get('server',''), r.get('status','')])
            self._stop_loading("DHCP服务器信息获取完成")
            self.log.append("✅  DHCP服务器信息获取完成")

        self._run_worker(do, done)

    def release_ip(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("释放IP地址")
        reply = QMessageBox.question(self, "确认操作", "确定要释放当前IP地址吗？\n此操作可能导致网络暂时中断！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No) # 默认不释放
        if reply == QMessageBox.StandardButton.Yes:
            self._start_loading("正在释放IP地址...")

            def do():
                return self.dhcp_manager.release_ip()

            def done(success):
                self._stop_loading()
                if success:
                    self.log.append("✅  IP地址释放成功")
                    QMessageBox.information(self, "成功", "IP地址已释放")
                else:
                    self.log.append("❌  IP地址释放失败")
                    QMessageBox.warning(self, "失败", "IP地址释放失败")
                self._dispatch("dhcp_info") # 刷新DHCP信息

            self._run_worker(do, done)
        else:
            self.log.append("📋  释放IP地址操作已取消。")


    def renew_ip(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("续订IP地址")
        reply = QMessageBox.question(self, "确认操作", "确定要续订IP地址吗？\n此操作可能导致网络暂时中断！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No) # 默认不续订
        if reply == QMessageBox.StandardButton.Yes:
            self._start_loading("正在续订IP地址...")

            def do():
                return self.dhcp_manager.renew_ip()

            def done(success):
                self._stop_loading()
                if success:
                    self.log.append("✅  IP地址续订成功")
                    QMessageBox.information(self, "成功", "IP地址已续订")
                else:
                    self.log.append("❌  IP地址续订失败")
                    QMessageBox.warning(self, "失败", "IP地址续订失败")
                self._dispatch("dhcp_info") # 刷新DHCP信息

            self._run_worker(do, done)
        else:
            self.log.append("📋  续订IP地址操作已取消。")


    # ==================== Hosts ====================
    def show_host(self):
        self._show_table_view()
        self.label_title.setText("Hosts 管理")
        self.search_box.setPlaceholderText("🔍  搜索IP/域名")
        self._setup_table(["IP", "域名"])
        self._start_loading("正在获取Hosts信息...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.host_manager.get_hosts()

        def done(hosts):
            self.current_table_data = hosts # 保存原始数据
            self.table.setRowCount(len(hosts))
            for i, r in enumerate(hosts):
                self._set_row(i, [r.get('ip',''), r.get('domain','')])
            self._stop_loading(f"共 {len(hosts)} 条Host记录")
            self.log.append(f"✅  Hosts信息获取完成，共 {len(hosts)} 条")

        self._run_worker(do, done)

    def add_host_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("添加 Host 记录")
        result = self._make_dialog("添加Host记录", [("IP地址:", ""), ("域名:", "")])
        if result:
            ip, domain = result
            if not ip or not domain:
                QMessageBox.warning(self, "输入错误", "IP地址和域名不能为空！")
                self.log.append("❌  Host记录添加失败: IP地址或域名为空。")
                return

            self._start_loading(f"正在添加Host记录: {ip} → {domain}...")

            def do():
                return self.host_manager.add_host(ip, domain)

            def done(success_msg_tuple):
                self._stop_loading()
                success, msg = success_msg_tuple
                if success:
                    self.log.append(f"✅  Host记录添加成功: {ip} → {domain}")
                    QMessageBox.information(self, "成功", msg)
                    self.show_host() # 刷新列表
                else:
                    self.log.append(f"❌  Host记录添加失败: {msg}")
                    QMessageBox.warning(self, "失败", msg)

            self._run_worker(do, done)
        else:
            self.log.append("📋  添加Host记录操作已取消。")


    def edit_host_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("修改 Host 记录")
        domain, ok = QInputDialog.getText(self, "修改Host记录", "请输入要修改的域名:")
        if not ok or not domain:
            self.log.append("📋  修改Host记录操作已取消。")
            return

        domain = domain.strip()
        hosts = self.host_manager.get_hosts()
        current_host = next((h for h in hosts if h['domain'].lower() == domain.lower()), None)

        if not current_host:
            QMessageBox.warning(self, "域名不存在", f"域名 '{domain}' 不存在。")
            self.log.append(f"❌  修改Host记录失败: 域名 '{domain}' 不存在。")
            return

        result = self._make_dialog(f"修改Host - {domain}", [("新IP地址:", current_host['ip']), ("新域名:", current_host['domain'])])
        if result:
            new_ip, new_domain = result
            if not new_ip or not new_domain:
                QMessageBox.warning(self, "输入错误", "新IP地址和新域名不能为空！")
                self.log.append("❌  Host记录修改失败: 新IP地址或新域名为空。")
                return

            self._start_loading(f"正在修改Host记录: {domain} → {new_ip} {new_domain}...")

            def do():
                return self.host_manager.update_host(domain, new_ip, new_domain)

            def done(success_msg_tuple):
                self._stop_loading()
                success, msg = success_msg_tuple
                if success:
                    self.log.append(f"✅  Host记录修改成功: {domain} → {new_ip} {new_domain}")
                    QMessageBox.information(self, "成功", msg)
                    self.show_host() # 刷新列表
                else:
                    self.log.append(f"❌  Host记录修改失败: {msg}")
                    QMessageBox.warning(self, "失败", msg)

            self._run_worker(do, done)
        else:
            self.log.append("📋  修改Host记录操作已取消。")


    def delete_host_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("删除 Host 记录")
        domain, ok = QInputDialog.getText(self, "删除Host记录", "请输入要删除的域名:")
        if ok and domain:
            reply = QMessageBox.question(self, "确认删除", f"确定要删除域名 '{domain.strip()}' 的记录吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No) # 默认不删除
            if reply == QMessageBox.StandardButton.Yes:
                self._start_loading(f"正在删除Host记录: {domain}...")

                def do():
                    return self.host_manager.delete_host(domain.strip())

                def done(success_msg_tuple):
                    self._stop_loading()
                    success, msg = success_msg_tuple
                    if success:
                        self.log.append(f"✅  Host记录删除成功: {domain}")
                        QMessageBox.information(self, "成功", msg)
                        self.show_host() # 刷新列表
                    else:
                        self.log.append(f"❌  Host记录删除失败: {msg}")
                        QMessageBox.warning(self, "失败", msg)

                self._run_worker(do, done)
            else:
                self.log.append("📋  删除Host记录操作已取消。")
        else:
            self.log.append("📋  删除Host记录操作已取消。")


    def backup_hosts(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("备份 Hosts 文件")
        reply = QMessageBox.question(self, "确认备份", "确定要备份 Hosts 文件吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._start_loading("正在备份Hosts文件...")

            def do():
                return self.host_manager.backup_hosts()

            def done(success_msg_tuple):
                self._stop_loading()
                success, message = success_msg_tuple
                if success:
                    self.log.append(f"✅  Hosts文件备份成功: {message}")
                    QMessageBox.information(self, "成功", f"Hosts文件已备份到:\n{message}")
                else:
                    self.log.append(f"❌  Hosts文件备份失败: {message}")
                    QMessageBox.warning(self, "失败", f"备份失败: {message}")

            self._run_worker(do, done)
        else:
            self.log.append("📋  备份Hosts文件操作已取消。")


    # ==================== 系统服务（阶段三） ====================
    def show_service_list(self):
        self._show_table_view()
        self.label_title.setText("系统服务列表")
        self.search_box.setPlaceholderText("🔍  搜索服务名/显示名/状态")
        self._setup_table(["服务名", "显示名", "状态", "启动类型", "PID"])
        self._start_loading("正在获取系统服务列表...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.service_manager.get_services()

        def done(services):
            self.current_table_data = services # 保存原始数据
            self.table.setRowCount(len(services))
            status_colors = {
                'running': '#a6e3a1',       # 绿色
                'stopped': '#f38ba8',       # 红色
                'paused': '#f9e2af',        # 黄色
                'start_pending': '#89b4fa', # 蓝色
                'stop_pending': '#fab387',  # 橙色
                'error': '#f38ba8',         # 错误也是红色
            }
            for i, s in enumerate(services):
                status = s.get('status', '').lower()
                self._set_row(i, [
                    s.get('name',''),
                    s.get('display_name',''),
                    s.get('status',''), # 显示原始状态字符串
                    s.get('start_type',''),
                    s.get('pid','')
                ])
                # 状态列着色
                status_item = self.table.item(i, 2)
                if status_item:
                    color = status_colors.get(status, '#cdd6f4') # 默认颜色
                    status_item.setForeground(QColor(color))

            self._stop_loading(f"共 {len(services)} 个服务")
            self.log.append(f"✅  系统服务列表获取完成，共 {len(services)} 个")

        self._run_worker(do, done)

    def service_start_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("启动服务")
        name, ok = QInputDialog.getText(self, "启动服务", "请输入服务名（英文名）:")
        if ok and name:
            self._start_loading(f"正在启动服务 {name}...")

            def do():
                return self.service_manager.start_service(name.strip())

            def done(success_msg_tuple):
                self._stop_loading()
                success, msg = success_msg_tuple
                icon = "✅" if success else "❌"
                self.log.append(f"{icon}  {msg}")
                if success:
                    QMessageBox.information(self, "成功", msg)
                else:
                    QMessageBox.warning(self, "失败", msg)
                self._dispatch("service_list") # 刷新服务列表

            self._run_worker(do, done)
        else:
            self.log.append("📋  启动服务操作已取消。")


    def service_stop_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("停止服务")
        name, ok = QInputDialog.getText(self, "停止服务", "请输入服务名（英文名）:")
        if ok and name:
            reply = QMessageBox.question(self, "确认操作", f"确定要停止服务 '{name.strip()}' 吗？\n停止关键服务可能影响系统稳定性！",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No) # 默认不停止
            if reply == QMessageBox.StandardButton.Yes:
                self._start_loading(f"正在停止服务 {name}...")

                def do():
                    return self.service_manager.stop_service(name.strip())

                def done(success_msg_tuple):
                    self._stop_loading()
                    success, msg = success_msg_tuple
                    icon = "✅" if success else "❌"
                    self.log.append(f"{icon}  {msg}")
                    if success:
                        QMessageBox.information(self, "成功", msg)
                    else:
                        QMessageBox.warning(self, "失败", msg)
                    self._dispatch("service_list") # 刷新服务列表

                self._run_worker(do, done)
            else:
                self.log.append("📋  停止服务操作已取消。")
        else:
            self.log.append("📋  停止服务操作已取消。")


    def service_restart_dialog(self):
        self._show_table_view() # 确保回到表格视图
        self.label_title.setText("重启服务")
        name, ok = QInputDialog.getText(self, "重启服务", "请输入服务名（英文名）:")
        if ok and name:
            reply = QMessageBox.question(self, "确认操作", f"确定要重启服务 '{name.strip()}' 吗？\n此操作会短暂停止服务！",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No) # 默认不重启
            if reply == QMessageBox.StandardButton.Yes:
                self._start_loading(f"正在重启服务 {name}...")

                def do():
                    return self.service_manager.restart_service(name.strip())

                def done(success_msg_tuple):
                    self._stop_loading()
                    success, msg = success_msg_tuple
                    icon = "✅" if success else "❌"
                    self.log.append(f"{icon}  {msg}")
                    if success:
                        QMessageBox.information(self, "成功", msg)
                    else:
                        QMessageBox.warning(self, "失败", msg)
                    self._dispatch("service_list") # 刷新服务列表

                self._run_worker(do, done)
            else:
                self.log.append("📋  重启服务操作已取消。")
        else:
            self.log.append("📋  重启服务操作已取消。")


    def show_service_log(self):
        self._show_table_view()
        self.label_title.setText("服务操作日志")
        self.search_box.setPlaceholderText("🔍  搜索服务/操作/结果")
        self._setup_table(["时间", "服务名", "操作", "结果"])
        self._start_loading("正在加载服务操作日志...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.service_manager.get_operation_logs()

        def done(logs):
            if not logs:
                self.log.append("📋  暂无操作记录，请先对服务执行启动/停止/重启操作")
                self._stop_loading("无操作日志")
                self.current_table_data = []
                self.table.setRowCount(0)
                return

            self.current_table_data = logs # 保存原始数据
            self.table.setRowCount(len(logs))
            for i, entry in enumerate(reversed(logs)):  # 最新在前
                self._set_row(i, [entry['time'], entry['service'], entry['action'], entry['result']])
            self._stop_loading(f"共 {len(logs)} 条日志")
            self.log.append(f"✅  操作日志加载完成，共 {len(logs)} 条")

        self._run_worker(do, done)


    # ==================== Wi-Fi / 局域网（阶段四） ====================
    def show_wifi_list(self):
        self._show_table_view()
        self.label_title.setText("周边 Wi-Fi 网络")
        self.search_box.setPlaceholderText("🔍  搜索SSID/认证方式/频道")
        self._setup_table(["SSID", "信号强度", "BSSID", "认证方式", "加密", "频道"])
        self._start_loading("正在扫描周边Wi-Fi...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.wifi_manager.get_wifi_networks()

        def done(networks):
            self.current_table_data = networks # 保存原始数据
            self.table.setRowCount(len(networks))
            for i, n in enumerate(networks):
                signal_raw = n.get('signal', '')
                signal_bar = self.wifi_manager.get_signal_bar(signal_raw)
                self._set_row(i, [
                    n.get('ssid', ''),
                    signal_bar,
                    n.get('bssid', ''),
                    n.get('auth', ''),
                    n.get('cipher', ''),
                    n.get('channel', '')
                ])
                # 信号着色
                sig_item = self.table.item(i, 1)
                if sig_item:
                    try:
                        # 尝试从信号条中解析百分比
                        pct_match = re.search(r'(\d+)%', signal_bar)
                        if pct_match:
                            pct = int(pct_match.group(1))
                            if pct >= 70:
                                sig_item.setForeground(QColor('#a6e3a1'))
                            elif pct >= 40:
                                sig_item.setForeground(QColor('#f9e2af'))
                            else:
                                sig_item.setForeground(QColor('#f38ba8'))
                    except Exception:
                        pass

            self._stop_loading(f"发现 {len(networks)} 个Wi-Fi网络")
            self.log.append(f"✅  Wi-Fi扫描完成，发现 {len(networks)} 个网络")

        self._run_worker(do, done)

    def show_wifi_current(self):
        self._show_table_view()
        self.label_title.setText("当前 Wi-Fi 连接")
        self.search_box.setPlaceholderText("🔍  搜索...")
        self._setup_table(["属性", "值"])
        self._start_loading("正在获取当前Wi-Fi信息...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.wifi_manager.get_current_wifi()

        def done(info):
            label_map = {
                'ssid': 'SSID（网络名）',
                'bssid': 'BSSID（路由器MAC）',
                'signal': '信号强度',
                'rx_rate': '接收速率',
                'tx_rate': '传输速率',
                'channel': '频道',
                'radio': '无线电类型',
                'auth': '认证方式'
            }
            rows = [(label_map.get(k, k), v) for k, v in info.items() if v]
            self.current_table_data = info # 保存原始数据
            self.table.setRowCount(len(rows))
            if not rows:
                self.table.setRowCount(1)
                self._set_row(0, ["状态", "未连接到任何Wi-Fi网络"])
            else:
                for i, (k, v) in enumerate(rows):
                    if k == '信号强度':
                        v = self.wifi_manager.get_signal_bar(v) # 转换为信号条显示
                    self._set_row(i, [k, v])

            self._stop_loading("当前Wi-Fi信息获取完成")
            self.log.append("✅  当前Wi-Fi信息获取完成")

        self._run_worker(do, done)

    def show_lan_devices(self):
        self._show_table_view()
        self.label_title.setText("局域网设备（ARP表）")
        self.search_box.setPlaceholderText("🔍  搜索IP/MAC/主机名")
        self._setup_table(["IP地址", "MAC地址", "类型", "主机名"])
        self._start_loading("正在获取局域网设备（含主机名解析，稍等）...")
        self.current_table_data = [] # 清空旧数据

        def do():
            return self.wifi_manager.get_lan_devices()

        def done(devices):
            self.current_table_data = devices # 保存原始数据
            self.table.setRowCount(len(devices))
            for i, d in enumerate(devices):
                self._set_row(i, [d.get('ip',''), d.get('mac',''), d.get('type',''), d.get('hostname','')])
            self._stop_loading(f"发现 {len(devices)} 台局域网设备")
            self.log.append(f"✅  局域网设备获取完成，共 {len(devices)} 台")

        self._run_worker(do, done)

    # ==================== 局域网拓扑图（新增） ====================
    def show_lan_topology(self):
        self._show_text_view()
        self.label_title.setText("局域网拓扑图 (DOT 格式)")
        self.search_box.setPlaceholderText("") # 文本视图不显示搜索框
        self.text_display_area.setText("") # 清空旧数据
        self._start_loading("正在生成局域网拓扑图（可能包含主机名解析）...")
        self.current_text_data = "" # 清空旧数据

        def do():
            devices = self.wifi_manager.get_lan_devices()
            return utils.generate_lan_topology_dot(devices)

        def done(dot_str):
            self.text_display_area.setText(dot_str)
            self.current_text_data = dot_str # 保存文本内容到变量
            self._stop_loading("局域网拓扑图生成完成")
            self.log.append("✅  局域网拓扑图生成完成 (DOT 格式)")
            QMessageBox.information(self, "拓扑图提示",
                                    "拓扑图已生成为 DOT 格式文本。\n"
                                    "你可以将这些文本复制到 Graphviz 在线工具（如 graphviz.org/dot/）\n"
                                    "或安装 Graphviz 软件，将其渲染成图形。")

        self._run_worker(do, done)

    # ==================== 检查更新（新增） ====================
    def check_for_updates_on_startup(self):
        """应用启动时自动检查更新，不弹出成功提示，只在有更新时提示"""
        self.log.append("ℹ️  正在后台检查更新...")
        def do():
            return self.version_checker.check_for_updates()

        def done(update_info):
            if update_info.get('has_update'):
                self.log.append(f"✨  发现新版本: v{update_info['latest_version']}")
                QMessageBox.information(self, "发现新版本",
                                        f"发现新版本 v{update_info['latest_version']}!\n"
                                        f"当前版本: v{self.CURRENT_VERSION}\n"
                                        f"前往下载更新：{update_info['download_url']}")
            elif update_info.get('error'):
                self.log.append(f"❌  检查更新失败: {update_info['error']}")
            # 否则无更新，不显示提示

        self._run_worker(do, done)

    def check_for_updates(self):
        """用户点击按钮手动检查更新"""
        self._show_text_view() # 显示更新信息在文本区
        self.label_title.setText("检查更新")
        self.text_display_area.setText("正在检查最新版本...\n")
        self.text_display_area.setObjectName("update_info_text") # 更改样式
        self.text_display_area.setStyleSheet(self.styleSheet()) # 刷新样式
        self._start_loading("正在检查更新...", indefinite=True)
        self.current_text_data = "" # 清空旧数据

        def do():
            return self.version_checker.check_for_updates()

        def done(update_info):
            self._stop_loading()
            if update_info.get('has_update'):
                self.log.append(f"✨  发现新版本: v{update_info['latest_version']}")
                update_text = (
                    f"<h3 style='color: #a6e3a1;'>发现新版本: v{update_info['latest_version']}!</h3>"
                    f"<p>当前版本: v{self.CURRENT_VERSION}</p>"
                    f"<p>更新日志:</p>"
                    f"<pre style='background-color:#252535; padding: 10px; border-radius: 5px; color: #cdd6f4;'>{update_info['release_notes']}</pre>"
                    f"<p>请访问官方发布页面下载最新版。</p>"
                    f"<a href='{update_info['download_url']}' style='color: #89b4fa; text-decoration: none;'>点击前往下载页面</a>"
                )
                self.text_display_area.setHtml(update_text)
                self.current_text_data = self.text_display_area.toPlainText() # 保存文本内容到变量

                # 弹窗提示
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("发现新版本")
                msg_box.setText(f"发现新版本 v{update_info['latest_version']}！\n您当前版本为 v{self.CURRENT_VERSION}。\n是否前往下载页面？")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
                msg_box.setIcon(QMessageBox.Icon.Information)

                # 自定义按钮样式
                for btn in msg_box.buttons():
                    if msg_box.buttonRole(btn) == QMessageBox.ButtonRole.AcceptRole:
                        btn.setObjectName("dialog_ok")
                    elif msg_box.buttonRole(btn) == QMessageBox.ButtonRole.RejectRole:
                        btn.setObjectName("dialog_cancel")
                    btn.setStyleSheet(self.styleSheet()) # 应用主窗口样式

                if msg_box.exec() == QMessageBox.StandardButton.Yes:
                    QDesktopServices.openUrl(update_info['download_url'])

            elif update_info.get('error'):
                self.log.append(f"❌  检查更新失败: {update_info['error']}")
                self.text_display_area.setText(f"<p style='color: #f38ba8;'>检查更新失败: {update_info['error']}</p>"
                                               "<p>请检查网络连接或稍后再试。</p>")
                self.current_text_data = self.text_display_area.toPlainText() # 保存文本内容到变量
                QMessageBox.warning(self, "检查更新失败", f"检查更新失败: {update_info['error']}\n请检查网络连接或稍后再试。")
            else:
                self.log.append("✅  当前已是最新版本。")
                self.text_display_area.setText(f"<h3 style='color: #a6e3a1;'>您当前已是最新版本 (v{self.CURRENT_VERSION})。</h3>"
                                               "<p>无需更新。</p>")
                self.current_text_data = self.text_display_area.toPlainText() # 保存文本内容到变量
                QMessageBox.information(self, "当前最新", f"您当前已是最新版本 (v{self.CURRENT_VERSION})。")

        self._run_worker(do, done)


    # ==================== 工具方法 ====================
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

    def _run_worker(self, func, on_done, on_error=None, **kwargs):
        """
        在后台线程执行func，完成后在主线程回调on_done，出错回调on_error。
        kwargs 可包含 progress_callback，用于 WorkerThread 传递进度。
        """
        if self._worker and self._worker.isRunning():
            self.log.append("⚠️  上一个任务正在运行中，请稍后再试。")
            QMessageBox.warning(self, "任务繁忙", "上一个任务正在运行中，请稍后再试。")
            return

        self._worker = WorkerThread(func, **kwargs)

        def _done(result):
            on_done(result)
            self._worker = None # 任务完成后清空引用

        def _err(msg):
            self._stop_loading("发生错误")
            self.log.append(f"❌  错误: {msg}")
            if on_error:
                on_error(msg)
            else:
                QMessageBox.warning(self, "错误", f"操作过程中发生错误:\n{msg}")
            self._worker = None # 任务完成后清空引用

        self._worker.result_signal.connect(_done)
        self._worker.error_signal.connect(_err)
        if 'progress_callback' in kwargs: # 如果有进度回调，连接信号
            self._worker.progress_signal.connect(kwargs['progress_callback'])
        self._worker.start()

    def _make_dialog(self, title, fields):
        """
        通用输入对话框。
        fields: list of (label_text, default_value)
        返回输入值的tuple，取消则返回None
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(360) # 略微增加宽度
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12) # 增加间距
        layout.setContentsMargins(25, 25, 25, 25) # 增加边距

        inputs = []
        for label_text, default in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setMinimumWidth(100) # 增加标签宽度
            inp = QLineEdit(default)
            inp.setStyleSheet("padding: 6px; border-radius: 4px; background-color: #252535; border: 1px solid #45475a;") # 独立样式
            inp.setClearButtonEnabled(True) # 添加清除按钮
            row.addWidget(lbl)
            row.addWidget(inp)
            layout.addLayout(row)
            inputs.append(inp)

        btn_row = QHBoxLayout()
        btn_row.addStretch() # 按钮靠右
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("dialog_ok")
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialog_cancel")
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        result = []

        def on_ok():
            result.extend([inp.text().strip() for inp in inputs])
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        # 应用样式
        dialog.setStyleSheet(self.styleSheet())

        if dialog.exec() == QDialog.DialogCode.Accepted and result:
            return tuple(result)
        return None
DARK_STYLE = """
/* ===== 全局 ===== */
QWidget {
    background-color: #1a1b26;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 10pt;
    color: #c0caf5;
}

/* ===== 侧边栏 ===== */
QWidget#sidebar {
    background-color: #16161e;
    border-right: 1px solid #292e42;
    min-width: 200px;
    max-width: 240px;
}

QLabel#app_title {
    font-size: 14pt;
    font-weight: bold;
    color: #7aa2f7;
    padding: 18px 16px 10px 16px;
    background: transparent;
    letter-spacing: 1px;
}

QFrame#separator {
    background-color: #292e42;
    max-height: 1px;
    margin: 4px 12px;
}

/* ===== 主功能按钮 ===== */
QPushButton#main_btn {
    background-color: transparent;
    color: #9aa5ce;
    border: none;
    border-radius: 8px;
    padding: 11px 16px;
    font-weight: bold;
    font-size: 10pt;
    text-align: left;
    margin: 2px 8px;
}
QPushButton#main_btn:hover {
    background-color: #1f2335;
    color: #c0caf5;
}
QPushButton#main_btn[active="true"] {
    background-color: #7aa2f7;
    color: #1a1b26;
}

/* ===== 子功能按钮 ===== */
QPushButton#sub_btn {
    background-color: transparent;
    color: #565f89;
    border: none;
    border-radius: 6px;
    padding: 8px 12px 8px 32px;
    font-size: 9pt;
    text-align: left;
    margin: 1px 8px;
}
QPushButton#sub_btn:hover {
    background-color: #1f2335;
    color: #9aa5ce;
}
QPushButton#sub_btn[active="true"] {
    background-color: rgba(122, 162, 247, 0.15);
    color: #7aa2f7;
    font-weight: bold;
}

/* ===== 标题栏 ===== */
QLabel#title_label {
    font-size: 16pt;
    font-weight: bold;
    color: #7aa2f7;
    padding: 12px 16px 4px 16px;
    background: transparent;
}

QLabel#status_label {
    color: #9ece6a;
    font-size: 9pt;
    padding: 2px 16px 6px 16px;
    background: transparent;
}

/* ===== 搜索框 ===== */
QLineEdit {
    background-color: #1f2335;
    border: 1px solid #292e42;
    border-radius: 8px;
    padding: 8px 14px;
    color: #c0caf5;
    font-size: 10pt;
    margin: 4px 8px;
    selection-background-color: #7aa2f7;
}
QLineEdit:focus {
    border: 1px solid #7aa2f7;
    background-color: #24283b;
}

/* ===== 表格 ===== */
QTableWidget {
    background-color: #16161e;
    border: 1px solid #292e42;
    border-radius: 8px;
    gridline-color: #292e42;
    color: #c0caf5;
    margin: 4px 8px;
    outline: none;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #1f2335;
}
QTableWidget::item:selected {
    background-color: rgba(122, 162, 247, 0.2);
    color: #7aa2f7;
}
QTableWidget::item:hover {
    background-color: #1f2335;
}
QHeaderView::section {
    background-color: #1f2335;
    color: #7aa2f7;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #7aa2f7;
    border-right: 1px solid #292e42;
    font-weight: bold;
    font-size: 9pt;
}

/* ===== 日志/文本区 ===== */
QTextEdit {
    background-color: #16161e;
    border: 1px solid #292e42;
    border-radius: 8px;
    color: #9ece6a;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 9pt;
    padding: 10px;
    margin: 4px 8px;
}
QTextEdit#update_info_text {
    background-color: #16161e;
    border: 1px solid #292e42;
    border-radius: 8px;
    color: #c0caf5;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 10pt;
    padding: 18px;
    margin: 4px 8px;
}

/* ===== 进度条 ===== */
QProgressBar {
    background-color: #1f2335;
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    margin: 0 8px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7aa2f7, stop:1 #bb9af7);
    border-radius: 3px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #292e42;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #7aa2f7;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #292e42;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #7aa2f7;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: none;
    width: 0px;
}

/* ===== 对话框 ===== */
QDialog {
    background-color: #1a1b26;
    border: 1px solid #292e42;
    border-radius: 12px;
}
QMessageBox {
    background-color: #1a1b26;
}
QInputDialog {
    background-color: #1a1b26;
}

QPushButton#dialog_ok {
    background-color: #7aa2f7;
    color: #1a1b26;
    border: none;
    border-radius: 8px;
    padding: 8px 24px;
    font-weight: bold;
    font-size: 10pt;
}
QPushButton#dialog_ok:hover {
    background-color: #89b4fa;
}
QPushButton#dialog_cancel {
    background-color: #292e42;
    color: #9aa5ce;
    border: none;
    border-radius: 8px;
    padding: 8px 24px;
    font-size: 10pt;
}
QPushButton#dialog_cancel:hover {
    background-color: #343a52;
    color: #c0caf5;
}

/* ===== 保存按钮 ===== */
QPushButton#save_btn {
    background-color: #292e42;
    color: #9aa5ce;
    border: none;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: normal;
    font-size: 9pt;
    margin: 4px 8px 4px 0px;
}
QPushButton#save_btn:hover {
    background-color: #343a52;
    color: #c0caf5;
}

/* ===== 链接按钮 ===== */
QPushButton#link_btn {
    background-color: #7aa2f7;
    color: #1a1b26;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 10pt;
    margin-top: 15px;
}
QPushButton#link_btn:hover {
    background-color: #89b4fa;
}

/* ===== 顶部栏 ===== */
QWidget#top_bar {
    background-color: #16161e;
    border-bottom: 1px solid #292e42;
}

/* ===== 欢迎页卡片 ===== */
QFrame#welcome_card {
    background-color: #1f2335;
    border: 1px solid #292e42;
    border-radius: 12px;
    padding: 20px;
}
"""

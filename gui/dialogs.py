from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
)


def make_dialog(parent, title, fields, style_sheet=None):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumWidth(360)
    layout = QVBoxLayout(dialog)
    layout.setSpacing(12)
    layout.setContentsMargins(25, 25, 25, 25)

    inputs = []
    for label_text, default in fields:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(100)
        inp = QLineEdit(default)
        inp.setStyleSheet(
            "padding: 6px; border-radius: 4px; "
            "background-color: #252535; border: 1px solid #45475a;"
        )
        inp.setClearButtonEnabled(True)
        row.addWidget(lbl)
        row.addWidget(inp)
        layout.addLayout(row)
        inputs.append(inp)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
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

    if style_sheet:
        dialog.setStyleSheet(style_sheet)

    if dialog.exec() == QDialog.DialogCode.Accepted and result:
        return tuple(result)
    return None

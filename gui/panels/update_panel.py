from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl


RELEASES_PAGE = "https://github.com/HiPing-20/WinNetTool/releases"


def check_for_updates_on_startup(window):
    window.log.append("正在后台检查更新...")

    def do():
        return window.version_checker.check_for_updates()

    def done(update_info):
        try:
            if update_info.get('has_update'):
                window.log.append(f"发现新版本: v{update_info['latest_version']}")
                QMessageBox.information(
                    window, "发现新版本",
                    f"发现新版本 v{update_info['latest_version']}!\n"
                    f"当前版本: v{window.CURRENT_VERSION}\n"
                    f"前往下载更新：{RELEASES_PAGE}"
                )
            elif update_info.get('error'):
                window.log.append(f"检查更新失败: {update_info['error']}")
            else:
                window.log.append("当前已是最新版本。")
        except Exception:
            pass

    window._run_worker(do, done)


def check_for_updates(window):
    window._show_text_view()
    window.label_title.setText("检查更新")
    window.text_display_area.setHtml(
        "<div style='padding:40px;text-align:center;color:#565f89;'>"
        "<div style='font-size:40px;margin-bottom:16px;'>&#128640;</div>"
        "<div style='font-size:14px;'>正在检查最新版本...</div>"
        "</div>"
    )
    window.text_display_area.setObjectName("update_info_text")
    window.text_display_area.setStyleSheet(window.styleSheet())
    window._start_loading("正在检查更新...", indefinite=True)
    window.current_text_data = ""

    def do():
        return window.version_checker.check_for_updates()

    def done(update_info):
        window._stop_loading()

        if update_info.get('has_update'):
            window.log.append(f"发现新版本: v{update_info['latest_version']}")
            ver = update_info['latest_version']
            notes = update_info.get('release_notes', '无更新说明')
            window.text_display_area.setHtml(f"""
                <div style="padding: 24px;">
                    <div style="text-align:center; margin-bottom: 24px;">
                        <span style="font-size:48px;">&#127881;</span>
                        <h2 style="color: #9ece6a; font-size: 20px; margin-top: 8px;">发现新版本: v{ver}</h2>
                        <p style="color: #565f89; font-size: 13px;">当前版本: v{window.CURRENT_VERSION}</p>
                    </div>
                    <div style="background:#1f2335; border:1px solid #292e42; border-radius:10px; padding:18px; margin-bottom:20px;">
                        <div style="color:#7aa2f7; font-weight:bold; margin-bottom:10px;">更新日志</div>
                        <pre style="color:#c0caf5; font-size:12px; white-space:pre-wrap; font-family:inherit;">{notes}</pre>
                    </div>
                    <div style="text-align:center;">
                        <a href="{RELEASES_PAGE}" style="
                            display:inline-block; background:#7aa2f7; color:#1a1b26;
                            padding:10px 32px; border-radius:8px; text-decoration:none;
                            font-weight:bold; font-size:13px;
                        ">前往下载页面</a>
                    </div>
                </div>
            """)
            window.current_text_data = window.text_display_area.toPlainText()

            reply = QMessageBox.question(
                window, "发现新版本",
                f"发现新版本 v{ver}！\n您当前版本为 v{window.CURRENT_VERSION}。\n是否前往下载页面？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    QDesktopServices.openUrl(QUrl(RELEASES_PAGE))
                except Exception:
                    pass

        elif update_info.get('error'):
            error_msg = update_info['error']
            window.log.append(f"检查更新失败: {error_msg}")

            window.text_display_area.setHtml(f"""
                <div style="padding: 40px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 16px;">&#128269;</div>
                    <h3 style="color: #e0af68; margin-bottom: 12px;">检查更新失败</h3>
                    <p style="color: #c0caf5; font-size: 13px; background:#1f2335; border:1px solid #292e42; border-radius:8px; padding:12px; display:inline-block;">{error_msg}</p>
                    <div style="margin-top: 20px;">
                        <p style="color:#9aa5ce; font-size:12px; margin-bottom:12px;">你可以手动前往 Release 页面查看：</p>
                        <a href="{RELEASES_PAGE}" style="
                            display:inline-block; background:#292e42; color:#c0caf5;
                            padding:10px 24px; border-radius:8px; text-decoration:none;
                            font-size:13px;
                        ">打开 Release 页面</a>
                    </div>
                    <p style="color:#565f89; font-size:11px; margin-top:16px;">当前版本: v{window.CURRENT_VERSION}</p>
                </div>
            """)
            window.current_text_data = window.text_display_area.toPlainText()

        else:
            window.log.append("当前已是最新版本。")
            window.text_display_area.setHtml(f"""
                <div style="padding: 40px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 16px;">&#9989;</div>
                    <h3 style="color: #9ece6a; margin-bottom: 8px;">当前已是最新版本</h3>
                    <p style="color: #565f89; font-size: 14px;">v{window.CURRENT_VERSION}</p>
                    <p style="color: #565f89; font-size: 12px; margin-top: 16px;">无需更新，继续享受最新功能。</p>
                </div>
            """)
            window.current_text_data = window.text_display_area.toPlainText()

    window._run_worker(do, done)

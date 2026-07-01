from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl


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
                    f"前往下载更新：{update_info['download_url']}"
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
            url = update_info.get('download_url', '#')
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
                        <a href="{url}" style="
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
                QDesktopServices.openUrl(QUrl(url))

        elif update_info.get('error'):
            error_msg = update_info['error']
            window.log.append(f"检查更新失败: {error_msg}")
            window.text_display_area.setHtml(f"""
                <div style="padding: 40px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 16px;">&#128269;</div>
                    <h3 style="color: #f7768e; margin-bottom: 12px;">检查更新失败</h3>
                    <p style="color: #565f89; font-size: 13px;">{error_msg}</p>
                    <p style="color: #565f89; font-size: 12px; margin-top: 12px;">请检查网络连接或稍后再试。</p>
                    <div style="margin-top: 24px; background:#1f2335; border:1px solid #292e42; border-radius:10px; padding:16px; text-align:left; display:inline-block;">
                        <p style="color:#7aa2f7; font-weight:bold; margin-bottom:8px;">提示</p>
                        <p style="color:#9aa5ce; font-size:12px; line-height:1.6;">
                            1. 请确保已连接互联网<br>
                            2. 检查防火墙是否阻止了访问<br>
                            3. 当前版本: v{window.CURRENT_VERSION}
                        </p>
                    </div>
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

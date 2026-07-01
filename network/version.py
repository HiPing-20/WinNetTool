import re
import requests


class VersionChecker:
    def __init__(self, current_version, update_check_url):
        self.current_version = current_version
        self.update_check_url = update_check_url
        # Release 页面地址（用于直接访问）
        self.releases_url = update_check_url.replace(
            '/releases/latest', '/releases'
        )

    def check_for_updates(self):
        # 先尝试 API（有版本号信息）
        result, error = self._try_api()
        if result:
            return result

        # API 失败则尝试直接访问 Release 页面
        result2, error2 = self._try_page()
        if result2:
            return result2

        return {'has_update': False, 'error': error or error2 or '检查失败'}

    def _try_api(self):
        try:
            response = requests.get(self.update_check_url, timeout=10)
            if response.status_code == 403:
                return None, "GitHub API 频率限制"
            if response.status_code == 404:
                return None, "尚未发布 Release"
            response.raise_for_status()
            data = response.json()
            tag = data.get('tag_name', '').lstrip('vV')
            cmp = self._version_compare(tag, self.current_version)
            if cmp > 0:
                return {
                    'has_update': True,
                    'latest_version': tag,
                    'current_version': self.current_version,
                    'release_notes': data.get('body', '无更新说明'),
                    'download_url': data.get('html_url', '#')
                }, None
            return {'has_update': False, 'message': '当前已是最新版本'}, None
        except Exception:
            return None, None

    def _try_page(self):
        """直接访问 Release 页面，提取版本号"""
        try:
            response = requests.get(self.releases_url, timeout=10,
                                    headers={'User-Agent': 'WinNetTool'})
            if response.status_code != 200:
                return None, "无法访问 Release 页面"

            # 从页面 HTML 中提取 tag 版本号
            # 匹配 /releases/tag/v1.0.0 这样的链接
            match = re.search(r'/releases/tag/v?([\d.]+)', response.text)
            if match:
                tag = match.group(1)
                cmp = self._version_compare(tag, self.current_version)
                if cmp > 0:
                    return {
                        'has_update': True,
                        'latest_version': tag,
                        'current_version': self.current_version,
                        'release_notes': '请前往 GitHub 查看更新日志',
                        'download_url': self.releases_url
                    }, None
                return {'has_update': False, 'message': '当前已是最新版本'}, None

            return None, "无法解析版本信息"
        except requests.exceptions.ConnectionError:
            return None, "网络连接失败"
        except Exception:
            return None, None

    def _version_compare(self, v1, v2):
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split('.')]
        try:
            n1 = tuple(normalize(v1))
            n2 = tuple(normalize(v2))
            if n1 > n2:
                return 1
            elif n1 < n2:
                return -1
        except Exception:
            pass
        return 0

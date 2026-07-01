import re
import requests


class VersionChecker:
    def __init__(self, current_version, update_check_url):
        self.current_version = current_version
        self.update_check_url = update_check_url

    def check_for_updates(self):
        try:
            response = requests.get(self.update_check_url, timeout=5)
            response.raise_for_status()
            latest_release = response.json()

            latest_version = latest_release.get('tag_name', '').lstrip('vV')
            release_notes = latest_release.get('body', '无更新说明')
            download_url = latest_release.get('html_url', '#')

            if self._version_compare(latest_version, self.current_version) > 0:
                return {
                    'has_update': True,
                    'latest_version': latest_version,
                    'current_version': self.current_version,
                    'release_notes': release_notes,
                    'download_url': download_url
                }
            else:
                return {'has_update': False, 'message': '当前已是最新版本'}
        except requests.exceptions.RequestException as e:
            return {'has_update': False, 'error': f"检查更新失败: {str(e)}"}
        except Exception as e:
            return {'has_update': False, 'error': f"解析更新信息失败: {str(e)}"}

    def _version_compare(self, v1, v2):
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split('.')]
        norm_v1 = tuple(normalize(v1))
        norm_v2 = tuple(normalize(v2))
        if norm_v1 > norm_v2:
            return 1
        elif norm_v1 < norm_v2:
            return -1
        else:
            return 0

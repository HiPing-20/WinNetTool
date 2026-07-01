import re

from .base import run_hidden_cmd, get_system_encoding


class WifiManager:
    def __init__(self):
        self.encoding = get_system_encoding()

    def _run_with_encoding_fallback(self, cmd, timeout=30):
        """执行命令，自动尝试多种编码解码（用于不确定输出编码的场景）"""
        primary = get_system_encoding()
        fallbacks = ['utf-8', 'latin-1']
        encodings = [primary] + [e for e in fallbacks if e != primary]

        for enc in encodings:
            try:
                result = run_hidden_cmd(
                    cmd,
                    capture_output=True, text=True, encoding=enc, errors='replace', timeout=timeout
                )
                if result.returncode == 0 and result.stdout:
                    # 检查是否有乱码（连续的替换字符）
                    if '\ufffd' not in result.stdout[:500]:
                        return result.stdout
            except Exception:
                continue
        # 最后兜底：用系统编码 + ignore
        try:
            result = run_hidden_cmd(
                cmd,
                capture_output=True, text=True, encoding=primary, errors='ignore', timeout=timeout
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            pass
        return None

    def get_wifi_networks(self):
        networks = []
        try:
            output = self._run_with_encoding_fallback(['netsh', 'wlan', 'show', 'networks', 'mode=Bssid'])
            if not output:
                return [{'ssid': '未找到Wi-Fi网络或权限不足', 'signal': '', 'auth': '', 'cipher': '', 'bssid': '', 'channel': ''}]

            current = {}
            for line in output.splitlines():
                line = line.strip()
                if re.match(r'^(?:SSID\s*\d+\s*|SSID)\s*:', line, re.IGNORECASE):
                    if current.get('ssid'):
                        networks.append(current)
                        current = {}
                    current['ssid'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:信号|Signal)\s*:', line, re.IGNORECASE):
                    current['signal'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:身份验证|Authentication)\s*:', line, re.IGNORECASE):
                    current['auth'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:加密|Cipher)\s*:', line, re.IGNORECASE):
                    current['cipher'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'BSSID\s*:', line, re.IGNORECASE) and 'BSSID 1' not in line and re.search(r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}', line):
                    current['bssid'] = line.split(':', 1)[1].strip()
                elif re.search(r'(?:频道|Channel)\s*:', line, re.IGNORECASE):
                    current['channel'] = line.split(':', 1)[1].strip() if ':' in line else ''

            if current.get('ssid'):
                networks.append(current)
        except Exception as e:
            networks.append({'ssid': f'获取失败: {str(e)}', 'signal': '', 'auth': '', 'cipher': '', 'bssid': '', 'channel': ''})
        return networks

    def get_current_wifi(self):
        try:
            output = self._run_with_encoding_fallback(['netsh', 'wlan', 'show', 'interfaces'])
            if not output:
                return {}

            info = {}
            for line in output.splitlines():
                line = line.strip()
                if re.search(r'SSID\s*:', line, re.IGNORECASE) and 'BSSID' not in line:
                    info['ssid'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'BSSID\s*:', line, re.IGNORECASE):
                    info['bssid'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:信号|Signal)\s*:', line, re.IGNORECASE):
                    info['signal'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:接收速率|Receive rate)\s*:', line, re.IGNORECASE):
                    info['rx_rate'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:传输速率|Transmit rate)\s*:', line, re.IGNORECASE):
                    info['tx_rate'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:频道|Channel)\s*:', line, re.IGNORECASE):
                    info['channel'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:无线电类型|Radio type)\s*:', line, re.IGNORECASE):
                    info['radio'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif re.search(r'(?:身份验证|Authentication)\s*:', line, re.IGNORECASE):
                    info['auth'] = line.split(':', 1)[1].strip() if ':' in line else ''
            return info
        except Exception as e:
            return {'ssid': f'获取失败: {str(e)}'}

    def get_lan_devices(self):
        devices = []
        try:
            output = self._run_with_encoding_fallback(['arp', '-a'])
            if not output:
                return [{'ip': '无法获取ARP表', 'mac': '', 'type': '', 'hostname': ''}]

            for line in output.splitlines():
                line = line.strip()
                match = re.match(
                    r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+'
                    r'([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})\s+'
                    r'(\S+)',
                    line
                )
                if match:
                    ip = match.group(1)
                    mac = match.group(2).replace('-', ':').upper()
                    dev_type = match.group(3)
                    devices.append({
                        'ip': ip,
                        'mac': mac,
                        'type': dev_type,
                        'hostname': ''
                    })
        except Exception as e:
            devices.append({'ip': f'获取失败: {str(e)}', 'mac': '', 'type': '', 'hostname': ''})
        return devices

    def get_signal_bar(self, signal_str):
        try:
            if '%' in signal_str:
                pct = int(signal_str.replace('%', '').strip())
            else:
                pct = int(signal_str.strip())
            bars = pct // 20
            filled = '█' * bars
            empty = '░' * (5 - bars)
            return f"{filled}{empty} {pct}%"
        except Exception:
            return signal_str

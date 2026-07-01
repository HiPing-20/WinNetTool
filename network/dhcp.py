import re

from .base import run_hidden_cmd, get_system_encoding


class DHCPManager:
    def __init__(self):
        self.encoding = get_system_encoding()

    def _run_ipconfig(self):
        """执行 ipconfig /all 并处理编码"""
        for enc in [self.encoding, 'utf-8', 'latin-1']:
            try:
                result = run_hidden_cmd(
                    ['ipconfig', '/all'],
                    capture_output=True, text=True, encoding=enc, errors='replace'
                )
                if result.returncode == 0 and result.stdout:
                    if '\ufffd' not in result.stdout[:500]:
                        return result.stdout
            except Exception:
                continue
        # 兜底
        try:
            result = run_hidden_cmd(
                ['ipconfig', '/all'],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            return result.stdout
        except Exception:
            return ''

    def get_dhcp_info(self):
        try:
            output = self._run_ipconfig()
            if not output:
                return [{"name": "未找到DHCP信息", "status": "无"}]

            dhcp_info = []
            lines = output.splitlines()
            current_adapter = None

            adapter_pattern = re.compile(r'^\s*([^:]+)\s+适配器|^\s*([^:]+)\s+adapter', re.IGNORECASE)
            dhcp_enabled_pattern = re.compile(r'DHCP (?:已启用|Enabled)\s*:\s*(是|Yes|否|No)', re.IGNORECASE)
            dhcp_server_pattern = re.compile(r'DHCP (?:服务器|Server)\s*:\s*([\d\.]+)', re.IGNORECASE)
            ip_address_pattern = re.compile(r'IPv4 (?:地址|Address)\.\s*:\s*([\d\.]+)', re.IGNORECASE)
            status_pattern = re.compile(r'媒体状态|Media State\s*:\s*(.+)', re.IGNORECASE)

            for line in lines:
                line = line.strip()
                adapter_match = adapter_pattern.match(line)
                if adapter_match:
                    if current_adapter:
                        dhcp_info.append(current_adapter)
                    name = adapter_match.group(1) or adapter_match.group(2)
                    current_adapter = {"name": name.strip(), "status": "未知"}
                    continue

                if current_adapter:
                    if dhcp_enabled_match := dhcp_enabled_pattern.search(line):
                        current_adapter["dhcp_enabled"] = "是" if dhcp_enabled_match.group(1).lower() in ['是', 'yes'] else "否"
                    elif dhcp_server_match := dhcp_server_pattern.search(line):
                        current_adapter["dhcp_server"] = dhcp_server_match.group(1)
                    elif ip_address_match := ip_address_pattern.search(line):
                        current_adapter["ip"] = ip_address_match.group(1)
                    elif status_match := status_pattern.search(line):
                        current_adapter["status"] = status_match.group(1).strip()

            if current_adapter:
                dhcp_info.append(current_adapter)

            return dhcp_info if dhcp_info else [{"name": "未找到DHCP信息", "status": "无"}]
        except Exception as e:
            return [{"name": f"获取失败: {str(e)}", "status": "错误"}]

    def release_ip(self):
        try:
            result = run_hidden_cmd(
                ['ipconfig', '/release'],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            return result.returncode == 0
        except Exception:
            return False

    def renew_ip(self):
        try:
            result = run_hidden_cmd(
                ['ipconfig', '/renew'],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_dhcp_server_info(self):
        try:
            output = self._run_ipconfig()
            if not output:
                return [{"server": "未找到DHCP服务器", "status": "无"}]

            servers = []
            lines = output.splitlines()
            dhcp_server_pattern = re.compile(r'DHCP (?:服务器|Server)\s*:\s*([\d\.]+)', re.IGNORECASE)

            for line in lines:
                line = line.strip()
                if dhcp_server_match := dhcp_server_pattern.search(line):
                    server = dhcp_server_match.group(1)
                    if server and server != "未定义":
                        servers.append({"server": server, "status": "活动"})

            unique_servers = []
            seen_servers = set()
            for s in servers:
                if s['server'] not in seen_servers:
                    unique_servers.append(s)
                    seen_servers.add(s['server'])

            return unique_servers if unique_servers else [{"server": "未找到DHCP服务器", "status": "无"}]
        except Exception as e:
            return [{"server": f"获取失败: {str(e)}", "status": "错误"}]

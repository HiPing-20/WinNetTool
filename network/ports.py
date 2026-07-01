import psutil
import nmap
import ctypes

from .base import run_hidden_cmd, get_system_encoding


class LocalPortManager:
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.encoding = get_system_encoding()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def get_local_ports(self):
        ports = []
        for conn in psutil.net_connections():
            if conn.laddr:
                try:
                    name = psutil.Process(conn.pid).name() if conn.pid else ''
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    name = ''
                ports.append({
                    'protocol': str(conn.type),
                    'port': conn.laddr.port,
                    'status': conn.status,
                    'pid': str(conn.pid),
                    'name': name
                })
        return ports

    def get_firewall_rules(self):
        try:
            # netsh advfirewall 输出是 UTF-8，但其他 netsh 子命令可能是 GBK
            output = None
            for encoding in ['utf-8', self.encoding, 'latin-1']:
                try:
                    result = run_hidden_cmd(
                        ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all', 'dir=in'],
                        capture_output=True, text=True, encoding=encoding, errors='replace'
                    )
                    if result.returncode == 0 and result.stdout:
                        # 检查是否有乱码（连续替换字符）
                        sample = result.stdout[:300]
                        bad_count = sample.count('\ufffd')
                        if bad_count == 0:
                            output = result.stdout
                            break
                        elif not output or bad_count < output[:300].count('\ufffd'):
                            output = result.stdout
                except Exception:
                    continue

            if not output:
                return []

            rules = []
            current = {}
            lines = output.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("规则名称:") or "规则名称" in line or line.startswith("Rule Name:"):
                    if current.get('name'):
                        rules.append(current)
                        current = {}

                    if ":" in line:
                        name_part = line.split(":", 1)[1].strip()
                    else:
                        name_part = line.replace("规则名称", "").replace("Rule Name", "").strip()
                    current['name'] = name_part
                    i += 1

                    while i < len(lines) and (not lines[i].strip() or "----" in lines[i] or "===" in lines[i]):
                        i += 1

                    while i < len(lines):
                        field_line = lines[i].strip()
                        if not field_line:
                            i += 1
                            continue
                        if field_line.startswith("规则名称:") or "规则名称" in field_line or field_line.startswith("Rule Name:"):
                            break

                        if field_line.startswith("已启用:") or "已启用" in field_line or field_line.startswith("Enabled:"):
                            if ":" in field_line:
                                current['enabled'] = field_line.split(":", 1)[1].strip()
                            else:
                                current['enabled'] = field_line.replace("已启用", "").replace("Enabled", "").strip()
                        elif field_line.startswith("本地端口:") or "本地端口" in field_line or field_line.startswith("Local Port:"):
                            if ":" in field_line:
                                port_val = field_line.split(":", 1)[1].strip()
                            else:
                                port_val = field_line.replace("本地端口", "").replace("Local Port", "").strip()
                            if port_val and port_val not in ["任何", "Any", ""]:
                                current['port'] = port_val
                        elif field_line.startswith("操作:") or "操作" in field_line or field_line.startswith("Action:"):
                            if ":" in field_line:
                                current['action'] = field_line.split(":", 1)[1].strip()
                            else:
                                current['action'] = field_line.replace("操作", "").replace("Action", "").strip()
                        i += 1
                else:
                    i += 1

            if current.get('name'):
                rules.append(current)
            return rules
        except Exception:
            return []

    def _run_netsh_firewall(self, cmd):
        """执行 netsh advfirewall 命令，输出是 UTF-8"""
        for enc in ['utf-8', self.encoding]:
            try:
                result = run_hidden_cmd(cmd, check=True, capture_output=True, text=True, encoding=enc, errors='replace')
                return result
            except UnicodeDecodeError:
                continue
        return run_hidden_cmd(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

    def open_port(self, port, rule_name):
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}', 'dir=in', 'action=allow',
            'protocol=TCP', f'localport={port}'
        ]
        self._run_netsh_firewall(cmd)

    def close_port(self, rule_name):
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'set', 'rule',
            f'name={rule_name}', 'new', 'enable=no'
        ]
        self._run_netsh_firewall(cmd)

    def delete_port(self, rule_name):
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            f'name={rule_name}'
        ]
        self._run_netsh_firewall(cmd)

    def get_port_distribution_data(self):
        port_counts = {}
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port != 0:
                port = conn.laddr.port
                port_counts[port] = port_counts.get(port, 0) + 1
        return [{'port': p, 'count': c} for p, c in port_counts.items()]


class PortScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()

    def scan_range(self, ip_range):
        results = []
        try:
            for ip_entry in ip_range.split(','):
                ip_entry = ip_entry.strip()
                if '/' in ip_entry or '-' in ip_entry:
                    self.nm.scan(hosts=ip_entry, arguments='-p 1-1024 -T4')
                else:
                    self.nm.scan(hosts=ip_entry, arguments='-p 1-65535 -T4')

                for host in self.nm.all_hosts():
                    for proto in self.nm[host].all_protocols():
                        lport = self.nm[host][proto].keys()
                        for port in lport:
                            state = self.nm[host][proto][port]['state']
                            results.append({
                                'ip': host,
                                'port': port,
                                'status': state
                            })
        except nmap.PortScannerError as e:
            results.append({'ip': '扫描错误', 'port': 0, 'status': str(e)})
        except Exception as e:
            results.append({'ip': '扫描异常', 'port': 0, 'status': str(e)})
        return results

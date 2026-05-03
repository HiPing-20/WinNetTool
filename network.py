import subprocess
import psutil
import nmap
import ctypes
import random
import socket
import locale
import time
import re
import datetime
import requests # 用于版本检查

# ---------------- 本地端口与防火墙管理 ----------------
class LocalPortManager:
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.encoding = locale.getpreferredencoding()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
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
            encodings_to_try = ['utf-8', 'gbk', 'cp936', locale.getpreferredencoding(), 'latin-1']
            output = None
            for encoding in encodings_to_try:
                try:
                    result = subprocess.run(
                        ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all', 'dir=in'],
                        capture_output=True, text=True, encoding=encoding, errors='ignore'
                    )
                    if result.returncode == 0 and result.stdout:
                        output = result.stdout
                        break
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
                # 兼容中文和英文的规则名称行
                if line.startswith("规则名称:") or "规则名称" in line or line.startswith("Rule Name:"):
                    if current.get('name'): # 如果已经有一个规则被解析，就添加到列表
                        rules.append(current)
                        current = {} # 重置

                    if ":" in line:
                        name_part = line.split(":", 1)[1].strip()
                    else: # 兼容只有关键字的情况，比如只有 "规则名称"
                        name_part = line.replace("规则名称", "").replace("Rule Name", "").strip()
                    current['name'] = name_part
                    i += 1

                    # 跳过分隔线和空行
                    while i < len(lines) and (not lines[i].strip() or "----" in lines[i] or "===" in lines[i]):
                        i += 1

                    # 解析当前规则的字段
                    while i < len(lines):
                        field_line = lines[i].strip()
                        if not field_line: # 空行跳过
                            i += 1
                            continue
                        # 如果遇到下一个规则名称，则停止解析当前规则
                        if field_line.startswith("规则名称:") or "规则名称" in field_line or field_line.startswith("Rule Name:"):
                            break

                        # 解析“已启用”/“Enabled”
                        if field_line.startswith("已启用:") or "已启用" in field_line or field_line.startswith("Enabled:"):
                            if ":" in field_line:
                                current['enabled'] = field_line.split(":", 1)[1].strip()
                            else:
                                current['enabled'] = field_line.replace("已启用", "").replace("Enabled", "").strip()
                        # 解析“本地端口”/“Local Port”
                        elif field_line.startswith("本地端口:") or "本地端口" in field_line or field_line.startswith("Local Port:"):
                            if ":" in field_line:
                                port_val = field_line.split(":", 1)[1].strip()
                            else:
                                port_val = field_line.replace("本地端口", "").replace("Local Port", "").strip()
                            if port_val and port_val not in ["任何", "Any", ""]:
                                current['port'] = port_val
                        # 解析“操作”/“Action”
                        elif field_line.startswith("操作:") or "操作" in field_line or field_line.startswith("Action:"):
                            if ":" in field_line:
                                current['action'] = field_line.split(":", 1)[1].strip()
                            else:
                                current['action'] = field_line.replace("操作", "").replace("Action", "").strip()
                        i += 1 # 移动到下一行
                else:
                    i += 1 # 如果不是规则名称行，则跳过

            if current.get('name'): # 添加最后一个解析的规则
                rules.append(current)
            return rules
        except Exception as e:
            # print(f"Error getting firewall rules: {e}") # 方便调试
            return []

    def open_port(self, port, rule_name):
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}', 'dir=in', 'action=allow',
            'protocol=TCP', f'localport={port}'
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding=self.encoding)

    def close_port(self, rule_name):
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'set', 'rule',
            f'name={rule_name}', 'new', 'enable=no'
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding=self.encoding)

    def delete_port(self, rule_name):
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            f'name={rule_name}'
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding=self.encoding)

    def get_port_distribution_data(self):
        """获取本地端口使用分布数据，按端口计数"""
        port_counts = {}
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port != 0:
                port = conn.laddr.port
                port_counts[port] = port_counts.get(port, 0) + 1

        # 转换为列表字典格式，方便处理
        return [{'port': p, 'count': c} for p, c in port_counts.items()]


# ---------------- 局域网端口扫描 ----------------
class PortScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()

    def scan_range(self, ip_range):
        results = []
        try:
            for ip_entry in ip_range.split(','): # 允许逗号分隔多个IP或范围
                ip_entry = ip_entry.strip()
                # 优化：判断是否是单个IP或CIDR，避免对单个IP也全端口扫描
                if '/' in ip_entry or '-' in ip_entry: # CIDR或范围，可能主机数较多
                    # 默认扫描常用端口，或可配置
                    self.nm.scan(hosts=ip_entry, arguments='-p 1-1024 -T4') # 仅扫描常用端口
                else: # 单个IP，全端口扫描
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
            # print(f"Nmap Error: {e}") # 方便调试
            results.append({'ip': '扫描错误', 'port': 0, 'status': str(e)})
        except Exception as e:
            # print(f"Scan Error: {e}") # 方便调试
            results.append({'ip': '扫描异常', 'port': 0, 'status': str(e)})
        return results

# ---------------- DHCP 管理 ----------------
class DHCPManager:
    def __init__(self):
        self.encoding = locale.getpreferredencoding()

    def get_dhcp_info(self):
        try:
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            output = result.stdout

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
            result = subprocess.run(
                ['ipconfig', '/release'],
                capture_output=True, text=True, encoding=self.encoding
            )
            return result.returncode == 0
        except Exception:
            return False

    def renew_ip(self):
        try:
            result = subprocess.run(
                ['ipconfig', '/renew'],
                capture_output=True, text=True, encoding=self.encoding
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_dhcp_server_info(self):
        try:
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            output = result.stdout

            servers = []
            lines = output.splitlines()

            dhcp_server_pattern = re.compile(r'DHCP (?:服务器|Server)\s*:\s*([\d\.]+)', re.IGNORECASE)

            for line in lines:
                line = line.strip()
                if dhcp_server_match := dhcp_server_pattern.search(line):
                    server = dhcp_server_match.group(1)
                    if server and server != "未定义":
                        servers.append({"server": server, "status": "活动"})

            # 过滤重复的 DHCP 服务器
            unique_servers = []
            seen_servers = set()
            for s in servers:
                if s['server'] not in seen_servers:
                    unique_servers.append(s)
                    seen_servers.add(s['server'])

            return unique_servers if unique_servers else [{"server": "未找到DHCP服务器", "status": "无"}]
        except Exception as e:
            return [{"server": f"获取失败: {str(e)}", "status": "错误"}]

# ---------------- Hosts 文件管理 ----------------
class HostManager:
    def __init__(self):
        self.hosts_file = r"C:\Windows\System32\drivers\etc\hosts"

    def get_hosts(self):
        hosts = []
        try:
            with open(self.hosts_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            hosts.append({"ip": parts[0], "domain": parts[1]})
        except Exception as e:
            hosts.append({"ip": f"读取失败: {str(e)}", "domain": "错误"})
        return hosts

    def add_host(self, ip, domain):
        try:
            existing_hosts = self.get_hosts()
            # 检查域名是否已存在，不区分大小写
            if any(h['domain'].lower() == domain.lower() for h in existing_hosts):
                return False, "域名已存在"
            with open(self.hosts_file, "a", encoding="utf-8") as f:
                f.write(f"\n{ip}\t{domain}")
            return True, "添加成功"
        except Exception as e:
            return False, f"添加失败: {str(e)}"

    def delete_host(self, domain):
        try:
            lines = []
            deleted = False
            with open(self.hosts_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_strip = line.strip()
                    if line_strip and not line_strip.startswith("#"):
                        parts = line_strip.split()
                        # 检查域名是否匹配，不区分大小写
                        if len(parts) >= 2 and parts[1].lower() == domain.lower():
                            deleted = True
                            continue # 跳过此行
                    lines.append(line)
            if deleted:
                with open(self.hosts_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True, "删除成功"
            else:
                return False, "域名不存在"
        except Exception as e:
            return False, f"删除失败: {str(e)}"

    def update_host(self, old_domain, new_ip, new_domain):
        try:
            lines = []
            updated = False
            with open(self.hosts_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_strip = line.strip()
                    if line_strip and not line_strip.startswith("#"):
                        parts = line_strip.split()
                        # 检查旧域名是否匹配，不区分大小写
                        if len(parts) >= 2 and parts[1].lower() == old_domain.lower():
                            lines.append(f"{new_ip}\t{new_domain}\n")
                            updated = True
                            continue
                    lines.append(line)
            if updated:
                with open(self.hosts_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True, "修改成功"
            else:
                return False, "域名不存在"
        except Exception as e:
            return False, f"修改失败: {str(e)}"

    def backup_hosts(self):
        try:
            import shutil
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.hosts_file + f".backup_{timestamp}"
            shutil.copy2(self.hosts_file, backup_file)
            return True, f"备份成功: {backup_file}"
        except Exception as e:
            return False, f"备份失败: {str(e)}"

# ---------------- 系统服务管理 ----------------
class ServiceManager:
    def __init__(self):
        self.encoding = locale.getpreferredencoding()
        self._operation_log = []

    def get_services(self):
        """获取所有系统服务列表"""
        services = []
        try:
            for svc in psutil.win_service_iter():
                try:
                    info = svc.as_dict()
                    services.append({
                        'name': info.get('name', ''),
                        'display_name': info.get('display_name', ''),
                        'status': info.get('status', ''),
                        'start_type': info.get('start_type', ''),
                        'pid': str(info.get('pid', '')) if info.get('pid') else '',
                        'description': info.get('description', '')
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied): # 避免个别服务导致整个列表获取失败
                    continue
        except Exception as e:
            services.append({
                'name': f'获取失败: {str(e)}',
                'display_name': '',
                'status': '错误',
                'start_type': '',
                'pid': '',
                'description': ''
            })
        return services

    def start_service(self, service_name):
        """启动服务"""
        try:
            result = subprocess.run(
                ['sc', 'start', service_name],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            # 检查返回码或输出，'1056'表示服务已在运行
            if result.returncode == 0 or '1056' in result.stdout or 'SERVICE_ALREADY_RUNNING' in result.stdout:
                self._log_operation(service_name, '启动', '成功')
                return True, f"服务 '{service_name}' 启动成功"
            else:
                msg = result.stdout.strip() or result.stderr.strip()
                self._log_operation(service_name, '启动', f'失败: {msg}')
                return False, f"启动失败: {msg}"
        except Exception as e:
            self._log_operation(service_name, '启动', f'异常: {str(e)}')
            return False, f"启动异常: {str(e)}"

    def stop_service(self, service_name):
        """停止服务"""
        try:
            result = subprocess.run(
                ['sc', 'stop', service_name],
                capture_output=True, text=True, encoding=self.encoding, errors='ignore'
            )
            # 检查返回码或输出，'1062'表示服务未运行
            if result.returncode == 0 or '1062' in result.stdout or 'SERVICE_NOT_ACTIVE' in result.stdout:
                self._log_operation(service_name, '停止', '成功')
                return True, f"服务 '{service_name}' 停止成功"
            else:
                msg = result.stdout.strip() or result.stderr.strip()
                self._log_operation(service_name, '停止', f'失败: {msg}')
                return False, f"停止失败: {msg}"
        except Exception as e:
            self._log_operation(service_name, '停止', f'异常: {str(e)}')
            return False, f"停止异常: {str(e)}"

    def restart_service(self, service_name):
        """重启服务"""
        self._log_operation(service_name, '重启', '尝试停止')
        stop_ok, stop_msg = self.stop_service(service_name)

        # 即使停止失败，也尝试启动，因为可能已经停止或只是暂时延迟
        time.sleep(1) # 给予服务一些停止时间

        self._log_operation(service_name, '重启', '尝试启动')
        start_ok, start_msg = self.start_service(service_name)

        if start_ok:
            self._log_operation(service_name, '重启', '成功')
            return True, f"服务 '{service_name}' 重启成功"
        else:
            self._log_operation(service_name, '重启', f'失败: {start_msg}')
            return False, f"重启失败: {start_msg}"

    def get_service_status(self, service_name):
        """查询单个服务状态"""
        try:
            svc = psutil.win_service_get(service_name)
            info = svc.as_dict()
            return {
                'name': info.get('name', ''),
                'display_name': info.get('display_name', ''),
                'status': info.get('status', ''),
                'start_type': info.get('start_type', ''),
                'pid': str(info.get('pid', '')),
                'description': info.get('description', '')
            }
        except Exception as e:
            return {'name': service_name, 'status': f'查询失败: {str(e)}'}

    def _log_operation(self, service_name, action, result):
        """记录操作日志"""
        entry = {
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'service': service_name,
            'action': action,
            'result': result
        }
        self._operation_log.append(entry)

    def get_operation_logs(self):
        """获取操作日志"""
        return list(self._operation_log)

    def clear_logs(self):
        """清空日志"""
        self._operation_log.clear()

# ---------------- Wi-Fi / 局域网信息 ----------------
class WifiManager:
    def __init__(self):
        self.encoding = locale.getpreferredencoding()

    def get_wifi_networks(self):
        """获取周边Wi-Fi网络列表（含信号强度）"""
        networks = []
        try:
            encodings_to_try = ['gbk', 'utf-8', 'cp936', locale.getpreferredencoding(), 'latin-1']
            output = None
            for enc in encodings_to_try:
                try:
                    result = subprocess.run(
                        ['netsh', 'wlan', 'show', 'networks', 'mode=Bssid'],
                        capture_output=True, text=True, encoding=enc, errors='ignore', timeout=10 # 增加超时
                    )
                    if result.returncode == 0 and result.stdout:
                        output = result.stdout
                        break
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
                except Exception:
                    continue

            if not output:
                return []

            current = {}
            for line in output.splitlines():
                line = line.strip()
                # SSID - 匹配 "SSID x :" 或 "SSID :"
                if re.match(r'^(?:SSID\s*\d+\s*|SSID)\s*:', line, re.IGNORECASE):
                    if current.get('ssid'): # 如果已经有一个 SSID，说明是新网络
                        networks.append(current)
                        current = {} # 重置
                    current['ssid'] = line.split(':', 1)[1].strip() if ':' in line else ''
                # 信号
                elif re.search(r'(?:信号|Signal)\s*:', line, re.IGNORECASE):
                    val = line.split(':', 1)[1].strip() if ':' in line else ''
                    current['signal'] = val
                # 认证
                elif re.search(r'(?:身份验证|Authentication)\s*:', line, re.IGNORECASE):
                    val = line.split(':', 1)[1].strip() if ':' in line else ''
                    current['auth'] = val
                # 加密
                elif re.search(r'(?:加密|Cipher)\s*:', line, re.IGNORECASE):
                    val = line.split(':', 1)[1].strip() if ':' in line else ''
                    current['cipher'] = val
                # BSSID (MAC) - 匹配 "BSSID :" 后面跟MAC地址，且不是 "BSSID 1" 等列表项
                elif re.search(r'BSSID\s*:', line, re.IGNORECASE) and 'BSSID 1' not in line and re.search(r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}', line):
                    current['bssid'] = line.split(':', 1)[1].strip()
                # 频道
                elif re.search(r'(?:频道|Channel)\s*:', line, re.IGNORECASE):
                    val = line.split(':', 1)[1].strip() if ':' in line else ''
                    current['channel'] = val

            if current.get('ssid'): # 添加最后一个网络
                networks.append(current)

        except Exception as e:
            networks.append({'ssid': f'获取失败: {str(e)}', 'signal': '', 'auth': '', 'cipher': '', 'bssid': '', 'channel': ''})

        return networks

    def get_current_wifi(self):
        """获取当前连接的Wi-Fi详细信息"""
        try:
            encodings_to_try = ['gbk', 'utf-8', 'cp936', locale.getpreferredencoding(), 'latin-1']
            output = None
            for enc in encodings_to_try:
                try:
                    result = subprocess.run(
                        ['netsh', 'wlan', 'show', 'interfaces'],
                        capture_output=True, text=True, encoding=enc, errors='ignore', timeout=10 # 增加超时
                    )
                    if result.returncode == 0 and result.stdout:
                        output = result.stdout
                        break
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
                except Exception:
                    continue

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
        """获取局域网设备列表（ARP表，含IP和MAC）"""
        devices = []
        try:
            encodings_to_try = ['gbk', 'utf-8', 'cp936', locale.getpreferredencoding(), 'latin-1']
            output = None
            for enc in encodings_to_try:
                try:
                    # 使用 ping 来更新 ARP 缓存，以获取更完整的设备列表
                    # 先 ping 广播地址（例如 192.168.1.255），可能需要几秒
                    # subprocess.run(['ping', '-n', '1', '192.168.1.255'], capture_output=True, timeout=5)

                    result = subprocess.run(
                        ['arp', '-a'],
                        capture_output=True, text=True, encoding=enc, errors='ignore', timeout=10 # 增加超时
                    )
                    if result.returncode == 0 and result.stdout:
                        output = result.stdout
                        break
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
                except Exception:
                    continue

            if not output:
                return []

            for line in output.splitlines():
                line = line.strip()
                # 匹配 IP MAC 类型
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
                    # 尝试解析主机名
                    hostname = ''
                    try:
                        # 对于每个IP进行反向DNS查询可能非常耗时，且容易失败
                        # 建议在UI层面异步处理或仅对部分IP进行
                        # hostname = socket.gethostbyaddr(ip)[0]
                        pass # 暂时禁用，避免卡顿
                    except Exception:
                        pass
                    devices.append({
                        'ip': ip,
                        'mac': mac,
                        'type': dev_type,
                        'hostname': hostname
                    })

        except Exception as e:
            devices.append({'ip': f'获取失败: {str(e)}', 'mac': '', 'type': '', 'hostname': ''})

        return devices

    def get_signal_bar(self, signal_str):
        """将信号百分比转换为ASCII信号条"""
        try:
            # 兼容 "XX%" 和 "XX"
            if '%' in signal_str:
                pct = int(signal_str.replace('%', '').strip())
            else:
                pct = int(signal_str.strip())

            bars = pct // 20  # 0-5格
            filled = '█' * bars
            empty = '░' * (5 - bars)
            return f"{filled}{empty} {pct}%"
        except Exception:
            return signal_str

# ---------------- 版本检查与自动更新（模拟） ----------------
class VersionChecker:
    def __init__(self, current_version, update_check_url):
        self.current_version = current_version
        self.update_check_url = update_check_url

    def check_for_updates(self):
        """
        检查是否有新版本可用。
        update_check_url 应指向 GitHub Releases API 或自定义的JSON接口。
        例如：https://api.github.com/repos/你的GitHub用户名/你的仓库名/releases/latest
        """
        try:
            response = requests.get(self.update_check_url, timeout=5)
            response.raise_for_status() # 对非200状态码抛出异常
            latest_release = response.json()

            latest_version = latest_release.get('tag_name', '').lstrip('vV') # 移除可能的 'v' 前缀
            release_notes = latest_release.get('body', '无更新说明')
            download_url = latest_release.get('html_url', '#') # 通常是GitHub Release页面链接

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
        """
        比较两个版本号字符串。
        如果 v1 > v2 返回正数
        如果 v1 < v2 返回负数
        如果 v1 == v2 返回 0
        """
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split('.')]
        return tuple(normalize(v1)) > tuple(normalize(v2)) - tuple(normalize(v1)) < tuple(normalize(v2)) or 0
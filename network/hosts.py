import shutil
import datetime
import time


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
            for attempt in range(3):
                try:
                    with open(self.hosts_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line_strip = line.strip()
                            if line_strip and not line_strip.startswith("#"):
                                parts = line_strip.split()
                                if len(parts) >= 2 and parts[1].lower() == domain.lower():
                                    deleted = True
                                    continue
                            lines.append(line)
                    break
                except IOError:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        raise
            if deleted:
                time.sleep(0.2)
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
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.hosts_file + f".backup_{timestamp}"
            shutil.copy2(self.hosts_file, backup_file)
            return True, f"备份成功: {backup_file}"
        except Exception as e:
            return False, f"备份失败: {str(e)}"

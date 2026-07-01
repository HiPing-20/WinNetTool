import psutil
import datetime
import time

from .base import run_hidden_cmd, get_system_encoding


class ServiceManager:
    def __init__(self):
        self.encoding = get_system_encoding()
        self._operation_log = []

    def _run_sc(self, args):
        """执行 sc 命令并处理编码"""
        cmd = ['sc'] + args
        for enc in [self.encoding, 'utf-8', 'latin-1']:
            try:
                result = run_hidden_cmd(
                    cmd,
                    capture_output=True, text=True, encoding=enc, errors='replace'
                )
                if result.returncode == 0:
                    return result
            except Exception:
                continue
        # 兜底
        return run_hidden_cmd(
            cmd,
            capture_output=True, text=True, encoding=self.encoding, errors='ignore'
        )

    def get_services(self):
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
                except (psutil.NoSuchProcess, psutil.AccessDenied):
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
        try:
            result = self._run_sc(['start', service_name])
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
        try:
            result = self._run_sc(['stop', service_name])
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
        self._log_operation(service_name, '重启', '尝试停止')
        stop_ok, stop_msg = self.stop_service(service_name)
        time.sleep(1)
        self._log_operation(service_name, '重启', '尝试启动')
        start_ok, start_msg = self.start_service(service_name)
        if start_ok:
            self._log_operation(service_name, '重启', '成功')
            return True, f"服务 '{service_name}' 重启成功"
        else:
            self._log_operation(service_name, '重启', f'失败: {start_msg}')
            return False, f"重启失败: {start_msg}"

    def get_service_status(self, service_name):
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
        entry = {
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'service': service_name,
            'action': action,
            'result': result
        }
        self._operation_log.append(entry)

    def get_operation_logs(self):
        return list(self._operation_log)

    def clear_logs(self):
        self._operation_log.clear()

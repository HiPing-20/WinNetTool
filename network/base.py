import subprocess
import locale
import os


def get_system_encoding():
    """获取系统实际编码，优先使用环境变量，其次用 locale"""
    # Windows 系统命令输出使用系统代码页（GBK/CP936）
    env_enc = os.environ.get('PYTHONIOENCODING', '')
    if env_enc:
        return env_enc
    pref = locale.getpreferredencoding()
    # 强制使用系统代码页，避免 PyInstaller 打包后 locale 返回错误值
    if pref and pref.lower() not in ('utf-8', 'utf8'):
        return pref
    # 如果 locale 返回 utf-8（PyInstaller 可能如此），硬编码为 gbk
    try:
        import ctypes
        codepage = ctypes.windll.kernel32.GetACP()
        return f'cp{codepage}'
    except Exception:
        return 'gbk'


# 模块级缓存，避免重复调用
_system_encoding = None


def run_hidden_cmd(cmd, **kwargs):
    global _system_encoding
    if _system_encoding is None:
        _system_encoding = get_system_encoding()

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    if 'capture_output' not in kwargs:
        kwargs['capture_output'] = True
    if 'text' not in kwargs:
        kwargs['text'] = True
    if 'encoding' not in kwargs:
        kwargs['encoding'] = _system_encoding
    if 'errors' not in kwargs:
        kwargs['errors'] = 'replace'
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30
    return subprocess.run(
        cmd,
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs
    )


def get_preferred_encoding():
    return get_system_encoding()

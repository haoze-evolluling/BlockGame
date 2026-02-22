import sys
import os
import winreg
import ctypes
import subprocess
from pathlib import Path


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def add_to_startup_registry(exe_path):
    """添加到注册表开机自启动（静默启动）"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NetworkController", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        return True
    except:
        return False


def create_vbs_launcher(exe_path):
    """创建VBS启动器实现完全静默"""
    vbs_path = os.path.join(os.path.dirname(exe_path), "launcher.vbs")
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{exe_path}" & chr(34), 0
Set WshShell = Nothing
'''
    try:
        with open(vbs_path, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        return vbs_path
    except:
        return None


def setup_autostart():
    """首次运行设置"""
    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    
    if add_to_startup_registry(exe_path):
        flag_file = os.path.join(os.path.dirname(exe_path), ".installed")
        with open(flag_file, 'w') as f:
            f.write("installed")
        return True
    return False


def check_first_run():
    """检查是否首次运行"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    
    flag_file = os.path.join(exe_dir, ".installed")
    return not os.path.exists(flag_file)


def main():
    if check_first_run():
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, 
                f'"{os.path.abspath(__file__)}"', None, 1
            )
            sys.exit(0)
        
        setup_autostart()
    
    from backend.server import app, initialize_network
    initialize_network()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()

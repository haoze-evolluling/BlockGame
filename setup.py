import sys
import os
import winreg
import ctypes
import shutil
import subprocess
from pathlib import Path


def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_exe_dir():
    """获取程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_install_dir():
    """获取安装目录"""
    program_files = os.environ.get('ProgramFiles', r'C:\Program Files')
    return os.path.join(program_files, 'NetworkController')


def is_installed():
    """检查程序是否已正确安装"""
    exe_dir = get_exe_dir()
    install_dir = get_install_dir()
    flag_file = os.path.join(install_dir, ".installed")
    
    # 检查是否在安装目录且存在标记文件
    return (exe_dir.lower() == install_dir.lower() and 
            os.path.exists(flag_file))


def install_to_program_files():
    """安装程序到Program Files目录"""
    source_dir = get_exe_dir()
    install_dir = get_install_dir()
    exe_name = 'NetworkController.exe'
    source_exe = os.path.join(source_dir, exe_name)
    target_exe = os.path.join(install_dir, exe_name)
    
    # 如果已经在安装目录，跳过
    if source_dir.lower() == install_dir.lower():
        return True, target_exe
    
    try:
        # 创建安装目录
        os.makedirs(install_dir, exist_ok=True)
        
        # 复制主程序
        if os.path.exists(source_exe):
            shutil.copy2(source_exe, target_exe)
        else:
            print(f"错误：找不到主程序 {source_exe}")
            return False, None
        
        # 复制backend目录
        source_backend = os.path.join(source_dir, 'backend')
        target_backend = os.path.join(install_dir, 'backend')
        if os.path.exists(source_backend):
            if os.path.exists(target_backend):
                shutil.rmtree(target_backend)
            shutil.copytree(source_backend, target_backend)
        
        # 复制frontend目录
        source_frontend = os.path.join(source_dir, 'frontend')
        target_frontend = os.path.join(install_dir, 'frontend')
        if os.path.exists(source_frontend):
            if os.path.exists(target_frontend):
                shutil.rmtree(target_frontend)
            shutil.copytree(source_frontend, target_frontend)
        
        # 创建卸载程序
        create_uninstaller(install_dir)
        
        return True, target_exe
    except Exception as e:
        print(f"安装失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def create_uninstaller(install_dir):
    """创建卸载程序"""
    uninstaller_path = os.path.join(install_dir, 'uninstall.bat')
    uninstaller_content = f'''@echo off
echo 正在卸载网络控制器...
taskkill /F /IM NetworkController.exe 2>nul
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v NetworkController /f >nul 2>&1
timeout /t 2 /nobreak >nul
rd /s /q "{install_dir}"
echo 卸载完成！
pause
'''
    with open(uninstaller_path, 'w', encoding='gbk') as f:
        f.write(uninstaller_content)


def add_to_startup_registry(exe_path):
    """添加到注册表开机自启动"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NetworkController", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        print(f"已设置开机自启动: {exe_path}")
        return True
    except Exception as e:
        print(f"设置自启动失败: {e}")
        return False


def remove_from_startup_registry():
    """从注册表移除开机自启动"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, "NetworkController")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"移除自启动失败: {e}")
        return False


def create_installed_flag(install_dir):
    """创建安装标记文件"""
    flag_file = os.path.join(install_dir, ".installed")
    try:
        with open(flag_file, 'w') as f:
            f.write("installed")
        return True
    except Exception as e:
        print(f"创建标记文件失败: {e}")
        return False


def run_installed_program(exe_path):
    """运行已安装的程序"""
    try:
        # 使用STARTUPINFO隐藏窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        
        subprocess.Popen(
            [exe_path],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return True
    except Exception as e:
        print(f"启动程序失败: {e}")
        return False


def run_server():
    """运行服务器"""
    exe_dir = get_exe_dir()
    
    # 设置工作目录为程序所在目录
    os.chdir(exe_dir)
    
    # 添加程序目录到Python路径
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)
    
    # 添加backend目录到Python路径
    backend_path = os.path.join(exe_dir, 'backend')
    if os.path.exists(backend_path) and backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
        from backend.server import app, initialize_network
        initialize_network()
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    # 检查是否有管理员权限
    if not is_admin():
        print("需要管理员权限进行安装...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f'"{os.path.abspath(__file__)}"', None, 1
        )
        sys.exit(0)
    
    # 检查是否已安装
    if not is_installed():
        print("首次运行，正在安装到Program Files...")
        success, installed_exe = install_to_program_files()
        if success:
            print(f"安装完成: {installed_exe}")
            
            # 设置开机自启动
            add_to_startup_registry(installed_exe)
            
            # 创建安装标记
            create_installed_flag(get_install_dir())
            
            # 启动已安装的程序
            print("正在启动服务...")
            run_installed_program(installed_exe)
            
            # 退出当前程序
            sys.exit(0)
        else:
            print("安装失败，继续使用当前路径运行...")
    
    # 运行服务器
    run_server()


if __name__ == '__main__':
    main()

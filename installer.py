"""
网络控制器安装程序
将exe安装到系统目录并设置开机自启
"""
import os
import sys
import shutil
import winreg
import ctypes
from pathlib import Path

def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """请求管理员权限"""
    if not is_admin():
        print("需要管理员权限，正在请求...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

def install_service():
    """安装服务"""
    print("🚀 网络控制器安装程序\n")
    
    # 检查管理员权限
    request_admin()
    
    # 安装路径
    install_dir = Path(os.getenv('ProgramFiles')) / 'NetworkController'
    install_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制exe文件
    exe_name = 'NetworkController.exe'
    current_dir = Path(__file__).parent
    source_exe = current_dir / 'dist' / exe_name
    target_exe = install_dir / exe_name
    
    if not source_exe.exists():
        print(f"❌ 找不到 {source_exe}")
        print("请先运行: python build.py")
        input("按回车键退出...")
        return
    
    print(f"📦 复制文件到: {install_dir}")
    shutil.copy2(source_exe, target_exe)
    
    # 设置开机自启动（注册表方式）
    print("⚙️ 设置开机自启动...")
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "NetworkController", 0, winreg.REG_SZ, str(target_exe))
        winreg.CloseKey(key)
        print("✅ 开机自启动设置成功")
    except Exception as e:
        print(f"❌ 设置开机自启动失败: {e}")
    
    # 创建卸载程序
    uninstaller_path = install_dir / 'uninstall.bat'
    uninstaller_content = f'''@echo off
echo 正在卸载网络控制器...
taskkill /F /IM NetworkController.exe 2>nul
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v NetworkController /f
timeout /t 2 /nobreak >nul
rd /s /q "{install_dir}"
echo 卸载完成！
pause
'''
    with open(uninstaller_path, 'w', encoding='gbk') as f:
        f.write(uninstaller_content)
    
    print(f"\n✨ 安装完成！")
    print(f"\n安装位置: {install_dir}")
    print(f"卸载程序: {uninstaller_path}")
    print("\n使用说明:")
    print("1. 程序已设置为开机自启动")
    print("2. 程序在后台隐藏运行")
    print("3. 浏览器访问: http://localhost:5000")
    print("4. 局域网访问: http://<本机IP>:5000")
    print("\n⚠️ 重要提示:")
    print("- 程序需要管理员权限才能修改网络设置")
    print("- 首次运行可能需要允许防火墙访问")
    
    # 询问是否立即启动
    choice = input("\n是否立即启动服务？(Y/n): ").strip().lower()
    if choice != 'n':
        print("\n🚀 正在启动服务...")
        os.startfile(target_exe)
        print("✅ 服务已启动")
    
    input("\n按回车键退出...")

if __name__ == '__main__':
    try:
        install_service()
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        input("按回车键退出...")

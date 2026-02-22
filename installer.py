"""
网络控制器安装程序
首次运行需要管理员权限
"""
import os
import sys
import shutil
import subprocess
import ctypes
import time


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{" ".join(sys.argv)}"', None, 1
        )
        sys.exit(0)


def get_resource_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(sys._MEIPASS, 'app')
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


def get_install_dir():
    program_files = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    return os.path.join(program_files, 'NetworkController')


def install():
    print("=" * 60)
    print("网络控制器安装程序")
    print("=" * 60)
    print()

    if not is_admin():
        print("需要管理员权限进行安装...")
        request_admin()
        return

    install_dir = get_install_dir()
    print(f"安装目录: {install_dir}")
    print()

    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
        print("✓ 创建安装目录")

    files_to_install = [
        ('NetworkController.exe', 'NetworkController.exe'),
        ('index.html', 'index.html'),
    ]

    for src_name, dst_name in files_to_install:
        try:
            src_path = get_resource_path(src_name)
            dst_path = os.path.join(install_dir, dst_name)
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                print(f"✓ 安装: {dst_name}")
            else:
                print(f"⚠ 未找到: {src_name}")
        except Exception as e:
            print(f"✗ 复制 {src_name} 失败: {e}")

    print()

    exe_path = os.path.join(install_dir, 'NetworkController.exe')
    if os.path.exists(exe_path):
        subprocess.run([exe_path, 'install'], check=False)

    print()
    print("=" * 60)
    print("安装完成！")
    print("=" * 60)
    print()
    print("使用说明:")
    print("- 访问 http://<本机IP>:5000 打开控制界面")
    print("- 服务已设置为开机自动启动")
    print(f"- 安装目录: {install_dir}")
    print()
    print("管理命令:")
    print(f"  {exe_path} install    - 安装服务")
    print(f"  {exe_path} uninstall  - 卸载服务")
    print(f"  {exe_path} start      - 启动服务")
    print(f"  {exe_path} stop       - 停止服务")
    print(f"  {exe_path} status     - 查看状态")
    print()

    try:
        subprocess.Popen(['cmd', '/c', 'start', 'http://localhost:5000'])
    except:
        pass

    input("按回车键退出...")


if __name__ == '__main__':
    install()

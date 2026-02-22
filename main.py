import os
import sys
import ctypes
import subprocess


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """以管理员权限重新启动程序"""
    script_path = os.path.abspath(sys.argv[0])
    params = ' '.join(sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}" {params}', None, 1)


def main():
    """主程序入口"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    server_script = os.path.join(backend_dir, 'server.py')
    
    if not os.path.exists(server_script):
        print(f"错误：找不到服务器脚本 {server_script}")
        input("按回车键退出...")
        sys.exit(1)
    
    print("=" * 50)
    print("网络控制器服务启动中...")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, server_script], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败：{e}")
        input("按回车键退出...")


if __name__ == '__main__':
    if not is_admin():
        print("需要管理员权限，正在申请...")
        run_as_admin()
        sys.exit(0)
    
    main()

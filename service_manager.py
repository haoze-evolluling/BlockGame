"""
Windows服务管理工具
使用sc命令管理服务，无需复杂的pywin32服务框架
"""
import subprocess
import sys
import os
import ctypes
import time


def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin():
    """请求管理员权限"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{" ".join(sys.argv)}"', None, 1
        )
        sys.exit(0)


def get_service_exe_path():
    """获取服务可执行文件路径"""
    # 默认安装路径
    program_files = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    default_path = os.path.join(program_files, 'NetworkController', 'NetworkController.exe')
    
    if os.path.exists(default_path):
        return default_path
    
    # 当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(current_dir, 'NetworkController.exe')
    
    if os.path.exists(local_path):
        return local_path
    
    return None


def install_service():
    """安装服务"""
    exe_path = get_service_exe_path()
    if not exe_path:
        print("✗ 未找到 NetworkController.exe")
        print("  请确保程序已正确安装")
        return False
    
    try:
        service_name = "NetworkController"
        display_name = "网络控制器服务"
        
        # 先停止并删除已存在的服务
        subprocess.run(['sc', 'stop', service_name], capture_output=True)
        time.sleep(1)
        subprocess.run(['sc', 'delete', service_name], capture_output=True)
        time.sleep(1)
        
        # 创建服务
        cmd = [
            'sc', 'create', service_name,
            'binPath=', f'"{exe_path}"',
            'DisplayName=', display_name,
            'start=', 'auto',
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            if '已存在' in result.stderr or '已存在' in result.stdout:
                print(f"✓ 服务已存在")
            else:
                print(f"创建服务输出: {result.stdout}")
                if result.stderr:
                    print(f"提示: {result.stderr}")
        else:
            print(f"✓ 服务 '{display_name}' 创建成功")
        
        # 设置服务描述
        subprocess.run(
            ['sc', 'description', service_name, '提供网络控制和Web管理界面服务'],
            capture_output=True
        )
        
        # 配置服务失败后自动重启
        subprocess.run(
            ['sc', 'failure', service_name, 'reset=', '86400', 'actions=', 'restart/5000/restart/10000/restart/30000'],
            capture_output=True
        )
        
        print("✓ 已设置为开机自动启动")
        return True
        
    except Exception as e:
        print(f"✗ 服务安装失败: {e}")
        return False


def remove_service():
    """卸载服务"""
    try:
        service_name = "NetworkController"
        
        # 先停止服务
        stop_service()
        time.sleep(1)
        
        # 删除服务
        result = subprocess.run(['sc', 'delete', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 服务已卸载")
            return True
        elif '指定的服务未安装' in result.stderr:
            print("服务未安装")
            return True
        else:
            print(f"卸载输出: {result.stdout}")
            if result.stderr:
                print(f"提示: {result.stderr}")
            return True
            
    except Exception as e:
        print(f"✗ 服务卸载失败: {e}")
        return False


def start_service():
    """启动服务"""
    try:
        service_name = "NetworkController"
        result = subprocess.run(['sc', 'start', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 服务已启动")
            return True
        elif '已经启动' in result.stdout or '已经启动' in result.stderr:
            print("服务已在运行")
            return True
        else:
            print(f"启动输出: {result.stdout}")
            if result.stderr:
                print(f"提示: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 启动服务失败: {e}")
        return False


def stop_service():
    """停止服务"""
    try:
        service_name = "NetworkController"
        result = subprocess.run(['sc', 'stop', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 服务已停止")
            return True
        elif '未启动' in result.stdout or '未启动' in result.stderr:
            print("服务未在运行")
            return True
        else:
            return True
            
    except Exception as e:
        print(f"✗ 停止服务失败: {e}")
        return False


def check_service_status():
    """检查服务状态"""
    try:
        service_name = "NetworkController"
        result = subprocess.run(['sc', 'query', service_name], capture_output=True, text=True)
        
        if result.returncode != 0:
            return "未安装"
        
        output = result.stdout
        if 'RUNNING' in output:
            return "运行中"
        elif 'STOPPED' in output:
            return "已停止"
        elif 'START_PENDING' in output:
            return "正在启动"
        elif 'STOP_PENDING' in output:
            return "正在停止"
        else:
            return "未知"
            
    except Exception as e:
        return f"查询失败: {e}"


def show_help():
    """显示帮助信息"""
    print("网络控制器服务管理工具")
    print("=" * 50)
    print()
    print("用法: ServiceManager.exe [命令]")
    print()
    print("命令:")
    print("  install   安装并启动服务")
    print("  remove    停止并卸载服务")
    print("  start     启动服务")
    print("  stop      停止服务")
    print("  status    查看服务状态")
    print("  restart   重启服务")
    print()
    print(f"当前状态: {check_service_status()}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'install':
        request_admin()
        if install_service():
            time.sleep(1)
            start_service()
            print()
            print("安装完成！访问 http://localhost:5000 使用")
            
    elif command == 'remove':
        request_admin()
        remove_service()
        
    elif command == 'start':
        request_admin()
        start_service()
        
    elif command == 'stop':
        request_admin()
        stop_service()
        
    elif command == 'restart':
        request_admin()
        stop_service()
        time.sleep(2)
        start_service()
        
    elif command == 'status':
        print(f"服务状态: {check_service_status()}")
        
    else:
        print(f"未知命令: {command}")
        show_help()


if __name__ == '__main__':
    main()

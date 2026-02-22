"""
网络控制器安装程序
首次运行需要管理员权限，用于注册系统服务
"""
import os
import sys
import shutil
import subprocess
import ctypes
import time
import tempfile


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


def get_resource_path(filename):
    """获取资源文件路径（支持打包后的环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境，资源在_MEIPASS/app目录中
        base_path = os.path.join(sys._MEIPASS, 'app')
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


def get_install_dir():
    """获取安装目录"""
    # 安装到Program Files
    program_files = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    install_dir = os.path.join(program_files, 'NetworkController')
    return install_dir


def install_service(exe_path):
    """使用sc命令注册Windows服务"""
    try:
        service_name = "NetworkController"
        display_name = "网络控制器服务"
        
        # 先删除已存在的服务
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
            'type=', 'own'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and '已存在' not in result.stderr:
            print(f"创建服务警告: {result.stderr}")
        
        # 设置服务描述
        subprocess.run([
            'sc', 'description', service_name,
            '提供网络控制和Web管理界面服务'
        ], capture_output=True)
        
        # 配置服务失败后自动重启
        subprocess.run([
            'sc', 'failure', service_name,
            'reset=', '86400',
            'actions=', 'restart/5000/restart/10000/restart/30000'
        ], capture_output=True)
        
        print(f"✓ 服务 '{display_name}' 注册成功")
        return True
        
    except Exception as e:
        print(f"✗ 服务注册失败: {e}")
        return False


def start_service():
    """启动服务"""
    try:
        service_name = "NetworkController"
        result = subprocess.run(['sc', 'start', service_name], capture_output=True, text=True)
        if result.returncode == 0 or '已经启动' in result.stdout:
            print(f"✓ 服务已启动")
            return True
        else:
            print(f"启动服务: {result.stdout}")
            return True
    except Exception as e:
        print(f"✗ 启动服务失败: {e}")
        return False


def check_service_status():
    """检查服务状态"""
    try:
        result = subprocess.run(['sc', 'query', 'NetworkController'], capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            return "运行中"
        elif 'STOPPED' in result.stdout:
            return "已停止"
        elif 'START_PENDING' in result.stdout:
            return "正在启动"
        else:
            return "未安装"
    except:
        return "未知"


def install():
    """执行安装"""
    print("=" * 60)
    print("网络控制器安装程序")
    print("=" * 60)
    print()
    
    # 检查管理员权限
    if not is_admin():
        print("需要管理员权限进行安装...")
        request_admin()
        return
    
    install_dir = get_install_dir()
    print(f"安装目录: {install_dir}")
    print()
    
    # 创建安装目录
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
        print("✓ 创建安装目录")
    
    # 复制文件
    files_to_install = [
        ('NetworkController.exe', 'NetworkController.exe'),
        ('ServiceManager.exe', 'ServiceManager.exe'),
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
    
    # 注册服务
    exe_path = os.path.join(install_dir, 'NetworkController.exe')
    if os.path.exists(exe_path):
        if install_service(exe_path):
            time.sleep(1)
            start_service()
    
    print()
    print("=" * 60)
    print("安装完成！")
    print("=" * 60)
    print()
    print("服务状态:", check_service_status())
    print()
    print("使用说明:")
    print("- 访问 http://localhost:5000 打开控制界面")
    print("- 服务已设置为开机自动启动")
    print("- 安装目录:", install_dir)
    print()
    print("管理服务:")
    print(f"  {install_dir}\\ServiceManager.exe stop    - 停止服务")
    print(f"  {install_dir}\\ServiceManager.exe start   - 启动服务")
    print(f"  {install_dir}\\ServiceManager.exe remove  - 卸载服务")
    print()
    
    # 打开浏览器
    try:
        subprocess.Popen(['cmd', '/c', 'start', 'http://localhost:5000'])
    except:
        pass
    
    input("按回车键退出...")


def main():
    """主函数"""
    try:
        install()
    except Exception as e:
        print(f"安装过程出错: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == '__main__':
    main()

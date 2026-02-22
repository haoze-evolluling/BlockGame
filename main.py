"""
网络控制器 - 集成服务管理版本
支持：Windows服务、局域网控制
"""
import subprocess
import os
import sys
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ctypes

SERVICE_NAME = "NetworkController"
SERVICE_DISPLAY = "网络控制器服务"
SERVICE_DESC = "提供网络控制和Web管理界面服务"


class NetworkController:
    def __init__(self):
        self.current_loss = 0
        self._recovery_timer = None

    def set_packet_loss(self, loss_percent):
        try:
            return self._set_windows_loss(loss_percent)
        except Exception as e:
            return False, str(e)

    def _set_windows_loss(self, loss_percent):
        if self._recovery_timer:
            self._recovery_timer.cancel()
            self._recovery_timer = None

        if loss_percent == 100:
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Disable-NetAdapter -Confirm:$false"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent
            self._recovery_timer = threading.Timer(5.0, self._auto_recover_network)
            self._recovery_timer.start()
            return True, "已禁用所有网络适配器，5秒后自动恢复"

        elif loss_percent == 0:
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent
            return True, f"已设置丢包率为 {loss_percent}%"

        return False, "无效的丢包率"

    def get_status(self):
        return {"loss_percent": self.current_loss}

    def _auto_recover_network(self):
        try:
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = 0
            self._recovery_timer = None
        except:
            pass

app = Flask(__name__)
CORS(app)
controller = NetworkController()


def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_from_directory(get_exe_dir(), 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(controller.get_status())


@app.route('/api/set-loss', methods=['POST'])
def set_loss():
    data = request.json
    loss = data.get('loss', 0)
    if loss not in [0, 100]:
        return jsonify({'success': False, 'message': '无效的丢包率'}), 400
    success, message = controller.set_packet_loss(loss)
    return jsonify({'success': success, 'message': message})


# ============================================================================
# 服务管理功能
# ============================================================================

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


def get_exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(__file__)


def check_service_status():
    try:
        result = subprocess.run(
            ['sc', 'query', SERVICE_NAME],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
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
        return "未知"
    except Exception as e:
        return f"查询失败: {e}"


def install_service():
    exe_path = get_exe_path()
    try:
        subprocess.run(
            ['sc', 'stop', SERVICE_NAME],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(0.5)
        subprocess.run(
            ['sc', 'delete', SERVICE_NAME],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(0.5)

        cmd = [
            'sc', 'create', SERVICE_NAME,
            f'binPath="{exe_path}" service',
            f'DisplayName={SERVICE_DISPLAY}',
            'start=auto',
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0 and '已存在' not in result.stderr:
            print(f"创建服务警告: {result.stderr}")

        subprocess.run(
            ['sc', 'description', SERVICE_NAME, SERVICE_DESC],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            ['sc', 'failure', SERVICE_NAME, 'reset=86400', 'actions=restart/5000/restart/10000/restart/30000'],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(f"✓ 服务 '{SERVICE_DISPLAY}' 安装成功")
        print("✓ 已设置为开机自动启动")
        return True
    except Exception as e:
        print(f"✗ 服务安装失败: {e}")
        return False


def uninstall_service():
    try:
        stop_service()
        time.sleep(0.5)
        result = subprocess.run(
            ['sc', 'delete', SERVICE_NAME],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 or '指定的服务未安装' in result.stderr:
            print("✓ 服务已卸载")
            return True
        print(f"卸载输出: {result.stdout}")
        return True
    except Exception as e:
        print(f"✗ 服务卸载失败: {e}")
        return False


def start_service():
    try:
        result = subprocess.run(
            ['sc', 'start', SERVICE_NAME],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 or '已经启动' in result.stdout:
            print("✓ 服务已启动")
            return True
        print(f"启动输出: {result.stdout}")
        return False
    except Exception as e:
        print(f"✗ 启动服务失败: {e}")
        return False


def stop_service():
    try:
        result = subprocess.run(
            ['sc', 'stop', SERVICE_NAME],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 or '未启动' in result.stdout:
            print("✓ 服务已停止")
            return True
        return True
    except Exception as e:
        print(f"✗ 停止服务失败: {e}")
        return False


def restart_service():
    stop_service()
    time.sleep(1)
    return start_service()


def show_help():
    print("网络控制器")
    print("=" * 50)
    print()
    print("用法: NetworkController.exe [命令]")
    print()
    print("命令:")
    print("  install     安装为Windows服务")
    print("  uninstall   卸载服务")
    print("  start       启动服务")
    print("  stop        停止服务")
    print("  restart     重启服务")
    print("  status      查看服务状态")
    print()
    print(f"当前状态: {check_service_status()}")
    print()
    print("安装后访问: http://<本机IP>:5000")


def enable_all_adapters():
    """启用所有网络适配器 - 使用WMI方式更可靠"""
    import logging
    logging.basicConfig(filename='c:\\net_service.log', level=logging.INFO)
    
    for attempt in range(3):
        try:
            logging.info(f"第{attempt+1}次尝试启用网络适配器...")
            
            # 方法1: 使用WMI（更底层，服务启动时更可靠）
            cmd = 'powershell -ExecutionPolicy Bypass -Command "& {Get-WmiObject Win32_NetworkAdapter | Where-Object {$_.NetEnabled -eq $false -and $_.PhysicalAdapter -eq $true} | ForEach-Object { $_.Enable() } }"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logging.info(f"WMI方式结果: {result.returncode}, stderr: {result.stderr}")
            
            # 方法2: 使用NetAdapter模块（作为备用）
            time.sleep(2)
            cmd2 = 'powershell -ExecutionPolicy Bypass -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logging.info(f"NetAdapter方式结果: {result2.returncode}, stderr: {result2.stderr}")
            
            logging.info("网络适配器启用命令已执行")
            return True
        except Exception as e:
            logging.error(f"启用网络适配器失败: {e}")
            time.sleep(3)
    return False


def run_server():
    # 延迟10秒执行，确保系统完全就绪
    threading.Timer(10.0, enable_all_adapters).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)


def main():
    if len(sys.argv) < 2:
        print("请使用命令参数运行")
        show_help()
        return

    command = sys.argv[1].lower()

    if command == 'service':
        run_server()
        return

    if command in ['install', 'uninstall', 'start', 'stop', 'restart']:
        request_admin()

    if command == 'install':
        if install_service():
            time.sleep(0.5)
            start_service()
            print()
            print("=" * 50)
            print("安装完成！")
            print("=" * 50)
            print("访问地址: http://<本机IP>:5000")

    elif command == 'uninstall':
        uninstall_service()

    elif command == 'start':
        start_service()

    elif command == 'stop':
        stop_service()

    elif command == 'restart':
        restart_service()

    elif command == 'status':
        print(f"服务状态: {check_service_status()}")

    elif command in ['help', '-h', '--help', '/?']:
        show_help()

    else:
        print(f"未知命令: {command}")
        show_help()


if __name__ == '__main__':
    main()

"""
网络控制器 - 集成服务管理版本
支持：独立运行、Windows服务、局域网控制
"""
import subprocess
import platform
import os
import sys
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ctypes
import logging


def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
        log_file = os.path.join(log_dir, 'network_controller.log')
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)
    return logging.getLogger(__name__)


logger = setup_logging()

SERVICE_NAME = "NetworkController"
SERVICE_DISPLAY = "网络控制器服务"
SERVICE_DESC = "提供网络控制和Web管理界面服务"


class NetworkController:
    def __init__(self):
        self.current_loss = 0
        self.system = platform.system()
        self._recovery_timer = None

    def set_packet_loss(self, loss_percent):
        try:
            if self.system == "Windows":
                return self._set_windows_loss(loss_percent)
            else:
                return self._set_linux_loss(loss_percent)
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
            self._recovery_timer = threading.Timer(30.0, self._auto_recover_network)
            self._recovery_timer.start()
            return True, "已禁用所有网络适配器，30秒后自动恢复"

        elif loss_percent == 0:
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent
            return True, f"已设置丢包率为 {loss_percent}%"

        return False, "无效的丢包率"

    def _set_linux_loss(self, loss_percent):
        interface = self._get_main_interface()
        if not interface:
            return False, "无法找到网络接口"
        subprocess.run(f"tc qdisc del dev {interface} root", shell=True, stderr=subprocess.DEVNULL)
        if loss_percent > 0:
            cmd = f"tc qdisc add dev {interface} root netem loss {loss_percent}%"
            subprocess.run(cmd, shell=True)
        self.current_loss = loss_percent
        return True, f"已设置丢包率为 {loss_percent}%"

    def _get_main_interface(self):
        try:
            result = subprocess.run("ip route | grep default | awk '{print $5}'",
                                  shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "eth0"

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

    def cleanup(self):
        if self._recovery_timer:
            self._recovery_timer.cancel()


def setup_environment():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        os.chdir(exe_dir)
        paths_to_add = [exe_dir, getattr(sys, '_MEIPASS', exe_dir)]
        for path in paths_to_add:
            if path and path not in sys.path:
                sys.path.insert(0, path)


setup_environment()
app = Flask(__name__)
CORS(app)
controller = NetworkController()


def initialize_network():
    """
    初始化网络状态
    重置控制器状态和取消残留定时器
    """
    try:
        # 重置控制器状态
        controller.current_loss = 0
        
        # 取消任何可能残留的定时器
        if controller._recovery_timer:
            controller._recovery_timer.cancel()
            controller._recovery_timer = None
        
        logger.info("网络初始化完成")
        return True
    except Exception as e:
        logger.error(f"网络初始化失败：{e}")
        return False


def get_frontend_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_from_directory(get_frontend_dir(), 'index.html')


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
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
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
    creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
    try:
        subprocess.run(
            ['sc', 'stop', SERVICE_NAME], 
            capture_output=True,
            creationflags=creation_flags
        )
        time.sleep(0.5)
        subprocess.run(
            ['sc', 'delete', SERVICE_NAME], 
            capture_output=True,
            creationflags=creation_flags
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
            creationflags=creation_flags
        )

        if result.returncode != 0 and '已存在' not in result.stderr:
            print(f"创建服务警告: {result.stderr}")

        subprocess.run(
            ['sc', 'description', SERVICE_NAME, SERVICE_DESC],
            capture_output=True,
            creationflags=creation_flags
        )
        subprocess.run(
            ['sc', 'failure', SERVICE_NAME, 'reset=86400', 'actions=restart/5000/restart/10000/restart/30000'],
            capture_output=True,
            creationflags=creation_flags
        )
        print(f"✓ 服务 '{SERVICE_DISPLAY}' 安装成功")
        print("✓ 已设置为开机自动启动")
        return True
    except Exception as e:
        print(f"✗ 服务安装失败: {e}")
        return False


def uninstall_service():
    creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
    try:
        stop_service()
        time.sleep(0.5)
        result = subprocess.run(
            ['sc', 'delete', SERVICE_NAME], 
            capture_output=True, 
            text=True,
            creationflags=creation_flags
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
    creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
    try:
        result = subprocess.run(
            ['sc', 'start', SERVICE_NAME], 
            capture_output=True, 
            text=True,
            creationflags=creation_flags
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
    creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
    try:
        result = subprocess.run(
            ['sc', 'stop', SERVICE_NAME], 
            capture_output=True, 
            text=True,
            creationflags=creation_flags
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
    print("  (无)        以独立模式运行Web服务器")
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


def run_server():
    initialize_network()
    logger.info("=" * 50)
    logger.info("网络控制器启动")
    logger.info("访问地址: http://0.0.0.0:5000")
    logger.info("=" * 50)
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}")
    finally:
        controller.cleanup()


def main():
    if len(sys.argv) < 2:
        if not is_admin():
            print("需要管理员权限运行网络控制功能...")
            request_admin()
            return
        run_server()
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

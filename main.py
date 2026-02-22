"""
网络控制器 - 服务版本
包含所有功能：网络控制、Web服务器、Windows服务支持
"""
import subprocess
import platform
import os
import sys
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import shutil
import winreg
import ctypes
from pathlib import Path
import logging


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 网络控制模块
# ============================================================================

class NetworkController:
    def __init__(self):
        self.current_loss = 0
        self.system = platform.system()
        self._recovery_timer = None

    def set_packet_loss(self, loss_percent):
        """设置丢包率：0% 或 100%"""
        try:
            if self.system == "Windows":
                return self._set_windows_loss(loss_percent)
            else:
                return self._set_linux_loss(loss_percent)
        except Exception as e:
            return False, str(e)

    def _set_windows_loss(self, loss_percent):
        """Windows系统直接禁用/启用网络适配器"""
        # 取消之前的恢复定时器
        if self._recovery_timer:
            self._recovery_timer.cancel()
            self._recovery_timer = None

        if loss_percent == 100:
            # 禁用所有网络适配器，30秒后自动恢复
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Disable-NetAdapter -Confirm:$false"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent

            # 启动定时器，30秒后自动恢复
            self._recovery_timer = threading.Timer(30.0, self._auto_recover_network)
            self._recovery_timer.start()

            return True, "已禁用所有网络适配器，30秒后自动恢复"

        elif loss_percent == 0:
            # 启用所有网络适配器
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent
            return True, f"已设置丢包率为 {loss_percent}%"

        return False, "无效的丢包率"

    def _set_linux_loss(self, loss_percent):
        """Linux系统使用tc命令"""
        interface = self._get_main_interface()
        if not interface:
            return False, "无法找到网络接口"

        # 清除现有规则
        subprocess.run(f"tc qdisc del dev {interface} root", shell=True, stderr=subprocess.DEVNULL)

        if loss_percent > 0:
            cmd = f"tc qdisc add dev {interface} root netem loss {loss_percent}%"
            subprocess.run(cmd, shell=True)

        self.current_loss = loss_percent
        return True, f"已设置丢包率为 {loss_percent}%"

    def _get_main_interface(self):
        """获取主网络接口"""
        try:
            result = subprocess.run("ip route | grep default | awk '{print $5}'",
                                  shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "eth0"

    def get_status(self):
        """获取当前状态"""
        return {"loss_percent": self.current_loss}

    def _auto_recover_network(self):
        """自动恢复网络适配器"""
        try:
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = 0
            self._recovery_timer = None
        except:
            pass

    def reboot_system(self):
        """重启系统"""
        try:
            if self.system == "Windows":
                subprocess.run("shutdown /r /t 0", shell=True)
                return True, "系统正在重启..."
            else:
                subprocess.run("reboot", shell=True)
                return True, "系统正在重启..."
        except Exception as e:
            return False, f"重启失败：{str(e)}"

    def cleanup(self):
        """清理资源"""
        if self._recovery_timer:
            self._recovery_timer.cancel()


# ============================================================================
# Web服务器模块
# ============================================================================

def setup_environment():
    """设置运行环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        exe_dir = os.path.dirname(sys.executable)
        os.chdir(exe_dir)
        paths_to_add = [
            exe_dir,
            getattr(sys, '_MEIPASS', exe_dir),
        ]
        for path in paths_to_add:
            if path and path not in sys.path:
                sys.path.insert(0, path)


setup_environment()

app = Flask(__name__)
CORS(app)

controller = NetworkController()


def initialize_network():
    """程序启动时初始化网络，启用所有网络适配器"""
    try:
        cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        controller.current_loss = 0
        logger.info("网络初始化完成：已启用所有网络适配器")
        return True
    except Exception as e:
        logger.error(f"网络初始化失败：{e}")
        return False


def get_frontend_dir():
    """获取前端目录路径"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    frontend_dir = get_frontend_dir()
    return send_from_directory(frontend_dir, 'index.html')


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


@app.route('/api/reboot', methods=['POST'])
def reboot():
    success, message = controller.reboot_system()
    return jsonify({'success': success, 'message': message})


# ============================================================================
# 服务运行支持
# ============================================================================

def run_server_as_service():
    """作为Windows服务运行服务器"""
    try:
        # 初始化网络
        initialize_network()
        
        logger.info("=" * 50)
        logger.info("网络控制器服务启动中...")
        logger.info("访问地址: http://localhost:5000")
        logger.info("=" * 50)
        
        # 使用waitress或其他WSGI服务器（更适合生产环境）
        # 这里继续使用Flask内置服务器，但禁用重载
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        controller.cleanup()


def run_server_standalone():
    """作为独立程序运行服务器"""
    try:
        # 检查管理员权限
        if not is_admin():
            request_admin()
            return
            
        # 初始化网络
        initialize_network()
        
        print("=" * 50)
        print("网络控制器服务启动中...")
        print("访问地址: http://localhost:5000")
        print("=" * 50)
        
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        controller.cleanup()


# ============================================================================
# 工具函数
# ============================================================================

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


# ============================================================================
# 主程序入口
# ============================================================================

def main():
    """主程序入口"""
    # 检查是否作为服务运行
    if os.environ.get('RUNNING_AS_SERVICE') == '1':
        run_server_as_service()
        return
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'service':
            # 服务模式运行
            run_server_as_service()
            return
    
    # 默认独立运行模式
    run_server_standalone()


if __name__ == '__main__':
    main()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import subprocess
import sys


def setup_environment():
    """设置运行环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        exe_dir = os.path.dirname(sys.executable)
        
        # 设置工作目录为exe所在目录
        os.chdir(exe_dir)
        
        # 添加各种可能的路径到Python路径
        paths_to_add = [
            exe_dir,
            os.path.join(exe_dir, 'backend'),
            getattr(sys, '_MEIPASS', exe_dir),
        ]
        
        for path in paths_to_add:
            if path and path not in sys.path:
                sys.path.insert(0, path)


# 初始化环境
setup_environment()

# 导入网络控制模块
try:
    from network_control import NetworkController
except ImportError:
    from backend.network_control import NetworkController

app = Flask(__name__)
CORS(app)

controller = NetworkController()


def initialize_network():
    """程序启动时初始化网络，启用所有网络适配器"""
    try:
        cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        controller.current_loss = 0
        print("网络初始化完成：已启用所有网络适配器")
        return True
    except Exception as e:
        print(f"网络初始化失败：{e}")
        return False


# 程序启动时执行网络初始化
initialize_network()


def get_frontend_dir():
    """获取前端目录路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境 - 优先检查exe所在目录
        exe_dir = os.path.dirname(sys.executable)
        frontend_dir = os.path.join(exe_dir, 'frontend')
        if os.path.exists(frontend_dir):
            return frontend_dir
        
        # 尝试_MEIPASS路径（PyInstaller解压路径）
        meipass_path = getattr(sys, '_MEIPASS', None)
        if meipass_path:
            frontend_dir = os.path.join(meipass_path, 'frontend')
            if os.path.exists(frontend_dir):
                return frontend_dir
    
    # 开发环境
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(current_dir), 'frontend')


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


if __name__ == '__main__':
    # 0.0.0.0 允许局域网访问
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        controller.cleanup()

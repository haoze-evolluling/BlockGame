from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from network_control import NetworkController
import os
import sys

# 获取资源文件路径（支持PyInstaller打包）
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

app = Flask(__name__)
CORS(app)

controller = NetworkController()

@app.route('/')
def index():
    html_path = get_resource_path('frontend')
    return send_from_directory(html_path, 'index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(controller.get_status())

@app.route('/api/set-loss', methods=['POST'])
def set_loss():
    data = request.json
    loss = data.get('loss', 0)
    
    if loss not in [0, 50, 100]:
        return jsonify({'success': False, 'message': '无效的丢包率'}), 400
    
    success, message = controller.set_packet_loss(loss)
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    # 0.0.0.0 允许局域网访问
    app.run(host='0.0.0.0', port=5000, debug=False)

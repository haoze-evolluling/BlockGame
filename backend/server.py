from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from network_control import NetworkController
import os

app = Flask(__name__)
CORS(app)

controller = NetworkController()

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

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

if __name__ == '__main__':
    # 0.0.0.0 允许局域网访问
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        controller.cleanup()

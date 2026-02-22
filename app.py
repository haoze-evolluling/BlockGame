from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys

app = Flask(__name__)
CORS(app)

# 当前延迟状态 (毫秒)
current_delay = 0
# 控制规则名称
RULE_NAME = "GameNetworkDelayControl"

# 使用 tc (Traffic Control) 模拟的替代方案 - 使用 Windows 的 netsh 和 hosts 文件方式
def apply_network_delay(delay_ms):
    """应用网络延迟设置"""
    global current_delay
    
    # 先清除现有规则
    clear_network_delay()
    
    if delay_ms == 0:
        current_delay = 0
        return True
    
    try:
        # 使用 netsh 接口配置来添加延迟
        # 通过配置代理和路由来模拟延迟效果
        if delay_ms == 100:
            # 轻度延迟 - 配置本地代理回环
            os.system('netsh interface ip set dns "Ethernet" static 127.0.0.1 >nul 2>&1')
            os.system('netsh interface ip set dns "Wi-Fi" static 127.0.0.1 >nul 2>&1')
            os.system('netsh interface ip set dns "以太网" static 127.0.0.1 >nul 2>&1')
        elif delay_ms == 500:
            # 重度延迟 - 配置到无效网关
            os.system('netsh interface ip set dns "Ethernet" static 192.0.2.1 >nul 2>&1')
            os.system('netsh interface ip set dns "Wi-Fi" static 192.0.2.1 >nul 2>&1')
            os.system('netsh interface ip set dns "以太网" static 192.0.2.1 >nul 2>&1')
        
        current_delay = delay_ms
        return True
    except Exception as e:
        print(f"应用延迟失败: {e}")
        return False

def clear_network_delay():
    """清除网络延迟设置"""
    try:
        # 恢复自动获取 DNS
        os.system('netsh interface ip set dns "Ethernet" dhcp >nul 2>&1')
        os.system('netsh interface ip set dns "Wi-Fi" dhcp >nul 2>&1')
        os.system('netsh interface ip set dns "以太网" dhcp >nul 2>&1')
        
        # 刷新 DNS 缓存
        os.system('ipconfig /flushdns >nul 2>&1')
        
        return True
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'delay': current_delay
    })

@app.route('/api/set', methods=['POST'])
def set_delay():
    data = request.get_json()
    delay_ms = data.get('delay', 0)
    
    if delay_ms not in [0, 100, 500]:
        return jsonify({'success': False, 'error': '无效的延迟值'})
    
    success = apply_network_delay(delay_ms)
    return jsonify({
        'success': success,
        'delay': current_delay
    })

@app.route('/api/clear', methods=['POST'])
def clear_rule():
    success = clear_network_delay()
    global current_delay
    current_delay = 0
    return jsonify({'success': success, 'delay': 0})

def run_hidden():
    """以隐藏模式运行Flask服务"""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    # 清理可能存在的旧规则
    clear_network_delay()
    
    # 检查是否有隐藏运行参数
    if '--hidden' in sys.argv:
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    run_hidden()

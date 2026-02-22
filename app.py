from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
import threading
import random

app = Flask(__name__)
CORS(app)

# 当前丢包率 (0, 0.5, 1.0 对应 0%, 50%, 100%)
current_drop_rate = 0.0
# 数据包嗅探线程
sniff_thread = None
sniff_running = False

# 导入 scapy
try:
    from scapy.all import sniff, IP, Raw, send
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("警告: scapy 未安装，将使用模拟模式")

# 获取网络接口列表
def get_network_interfaces():
    """获取可用的网络接口"""
    interfaces = []
    try:
        import subprocess
        result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        lines = result.stdout.strip().split('\n')[3:]  # 跳过表头
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                iface_name = ' '.join(parts[3:])
                if iface_name and iface_name not in ['Loopback', '环回']:
                    interfaces.append(iface_name)
    except:
        pass
    
    # 添加常见接口名称
    default_interfaces = ['以太网', 'Ethernet', 'Wi-Fi', 'WLAN', '本地连接', 'Local Area Connection']
    for iface in default_interfaces:
        if iface not in interfaces:
            interfaces.append(iface)
    
    return interfaces

# 数据包处理回调
def packet_callback(pkt):
    """处理捕获的数据包，根据丢包率决定是否丢弃"""
    global current_drop_rate
    
    if current_drop_rate <= 0:
        return
    
    if random.random() < current_drop_rate:
        # 丢弃数据包 - 不执行任何操作
        return
    else:
        # 转发数据包
        try:
            if IP in pkt:
                send(pkt, verbose=False, realtime=True)
        except:
            pass

# 启动数据包嗅探
def start_packet_sniffing():
    """在后台线程中启动数据包嗅探"""
    global sniff_running
    
    if not SCAPY_AVAILABLE or sniff_running:
        return
    
    def sniff_packets():
        global sniff_running
        sniff_running = True
        
        interfaces = get_network_interfaces()
        
        # 尝试在每个接口上嗅探
        for iface in interfaces:
            try:
                sniff(
                    iface=iface,
                    prn=packet_callback,
                    filter="ip",
                    store=0,
                    stop_filter=lambda x: not sniff_running
                )
            except:
                continue
    
    thread = threading.Thread(target=sniff_packets, daemon=True)
    thread.start()

# 应用丢包率设置
def apply_packet_drop(drop_rate):
    """应用丢包率设置"""
    global current_drop_rate, sniff_thread, sniff_running
    
    current_drop_rate = drop_rate
    
    # 如果丢包率大于0且scapy可用，启动嗅探
    if drop_rate > 0 and SCAPY_AVAILABLE and not sniff_running:
        start_packet_sniffing()
    
    return True

# 清除丢包设置
def clear_packet_drop():
    """清除丢包设置"""
    global current_drop_rate, sniff_running
    
    current_drop_rate = 0.0
    sniff_running = False
    
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'drop_rate': current_drop_rate,
        'scapy_available': SCAPY_AVAILABLE
    })

@app.route('/api/set', methods=['POST'])
def set_drop_rate():
    data = request.get_json()
    drop_rate = data.get('drop_rate', 0)
    
    # 支持 0, 0.5, 1.0 三档 (0%, 50%, 100%)
    if drop_rate not in [0, 0.5, 1.0]:
        return jsonify({'success': False, 'error': '无效的丢包率值'})
    
    success = apply_packet_drop(drop_rate)
    return jsonify({
        'success': success,
        'drop_rate': current_drop_rate
    })

@app.route('/api/clear', methods=['POST'])
def clear_rule():
    success = clear_packet_drop()
    return jsonify({'success': success, 'drop_rate': 0})

def run_hidden():
    """以隐藏模式运行Flask服务"""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    # 清理可能存在的旧规则
    clear_packet_drop()
    
    # 检查是否有隐藏运行参数
    if '--hidden' in sys.argv:
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    run_hidden()

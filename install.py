import os
import sys
import subprocess
import platform

def setup_autostart_windows():
    """设置Windows开机自启"""
    script_path = os.path.abspath("backend/server.py")
    python_path = sys.executable
    
    # 创建VBS脚本实现隐藏运行
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{python_path}"" ""{script_path}""", 0, False
Set WshShell = Nothing
'''
    
    vbs_path = os.path.join(os.path.dirname(script_path), "start_hidden.vbs")
    with open(vbs_path, 'w') as f:
        f.write(vbs_content)
    
    # 添加到启动文件夹
    startup_folder = os.path.join(os.getenv('APPDATA'), 
                                  'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
    shortcut_path = os.path.join(startup_folder, 'NetworkController.vbs')
    
    try:
        import shutil
        shutil.copy(vbs_path, shortcut_path)
        print(f"✅ 已设置开机自启：{shortcut_path}")
        return True
    except Exception as e:
        print(f"❌ 设置开机自启失败：{e}")
        return False

def setup_autostart_linux():
    """设置Linux开机自启"""
    script_path = os.path.abspath("backend/server.py")
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Network Controller Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
ExecStart={python_path} {script_path}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    service_path = "/etc/systemd/system/network-controller.service"
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        subprocess.run(['systemctl', 'daemon-reload'])
        subprocess.run(['systemctl', 'enable', 'network-controller'])
        print(f"✅ 已设置开机自启：{service_path}")
        return True
    except Exception as e:
        print(f"❌ 设置开机自启失败（需要root权限）：{e}")
        return False

def install():
    print("🚀 网络控制器安装程序\n")
    
    # 安装依赖
    print("📦 安装Python依赖...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # 设置开机自启
    print("\n⚙️ 设置开机自启...")
    system = platform.system()
    
    if system == "Windows":
        setup_autostart_windows()
    elif system == "Linux":
        setup_autostart_linux()
    else:
        print(f"❌ 不支持的操作系统：{system}")
    
    print("\n✨ 安装完成！")
    print("\n使用说明：")
    print("1. 运行服务：python backend/server.py")
    print("2. 浏览器访问：http://localhost:5000")
    print("3. 局域网访问：http://<本机IP>:5000")
    print("\n⚠️ 注意：修改网络设置需要管理员权限")

if __name__ == '__main__':
    install()

import subprocess
import sys
import os

def start_hidden():
    """以完全隐藏模式启动应用"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    # 使用 pythonw.exe 运行（无控制台窗口）
    pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
    
    subprocess.Popen(
        [pythonw_path, app_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=script_dir
    )

if __name__ == "__main__":
    start_hidden()

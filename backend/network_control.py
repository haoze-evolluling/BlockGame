import subprocess
import platform
import os
import sys
import psutil

class NetworkController:
    def __init__(self):
        self.current_loss = 0
        self.system = platform.system()
        self.clumsy_process = None
        self.clumsy_path = self._get_clumsy_path()
    
    def _get_clumsy_path(self):
        """获取clumsy.exe路径"""
        # 支持PyInstaller打包后的路径
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 尝试多个可能的路径
        possible_paths = [
            os.path.join(base_path, 'clumsy', 'clumsy.exe'),  # clumsy文件夹中
            os.path.join(base_path, 'clumsy.exe'),             # 根目录
            os.path.join(os.getcwd(), 'clumsy', 'clumsy.exe'), # 当前目录的clumsy文件夹
            os.path.join(os.getcwd(), 'clumsy.exe'),           # 当前目录
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_clumsy_dir(self):
        """获取clumsy目录（包含依赖文件）"""
        if self.clumsy_path:
            return os.path.dirname(self.clumsy_path)
        return None
    
    def _kill_clumsy(self):
        """停止所有clumsy进程"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'clumsy' in proc.info['name'].lower():
                    proc.kill()
        except:
            pass
    
    def set_packet_loss(self, loss_percent):
        """设置丢包率：0%, 50%, 100%"""
        try:
            if self.system == "Windows":
                return self._set_windows_loss(loss_percent)
            else:
                return self._set_linux_loss(loss_percent)
        except Exception as e:
            return False, str(e)
    
    def _set_windows_loss(self, loss_percent):
        """Windows系统使用clumsy或直接禁用网络适配器"""
        # 先停止之前的clumsy进程
        self._kill_clumsy()
        
        if loss_percent == 100:
            # 禁用所有网络适配器
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Disable-NetAdapter -Confirm:$false"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent
            return True, f"已设置丢包率为 {loss_percent}%"
            
        elif loss_percent == 0:
            # 启用所有网络适配器
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.current_loss = loss_percent
            return True, f"已设置丢包率为 {loss_percent}%"
            
        elif loss_percent == 50:
            # 使用clumsy实现50%丢包
            if not self.clumsy_path:
                return False, "找不到clumsy.exe，请确保clumsy文件夹在项目目录中"
            
            if not os.path.exists(self.clumsy_path):
                return False, f"clumsy.exe不存在: {self.clumsy_path}"
            
            try:
                # 获取clumsy目录（需要在同目录下找到依赖文件）
                clumsy_dir = self._get_clumsy_dir()
                
                # 启动clumsy，设置50%丢包
                # 参数说明：
                # --filter "outbound or inbound" - 影响出站和入站流量
                # --drop on - 启用丢包
                # --drop-chance 50 - 50%丢包率
                cmd = [
                    self.clumsy_path,
                    '--filter', 'outbound or inbound',
                    '--drop', 'on',
                    '--drop-chance', '50'
                ]
                
                # 使用CREATE_NO_WINDOW标志隐藏窗口
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
                # 在clumsy目录下运行（确保能找到依赖文件）
                self.clumsy_process = subprocess.Popen(
                    cmd,
                    cwd=clumsy_dir,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                self.current_loss = loss_percent
                return True, f"已设置丢包率为 {loss_percent}%（使用clumsy）"
                
            except Exception as e:
                return False, f"启动clumsy失败: {str(e)}"
        
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
    
    def cleanup(self):
        """清理资源"""
        self._kill_clumsy()

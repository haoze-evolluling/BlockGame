import subprocess
import platform

class NetworkController:
    def __init__(self):
        self.current_loss = 0
        self.system = platform.system()
    
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
        if loss_percent == 100:
            # 禁用所有网络适配器
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Disable-NetAdapter -Confirm:$false"'
        elif loss_percent == 0:
            # 启用所有网络适配器
            cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Disabled\'} | Enable-NetAdapter -Confirm:$false"'
        else:
            # 50%丢包需要使用clumsy工具或其他方法
            return False, "50%丢包需要安装clumsy工具"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        self.current_loss = loss_percent
        return True, f"已设置丢包率为 {loss_percent}%"
    
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

import subprocess
import platform
import os
import sys
import threading
import time

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

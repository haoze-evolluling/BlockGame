"""
网络控制器安装程序
首次运行需要管理员权限
"""
import os
import sys
import shutil
import subprocess
import ctypes
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class InstallConfig:
    """安装配置"""
    app_name: str = "NetworkController"
    port: int = 5000
    files: List[Tuple[str, str]] = None

    def __post_init__(self):
        if self.files is None:
            self.files = [
                ("NetworkController.exe", "NetworkController.exe"),
                ("index.html", "index.html"),
            ]

    @property
    def install_dir(self) -> Path:
        program_files = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        return Path(program_files) / self.app_name


class AdminHelper:
    """管理员权限管理"""

    @staticmethod
    def check() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    @staticmethod
    def request() -> None:
        if not AdminHelper.check():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{" ".join(sys.argv)}"', None, 1
            )
            sys.exit(0)


class ResourceHelper:
    """资源路径管理"""

    @staticmethod
    def get_path(filename: str) -> Path:
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS) / "app"
        else:
            base_path = Path(__file__).parent
        return base_path / filename


class FileInstaller:
    """文件安装器"""

    def __init__(self, config: InstallConfig):
        self.config = config
        self.results: List[Tuple[str, bool, str]] = []

    def install_all(self) -> bool:
        """安装所有文件，返回是否全部成功"""
        self.config.install_dir.mkdir(parents=True, exist_ok=True)

        for src_name, dst_name in self.config.files:
            success, message = self._copy_file(src_name, dst_name)
            self.results.append((dst_name, success, message))

        return all(r[1] for r in self.results)

    def _copy_file(self, src_name: str, dst_name: str) -> Tuple[bool, str]:
        """复制单个文件"""
        try:
            src_path = ResourceHelper.get_path(src_name)
            dst_path = self.config.install_dir / dst_name

            if not src_path.exists():
                return False, f"未找到: {src_name}"

            shutil.copy2(src_path, dst_path)
            return True, f"安装: {dst_name}"
        except Exception as e:
            return False, f"复制 {src_name} 失败: {e}"

    def print_results(self) -> None:
        """打印安装结果"""
        for name, success, message in self.results:
            symbol = "✓" if success else "✗"
            print(f"{symbol} {message}")


class ServiceManager:
    """服务管理器"""

    def __init__(self, exe_path: Path):
        self.exe_path = exe_path

    def install(self) -> bool:
        """安装服务"""
        if not self.exe_path.exists():
            return False
        try:
            subprocess.run([str(self.exe_path), "install"], check=False)
            return True
        except Exception:
            return False

    def get_commands(self) -> List[Tuple[str, str]]:
        """获取管理命令列表"""
        return [
            ("install", "安装服务"),
            ("uninstall", "卸载服务"),
            ("start", "启动服务"),
            ("stop", "停止服务"),
            ("status", "查看状态"),
        ]


class BrowserLauncher:
    """浏览器启动器"""

    @staticmethod
    def open(url: str) -> None:
        try:
            subprocess.Popen(["cmd", "/c", "start", url])
        except Exception:
            pass


import socket


class NetworkHelper:
    """网络工具"""

    @staticmethod
    def get_local_ips() -> List[str]:
        """获取本机所有局域网 IP 地址"""
        ips = []
        try:
            hostname = socket.gethostname()
            addr_info = socket.getaddrinfo(hostname, None)
            for info in addr_info:
                ip = info[4][0]
                if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                    if ip not in ips:
                        ips.append(ip)
        except Exception:
            pass

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip not in ips and not ip.startswith("127."):
                ips.insert(0, ip)
            s.close()
        except Exception:
            pass

        return ips if ips else ["127.0.0.1"]


class InstallerUI:
    """安装界面"""

    def __init__(self, config: InstallConfig):
        self.config = config

    def show_header(self) -> None:
        print("=" * 60)
        print("网络控制器安装程序")
        print("=" * 60)
        print()

    def show_footer(self, success: bool) -> None:
        print()
        print("=" * 60)
        print("安装完成！" if success else "安装出现问题")
        print("=" * 60)
        print()

    def show_usage(self) -> None:
        ips = NetworkHelper.get_local_ips()
        print("使用说明:")
        print()
        print("本机访问:")
        print(f"  http://127.0.0.1:{self.config.port}")
        print(f"  http://localhost:{self.config.port}")
        print()
        print("局域网访问:")
        for ip in ips:
            print(f"  http://{ip}:{self.config.port}")
        print()
        print("其他信息:")
        print("- 服务已设置为开机自动启动")
        print(f"- 安装目录: {self.config.install_dir}")
        print()

    def show_commands(self, exe_path: Path) -> None:
        print("管理命令:")
        for cmd, desc in ServiceManager(exe_path).get_commands():
            print(f"  {exe_path} {cmd:<10} - {desc}")
        print()

    def wait_exit(self) -> None:
        input("按回车键退出...")


class Installer:
    """主安装程序"""

    def __init__(self):
        self.config = InstallConfig()
        self.ui = InstallerUI(self.config)
        self.file_installer = FileInstaller(self.config)

    def run(self) -> None:
        self.ui.show_header()

        if not self._ensure_admin():
            return

        print(f"安装目录: {self.config.install_dir}")
        print()

        success = self.file_installer.install_all()
        self.file_installer.print_results()

        exe_path = self.config.install_dir / "NetworkController.exe"
        ServiceManager(exe_path).install()

        self.ui.show_footer(success)
        self.ui.show_usage()
        self.ui.show_commands(exe_path)

        BrowserLauncher.open(f"http://localhost:{self.config.port}")
        self.ui.wait_exit()

    def _ensure_admin(self) -> bool:
        """确保以管理员权限运行"""
        if not AdminHelper.check():
            print("需要管理员权限进行安装...")
            AdminHelper.request()
            return False
        return True


def main():
    Installer().run()


if __name__ == "__main__":
    main()

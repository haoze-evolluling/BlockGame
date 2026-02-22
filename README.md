# 网络控制器

用于调节电脑网络丢包率的工具，支持三档控制：0%、50%、100%。

## 功能特性

- 🎮 三档丢包率控制（正常/中等/完全阻断）
- 🌐 支持局域网访问
- 🎨 现代炫酷的Web界面
- 👻 后台隐藏运行（无窗口）
- 🚀 开机自动启动
- 📦 打包成exe，一键安装

## 快速安装

### 方式一：一键安装（推荐）
双击运行 `一键打包安装.bat`

### 方式二：手动安装
```bash
# 1. 打包程序
python build.py

# 2. 安装程序
python installer.py
```

## 使用方法

安装后程序会自动在后台运行，通过浏览器访问控制面板：

### 本机访问
`http://localhost:5000`

### 局域网访问
`http://<本机IP>:5000`

查看本机IP：运行 `ipconfig` 命令

## 卸载程序

运行：`C:\Program Files\NetworkController\uninstall.bat`

## 开发模式

如需开发调试，可直接运行源码：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
python backend/server.py
```

## 技术说明

- 打包工具：PyInstaller
- 后端：Flask + Python
- 前端：原生HTML/CSS/JavaScript
- 网络控制：PowerShell (Windows) / tc (Linux)
- 自启动：注册表 Run 键

## 注意事项

⚠️ **重要提示**：
- 程序需要管理员权限才能修改网络设置
- 100%阻断会完全断开网络连接
- 确保防火墙允许5000端口访问
- 50%丢包在Windows上需要额外工具（如clumsy）

详细说明请查看 `使用说明.md`

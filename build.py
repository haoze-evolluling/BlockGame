"""
PyInstaller 打包脚本
生成可安装的exe程序，包含服务管理功能
"""
import PyInstaller.__main__
import os
import shutil
import sys


def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist', '发布包']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理: {dir_name}")
    
    # 清理spec文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
            print(f"已清理: {file}")


def build_main_app():
    """打包主应用程序"""
    print("=" * 50)
    print("正在打包主应用程序...")
    print("=" * 50)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    args = [
        'main.py',
        '--name=NetworkController',
        '--onefile',
        '--windowed',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32event',
        '--hidden-import=servicemanager',
        f'--add-data={base_dir}/index.html;.',
        '--strip',
        '--noupx',
    ]
    
    PyInstaller.__main__.run(args)
    print("✓ 主应用程序打包完成")


def build_service_manager():
    """打包服务管理工具"""
    print("=" * 50)
    print("正在打包服务管理工具...")
    print("=" * 50)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    args = [
        'service_manager.py',
        '--name=ServiceManager',
        '--onefile',
        '--console',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32event',
        '--hidden-import=servicemanager',
        f'--add-data={base_dir}/main.py;.',
        '--strip',
        '--noupx',
    ]
    
    PyInstaller.__main__.run(args)
    print("✓ 服务管理工具打包完成")


def build_installer():
    """打包安装程序"""
    print("=" * 50)
    print("正在打包安装程序...")
    print("=" * 50)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    args = [
        'installer.py',
        '--name=安装程序',
        '--onefile',
        '--console',
        '--uac-admin',
        f'--add-data={base_dir}/dist/NetworkController.exe;app',
        f'--add-data={base_dir}/dist/ServiceManager.exe;app',
        f'--add-data={base_dir}/index.html;app',
        '--strip',
        '--noupx',
    ]
    
    PyInstaller.__main__.run(args)
    print("✓ 安装程序打包完成")


def create_distribution():
    """创建分发目录"""
    print("=" * 50)
    print("创建分发包...")
    print("=" * 50)
    
    dist_dir = '发布包'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # 复制文件
    files_to_copy = [
        ('dist/安装程序.exe', '安装程序.exe'),
        ('dist/ServiceManager.exe', 'ServiceManager.exe'),
        ('dist/NetworkController.exe', 'NetworkController.exe'),
        ('index.html', 'index.html'),
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy(src, os.path.join(dist_dir, dst))
            print(f"✓ 复制: {dst}")
    
    # 创建说明文件
    readme_content = """网络控制器 - 安装说明
========================

首次安装（需要管理员权限）：
1. 右键点击"安装程序.exe"
2. 选择"以管理员身份运行"
3. 按提示完成安装

安装完成后：
- 服务会自动注册并启动
- 开机时会自动运行，无需再次授权
- 访问 http://localhost:5000 使用

服务管理：
- ServiceManager.exe install  - 安装服务
- ServiceManager.exe remove   - 卸载服务
- ServiceManager.exe start    - 启动服务
- ServiceManager.exe stop     - 停止服务
- ServiceManager.exe status   - 查看状态

卸载：
以管理员身份运行: ServiceManager.exe remove
"""
    
    with open(os.path.join(dist_dir, '使用说明.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ 分发包已创建: {dist_dir}/")


def main():
    """主构建流程"""
    print("开始构建网络控制器...")
    print()
    
    # 清理旧构建
    clean_build()
    
    # 打包各个组件
    build_main_app()
    build_service_manager()
    build_installer()
    
    # 创建分发包
    create_distribution()
    
    print()
    print("=" * 50)
    print("构建完成！")
    print("=" * 50)
    print("输出目录: 发布包/")
    print("运行 发布包/安装程序.exe 进行安装")


if __name__ == '__main__':
    main()

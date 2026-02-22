"""
PyInstaller 打包脚本
生成网络控制器安装包
"""
import PyInstaller.__main__
import os
import shutil


def clean_build():
    dirs_to_remove = ['build', 'dist', '发布包']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理: {dir_name}")
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
            print(f"已清理: {file}")


def build_main_app():
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
        f'--add-data={base_dir}/index.html;.',
        '--strip',
        '--noupx',
    ]

    PyInstaller.__main__.run(args)
    print("✓ 主应用程序打包完成")


def build_installer():
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
        f'--add-data={base_dir}/index.html;app',
        '--strip',
        '--noupx',
    ]

    PyInstaller.__main__.run(args)
    print("✓ 安装程序打包完成")


def create_distribution():
    print("=" * 50)
    print("创建分发包...")
    print("=" * 50)

    dist_dir = '发布包'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    files_to_copy = [
        ('dist/安装程序.exe', '安装程序.exe'),
        ('dist/NetworkController.exe', 'NetworkController.exe'),
        ('index.html', 'index.html'),
    ]

    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy(src, os.path.join(dist_dir, dst))
            print(f"✓ 复制: {dst}")

    readme_content = """网络控制器 - 使用说明
========================

首次安装：
1. 右键点击"安装程序.exe"
2. 选择"以管理员身份运行"
3. 按提示完成安装

安装完成后：
- 服务会自动注册并启动
- 开机时会自动运行
- 访问 http://<本机IP>:5000 使用

直接运行（不安装服务）：
- NetworkController.exe
- 需要管理员权限

管理命令：
- NetworkController.exe install    - 安装服务
- NetworkController.exe uninstall  - 卸载服务
- NetworkController.exe start      - 启动服务
- NetworkController.exe stop       - 停止服务
- NetworkController.exe restart    - 重启服务
- NetworkController.exe status     - 查看状态

卸载：
以管理员身份运行: NetworkController.exe uninstall
"""

    with open(os.path.join(dist_dir, '使用说明.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✓ 分发包已创建: {dist_dir}/")


def main():
    print("开始构建网络控制器...")
    print()

    clean_build()
    build_main_app()
    build_installer()
    create_distribution()

    print()
    print("=" * 50)
    print("构建完成！")
    print("=" * 50)
    print("输出目录: 发布包/")
    print("运行 发布包/安装程序.exe 进行安装")


if __name__ == '__main__':
    main()

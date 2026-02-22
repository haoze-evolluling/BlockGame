"""
构建脚本 - 打包成exe
"""
import subprocess
import sys
import os

def install_dependencies():
    """安装打包依赖"""
    print("📦 安装打包依赖...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def build_exe():
    """使用PyInstaller打包"""
    print("\n🔨 开始打包...")
    
    # 清理旧的构建文件
    if os.path.exists('build'):
        import shutil
        shutil.rmtree('build')
    if os.path.exists('dist'):
        import shutil
        shutil.rmtree('dist')
    
    # 使用spec文件打包
    result = subprocess.run(['pyinstaller', 'build.spec', '--clean'])
    
    if result.returncode == 0:
        print("\n✅ 打包成功！")
        print("\n生成的文件:")
        print("  - dist/NetworkController.exe")
        print("\n下一步:")
        print("  运行安装程序: python installer.py")
    else:
        print("\n❌ 打包失败")
        sys.exit(1)

if __name__ == '__main__':
    print("🚀 网络控制器构建工具\n")
    install_dependencies()
    build_exe()

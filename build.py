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
    
    # 检查clumsy文件夹是否存在
    if not os.path.exists('clumsy'):
        print("\n❌ 错误: 找不到 clumsy 文件夹")
        print("请确保 clumsy 文件夹在项目根目录")
        sys.exit(1)
    
    # 检查clumsy.exe是否存在
    if not os.path.exists('clumsy/clumsy.exe'):
        print("\n❌ 错误: 找不到 clumsy/clumsy.exe")
        print("50%丢包功能需要 clumsy.exe")
        print("请将 clumsy 文件夹放到项目根目录")
        sys.exit(1)
    
    # 检查依赖文件
    required_files = [
        'clumsy/WinDivert.dll',
        'clumsy/WinDivert64.sys'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("\n⚠️ 警告: 缺少依赖文件:")
        for f in missing_files:
            print(f"  - {f}")
        choice = input("\n是否继续打包？(y/N): ").strip().lower()
        if choice != 'y':
            print("已取消打包")
            sys.exit(0)
    
    print("✅ clumsy 文件检查通过")
    
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

@echo off
chcp 65001 >nul
echo ========================================
echo 网络控制器 - 打包脚本
echo ========================================
echo.

echo [1/3] 检查依赖...
pip install pyinstaller flask flask-cors

echo.
echo [2/3] 开始打包...
pyinstaller --clean build.spec

echo.
echo [3/3] 打包完成！
echo.
echo 生成的EXE文件位置：dist\NetworkController.exe
echo.
echo 使用说明：
echo 1. 双击运行 NetworkController.exe
echo 2. 首次运行会请求管理员权限并配置自启动
echo 3. 后续开机自动静默启动
echo 4. 访问 http://localhost:5000 使用控制面板
echo.
pause

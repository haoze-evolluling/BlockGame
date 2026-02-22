@echo off
chcp 65001 >nul
echo ========================================
echo   网络控制器 - 一键打包安装
echo ========================================
echo.

echo [1/2] 正在打包程序...
python build.py
if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    pause
    exit /b 1
)

echo.
echo [2/2] 正在安装程序...
python installer.py

pause

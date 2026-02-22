@echo off
chcp 65001 >nul
title 网络控制器 - 一键打包安装

:: 保存原始工作目录
cd /d "%~dp0"

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 需要管理员权限，正在请求...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 确保在正确的目录
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       网络控制器 - 一键打包安装          ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 错误: 未检测到Python环境
    echo     请先安装Python 3.8或更高版本
    pause
    exit /b 1
)
echo [✓] Python环境检测通过

:: 步骤1: 打包
echo.
echo ──────────────────────────────────────────
echo  [1/2] 正在打包程序...
echo ──────────────────────────────────────────
python build.py
if %errorlevel% neq 0 (
    echo.
    echo [✗] 打包失败！
    pause
    exit /b 1
)

:: 步骤2: 安装
echo.
echo ──────────────────────────────────────────
echo  [2/2] 正在安装程序...
echo ──────────────────────────────────────────
python installer.py

pause

@echo off
cd /d "%~dp0"

echo Starting network control tool...
start /b pythonw hidden_start.pyw
echo Service started, please visit http://localhost:5000

timeout /t 3 >nul

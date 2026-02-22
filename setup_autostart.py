import os
import sys
import winreg
import shutil

def setup_autostart():
    """设置开机自启动"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建启动器脚本
    launcher_path = os.path.join(script_dir, "launcher.vbs")
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write('''Set WshShell = CreateObject("WScript.Shell")
Set objWMIService = GetObject("winmgmts:\\\\.\\root\\cimv2")
Set colItems = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'python.exe' OR Name = 'pythonw.exe'")
Dim isRunning
isRunning = False
For Each objItem in colItems
    If InStr(objItem.CommandLine, "app.py") > 0 Then
        isRunning = True
        Exit For
    End If
Next
If Not isRunning Then
    WshShell.Run "\"" & WshShell.CurrentDirectory & "\\hidden_start.pyw\"", 0, False
End If
Set WshShell = Nothing
''')
    
    # 添加到注册表启动项
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "NetworkControlTool"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'wscript.exe "{launcher_path}"')
        winreg.CloseKey(key)
        print("开机自启动设置成功")
        return True
    except Exception as e:
        print(f"设置开机自启动失败: {e}")
        return False

def remove_autostart():
    """移除开机自启动"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "NetworkControlTool"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
        print("已移除开机自启动")
        return True
    except:
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_autostart()
    else:
        setup_autostart()

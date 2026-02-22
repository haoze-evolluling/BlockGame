# Clumsy 集成说明

## 已完成的集成

程序已集成 clumsy.exe 用于实现 50% 丢包功能。

## 文件位置

请确保 `clumsy` 文件夹放在项目根目录：

```
项目目录/
├── clumsy/
│   ├── clumsy.exe          ← clumsy主程序
│   ├── WinDivert.dll       ← 依赖文件
│   └── WinDivert64.sys     ← 依赖文件
├── backend/
├── frontend/
└── ...
```

⚠️ **重要**: clumsy 需要这些依赖文件才能正常工作，请确保整个 clumsy 文件夹都在项目中。

## 功能说明

- **0% 丢包** - 启用所有网络适配器（正常模式）
- **50% 丢包** - 使用 clumsy.exe 实现（模拟网络不稳定）
- **100% 丢包** - 禁用所有网络适配器（完全断网）

## 测试集成

运行测试脚本：

```bash
python test_clumsy.py
```

这会测试 clumsy 是否正确集成并能正常工作。

## 打包说明

打包时整个 clumsy 文件夹会自动包含在 exe 中：

```bash
python build.py
```

打包后的程序会自动查找并使用内置的 clumsy 及其依赖文件。

## Clumsy 参数说明

程序使用的 clumsy 参数：

```
--filter "outbound or inbound"  # 影响出站和入站流量
--drop on                        # 启用丢包功能
--drop-chance 50                 # 50% 丢包率
```

## 注意事项

⚠️ **重要提示**：

1. clumsy.exe 需要管理员权限运行
2. 程序会自动隐藏 clumsy 窗口
3. 切换模式时会自动停止之前的 clumsy 进程
4. 程序退出时会自动清理 clumsy 进程
5. clumsy 必须和 WinDivert.dll、WinDivert64.sys 在同一目录

## 下载 Clumsy

如果还没有 clumsy，可以从官方下载：

https://jagt.github.io/clumsy/

下载后解压，将整个 `clumsy` 文件夹放到项目根目录即可。

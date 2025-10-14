# Android性能监控工具

这是一个Android版本的性能监控工具，功能和逻辑与iOS版本完全一样，使用ADB来获取Android应用的性能参数。

## 功能特性

- ✅ **实时性能监控**: CPU、内存、FPS、线程数、磁盘读写
- ✅ **Web可视化界面**: 基于Chart.js的实时图表展示
- ✅ **拖拽功能**: 所有面板支持拖拽排序，并保存到localStorage
- ✅ **数据统计**: 显示当前值、平均值、最大值/最小值
- ✅ **设备管理**: 自动检测连接的Android设备
- ✅ **应用选择**: 列出设备上安装的第三方应用

## 系统要求

### 必需工具
- Python 3.8+
- Android SDK Platform Tools (ADB)
- Android设备（已开启开发者选项和USB调试）

### 安装ADB
```bash
# macOS (使用Homebrew)
brew install android-platform-tools

# Ubuntu/Debian
sudo apt update
sudo apt install android-tools-adb

# Windows
# 下载Android SDK Platform Tools并添加到PATH环境变量
```

### Android设备设置
1. 打开"设置" → "关于手机"
2. 连续点击"版本号"7次开启开发者选项
3. 进入"设置" → "开发者选项"
4. 开启"USB调试"
5. 使用USB线连接设备到电脑
6. 首次连接时，设备上会弹出授权提示，选择"允许"

## 使用方法

### 方法1: Web可视化界面（推荐）

```bash
# 启动Web界面
python3 start_android_monitor.py

# 或直接运行
python3 android_web_visualizer.py
```

访问地址：http://localhost:5003

### 方法2: 命令行版本

```bash
# 监控指定应用
python3 android_main.py com.example.app

# 监控指定设备上的应用
python3 android_main.py emulator-5554 com.example.app
```

## 功能对比

| 功能 | iOS版本 | Android版本 |
|------|---------|-------------|
| 设备通信 | pymobiledevice3 + py_ios_device | ADB |
| 端口 | 5002 | 5003 |
| CPU监控 | ✅ | ✅ |
| 内存监控 | ✅ | ✅ |
| FPS监控 | ✅ | ✅ |
| 线程监控 | ✅ | ✅ |
| 磁盘I/O | ✅ | ✅ |
| 拖拽功能 | ✅ | ✅ |
| 数据统计 | ✅ | ✅ |

## 数据采集原理

### CPU使用率
- 使用 `adb shell top -p <pid> -n 1` 获取进程CPU使用率

### 内存使用
- 使用 `adb shell dumpsys meminfo <package>` 获取内存统计

### FPS帧率
- 使用 `adb shell dumpsys gfxinfo <package> framestats` 分析帧时间

### 线程数
- 读取 `/proc/<pid>/task` 目录下的线程列表

### 磁盘I/O
- 读取 `/proc/<pid>/io` 文件获取读写字节数

## 文件结构

```
android_web_visualizer.py     # Web服务后端（主要文件）
android_main.py               # 命令行版本
start_android_monitor.py      # 启动脚本
templates/android_index.html  # Web界面HTML
static/android_script.js      # Web界面JavaScript
```

## 故障排除

### 1. 设备检测不到
```bash
# 检查ADB状态
adb devices

# 重启ADB服务
adb kill-server
adb start-server
```

### 2. 应用PID获取失败
- 确保应用正在运行
- 检查应用包名是否正确
- 某些系统应用可能需要root权限

### 3. 权限问题
```bash
# 确保USB调试已开启
adb shell getprop ro.debuggable

# 检查开发者选项状态
adb shell settings get global development_settings_enabled
```

### 4. FPS数据为0
- 确保应用有图形界面活动
- 某些应用可能不支持gfxinfo
- 需要应用处于前台状态

## 对比说明

这个Android版本完全参考iOS版本的逻辑和功能：

1. **架构一致**: Flask + Socket.IO + Chart.js
2. **功能一致**: 相同的监控指标和统计方式
3. **界面一致**: 相同的Web界面设计和拖拽功能
4. **数据格式一致**: 相同的JSON输出格式
5. **更新频率一致**: 1秒间隔的实时监控

主要差异只在于数据获取方式：
- iOS版本使用pymobiledevice3/py_ios_device
- Android版本使用ADB命令行工具

这样确保了两个平台的监控工具具有完全一致的用户体验。
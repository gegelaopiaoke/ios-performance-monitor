# Windows 平台使用说明

## 📌 重要说明

**Windows 平台支持状况：**
- ✅ **Android 监控**：完全支持
- ⚠️ **iOS 监控**：**实验性功能**（需要安装 iTunes）

## ✅ 支持的功能

- ✅ Android 设备性能监控（完全支持）
- ⚠️ iOS 设备性能监控（实验性，需要 iTunes）
- ✅ 实时 CPU、内存、FPS、线程数监控
- ✅ Web 可视化界面
- ✅ 内存泄漏检测
- ✅ 数据导出和统计

## 🚀 快速开始

### 1. 系统要求

- Windows 10/11
- Python 3.8+
- **Android 监控**：Android SDK Platform Tools (ADB)
- **iOS 监控**：iTunes 或 Apple Device Support（可选，实验性）

### 2. 安装 ADB

**方法一：下载独立版本**
1. 访问 [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
2. 下载 Windows 版本
3. 解压到任意目录（如 `C:\adb`）
4. 添加到系统环境变量 PATH：
   - 右键"此电脑" → "属性" → "高级系统设置"
   - "环境变量" → 编辑 PATH → 添加 ADB 目录路径

**方法二：安装 Android Studio**
- Android Studio 会自动安装 ADB
- 路径通常在：`C:\Users\你的用户名\AppData\Local\Android\Sdk\platform-tools`

**验证安装：**
```cmd
adb version
```

### 3. 安装 iTunes（iOS 监控需要）

⚠️ **如果只需要 Android 监控，可以跳过此步骤**

**选项 1：安装 iTunes（推荐）**
- 从 [Apple 官网](https://www.apple.com/itunes/) 下载并安装 iTunes
- 安装后无需打开，驱动会自动生效

**选项 2：仅安装 Apple Device Support**
- 适用于不想安装完整 iTunes 的用户
- 从 Apple 官网下载独立的设备驱动

### 4. 安装 Python 依赖

```cmd
# 克隆项目
git clone <repository-url>
cd ios性能

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖（包含 iOS 实验性支持）
pip install -r requirements_windows.txt
```

### 5. 准备设备

#### Android 设备

1. 开启开发者选项：
   - 设置 → 关于手机 → 连续点击"版本号" 7次

2. 开启 USB 调试：
   - 设置 → 开发者选项 → 开启"USB调试"

3. 连接设备：
   - 使用 USB 线连接手机到电脑
   - 首次连接会弹出授权提示，点击"允许"

4. 验证连接：
```cmd
adb devices
```
应该显示类似：
```
List of devices attached
ABC123456789    device
```

#### iOS 设备（实验性）

1. 安装 iTunes 或 Apple Device Support（见上文）

2. 连接 iOS 设备：
   - 使用原装 USB 数据线连接
   - 设备上会弹出"信任此电脑"提示，点击"信任"
   - 如果没有弹出，断开重连

3. 验证连接：
```cmd
# 使用 pymobiledevice3 检查
python -m pymobiledevice3 usbmux list
```

⚠️ **注意事项：**
- Windows 上 iOS 监控为实验性功能，可能存在兼容性问题
- 建议先在 Android 设备上测试，确认工具可正常运行
- 如遇问题，请在 macOS 或 Linux 上使用 iOS 功能

## 📱 启动监控

### 方法一：使用统一启动器（推荐）

```cmd
python start_unified_monitor.py
```
- 自动检测 Windows 系统
- 支持 iOS 和 Android 监控
- iOS 为实验性功能，会有提示

### 方法二：使用单独启动脚本

**Android 监控：**
```cmd
python start_android_monitor.py
```

**iOS 监控：**
```cmd
python start_ios_monitor.py
```

### 方法三：直接启动

```cmd
cd android
python android_web_visualizer.py
```

## 🌐 访问监控界面

启动后，在浏览器中访问：

```
http://localhost:5003
```

或者局域网内其他设备访问：
```
http://你的电脑IP:5003
```

## 🎯 使用流程

1. **选择设备**：如果有多个设备，下拉选择要监控的设备
2. **选择应用**：
   - 点击"刷新应用列表"
   - 从下拉列表中选择要监控的应用
   - 显示格式：应用名称 (包名)
3. **开始监控**：点击"开始监控"按钮
4. **查看数据**：实时图表会自动更新
5. **停止监控**：点击"停止监控"按钮

## ⚙️ 功能说明

### 监控指标

| 指标 | 说明 |
|------|------|
| CPU使用率 | 应用占用的CPU百分比 |
| 内存使用 | 应用占用的物理内存（MB）|
| FPS | 应用渲染帧率 |
| 线程数 | 应用的线程总数 |
| 磁盘I/O | 读写速度（KB/s）|

### 内存泄漏检测

- 自动分析内存增长趋势
- 三级告警：轻微 / 警告 / 严重
- 实时显示检测状态
- 日志保存在 `logs/android_memory_leak_events.log`

### 数据统计

每个指标显示：
- 当前值
- 平均值
- 最大值

## 🔧 常见问题

### Q: 提示 "adb 不是内部或外部命令"？
**A:** ADB 未正确安装或未添加到 PATH 环境变量。参考上面的 ADB 安装步骤。

### Q: 设备列表为空？
**A:** 
1. 检查 USB 线是否连接良好
2. 确认手机已开启 USB 调试
3. 运行 `adb devices` 检查连接状态
4. 尝试 `adb kill-server` 然后 `adb start-server`

### Q: 应用列表为空？
**A:**
1. 确保设备已选择
2. 点击"刷新应用列表"
3. 检查设备是否有安装的应用

### Q: 监控数据不更新？
**A:**
1. 确认应用正在前台运行
2. 检查浏览器控制台是否有错误
3. 刷新页面重新连接

### Q: 端口 5003 被占用？
**A:** 
```cmd
# 查找占用端口的进程
netstat -ano | findstr :5003

# 结束进程（PID 是上面命令显示的最后一列）
taskkill /F /PID <进程ID>
```

### Q: 能否监控 iOS 设备？
**A:** 可以，但为**实验性功能**。需要：
1. 安装 iTunes 或 Apple Device Support
2. 安装 `requirements_windows.txt` 中的所有依赖
3. 使用 `python start_unified_monitor.py` 或 `python start_ios_monitor.py` 启动
4. 如遇问题，建议在 macOS 或 Linux 上使用

## 💡 性能优化建议

1. **关闭不必要的应用**：监控时关闭其他应用以获得更准确的数据
2. **使用原装 USB 线**：确保数据传输稳定
3. **保持设备唤醒**：监控过程中保持屏幕常亮
4. **局域网访问**：可以在平板或其他电脑上查看监控界面

## 📊 数据导出

监控数据会自动保存，可以通过以下方式导出：
- 截图保存图表
- 复制统计数据
- 查看日志文件（logs 目录）

## 🆘 获取帮助

如遇到其他问题：
1. 查看控制台输出的错误信息
2. 查看项目主 README.md
3. 提交 Issue 到项目仓库

## 📝 限制说明

Windows 平台特性：
- **Android 监控**：✅ 完全支持，稳定可靠
- **iOS 监控**：⚠️ 实验性支持，可能存在兼容性问题
- 某些高级功能可能需要管理员权限
- 部分系统信息获取方式与 macOS/Linux 不同

**建议：**
- 生产环境或关键测试，建议使用 macOS（最稳定）
- Windows 适合日常开发和 Android 测试
- iOS 测试建议优先选择 macOS


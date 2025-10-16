# 跨平台支持说明

## 🌍 平台兼容性总览

| 功能 | macOS | Linux | Windows |
|------|-------|-------|---------|
| iOS 监控 | ✅ | ✅ | ❌ |
| Android 监控 | ✅ | ✅ | ✅ |
| 统一启动器 | ✅ | ✅ | ✅* |
| Web 界面 | ✅ | ✅ | ✅ |
| 内存泄漏检测 | ✅ | ✅ | ✅ |

*Windows 上的统一启动器会自动禁用 iOS 选项

## 📦 依赖安装

### macOS / Linux
```bash
pip install -r requirements.txt
```

### Windows
```bash
pip install -r requirements_windows.txt
```

## 🚀 启动方式

### macOS / Linux（完整功能）

```bash
# 统一启动器（推荐）
python start_unified_monitor.py

# iOS 监控
python start_ios_monitor.py

# Android 监控
python start_android_monitor.py
```

### Windows（仅 Android）

```bash
# Android 监控（推荐）
python start_android_monitor.py

# 或使用统一启动器（会自动识别 Windows）
python start_unified_monitor.py
```

## 🔧 技术实现

### 跨平台适配

1. **端口检测**
   - Windows: `netstat -ano`
   - macOS/Linux: `lsof -ti :port`

2. **进程终止**
   - Windows: `taskkill /F /PID`
   - macOS/Linux: `kill -9`

3. **IP 地址获取**
   - Windows: `ipconfig`
   - macOS/Linux: `ifconfig`

4. **管理员权限检查**
   - Windows: `ctypes.windll.shell32.IsUserAnAdmin()`
   - macOS/Linux: `os.geteuid() == 0`

### 平台检测代码

```python
import platform

current_os = platform.system()
# 返回: 'Windows', 'Darwin' (macOS), 'Linux'
```

## ⚠️ Windows 限制

### 为什么 iOS 监控不支持 Windows？

1. **依赖库限制**
   - `pymobiledevice3` 仅支持 macOS/Linux
   - `py_ios_device` 需要 Unix 系统调用

2. **USB 通信协议**
   - iOS 设备 USB 通信需要 Apple 专有驱动
   - Windows 上的 iTunes 驱动与 Python 库不兼容

3. **系统 API**
   - iOS 工具依赖 Unix 特定的系统调用
   - Windows 没有等效的 API

### Windows 用户建议

1. **仅需 Android 监控**: 直接使用 Windows
2. **需要 iOS 监控**: 
   - 使用 macOS 系统
   - 使用 Linux（Ubuntu/Debian）
   - 使用虚拟机运行 Linux

## 📱 访问地址

无论哪个平台：

- iOS 监控: http://localhost:5002
- Android 监控: http://localhost:5003

## 🐛 常见问题

### macOS / Linux

**Q: 提示权限不足？**
```bash
sudo python start_ios_monitor.py
```

**Q: 找不到 iOS 设备？**
- 检查设备是否信任此电脑
- 尝试重新插拔 USB
- 运行 `pymobiledevice3 usbmux list` 检查

### Windows

**Q: 提示 "adb 不是内部或外部命令"？**
- 安装 Android SDK Platform Tools
- 添加 ADB 到系统 PATH

**Q: 为什么不能选择 iOS 监控？**
- Windows 不支持 iOS 监控，这是技术限制
- 请使用 macOS 或 Linux

**Q: 能用虚拟机吗？**
- Android 监控：✅ 可以，USB 直通即可
- iOS 监控：⚠️ 不推荐，USB 支持不稳定

## 📊 性能对比

| 项目 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 启动速度 | 快 | 快 | 快 |
| 稳定性 | 优秀 | 良好 | 良好 |
| USB 兼容性 | 优秀 | 良好 | 良好* |
| 功能完整度 | 100% | 100% | ~50% |

*Windows 仅 Android USB 支持良好

## 🎯 推荐配置

### 专业测试环境
- **推荐**: macOS（M系列或Intel）
- **原因**: 完整支持 iOS + Android
- **备选**: Ubuntu 20.04+ LTS

### 个人开发环境
- **iOS 应用**: 必须 macOS
- **Android 应用**: 任意平台
- **跨平台应用**: macOS（最方便）

### CI/CD 集成
- **GitHub Actions**: macOS runner（支持完整功能）
- **GitLab CI**: 配置 macOS executor
- **Jenkins**: macOS 或 Linux 节点

## 📚 相关文档

- [主 README](README.md)
- [Windows 使用说明](docs/README_Windows.md)
- [Android 专用文档](docs/README_Android.md)
- [内存泄漏检测说明](docs/内存泄漏检测使用说明.md)


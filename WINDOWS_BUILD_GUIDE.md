# Windows 平台快速打包指南

## 🎯 一键打包（最简单）

### 方法1: 使用批处理脚本（推荐）

1. 双击运行 `build_windows.bat`
2. 按照提示选择打包方式
3. 等待打包完成
4. 在 `dist/` 目录找到生成的 exe 文件

```batch
# 直接运行
build_windows.bat
```

---

## 🔧 手动打包（详细步骤）

### 前置准备

#### 1. 检查 Python 环境
```bash
python --version
# 需要 Python 3.7 或更高版本
```

#### 2. 安装依赖
```bash
# 安装项目依赖
pip install -r requirements_windows.txt

# 安装 PyInstaller
pip install pyinstaller
```

#### 3. 测试运行
```bash
# 测试 Android 监控
python start_android_monitor.py

# 测试统一监控
python start_unified_monitor.py
```

---

### 打包 Android 监控（推荐）

#### 方式一: 单文件打包
```bash
pyinstaller --onefile ^
    --name "Android性能监控" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "android;android" ^
    --add-data "ios;ios" ^
    --hidden-import=flask ^
    --hidden-import=flask_socketio ^
    --hidden-import=psutil ^
    start_android_monitor.py
```

#### 方式二: 使用配置文件
```bash
pyinstaller build_android.spec
```

**优点:**
- ✅ 单个 exe 文件，易于分发
- ✅ 约 25-30MB
- ✅ 无需额外依赖

**缺点:**
- ⚠️ 首次启动需要解压 (3-5秒)

---

### 打包统一监控（完整版）

#### 方式一: 单文件打包
```bash
pyinstaller --onefile ^
    --name "跨平台性能监控" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "android;android" ^
    --add-data "ios;ios" ^
    --hidden-import=flask ^
    --hidden-import=flask_socketio ^
    --hidden-import=psutil ^
    --hidden-import=py_ios_device ^
    --hidden-import=pymobiledevice3 ^
    start_unified_monitor.py
```

#### 方式二: 使用配置文件
```bash
pyinstaller build_unified.spec
```

**特点:**
- ✅ 支持 iOS 和 Android
- ✅ 约 35-40MB
- ⚠️ iOS 监控需要安装 iTunes

---

## 📦 打包结果

打包完成后，在 `dist/` 目录下会生成:

```
dist/
├── Android性能监控.exe    (Android 监控)
└── 跨平台性能监控.exe      (统一监控)
```

---

## ✅ 验证打包结果

### 1. 运行 exe 文件
```bash
cd dist
.\Android性能监控.exe
```

### 2. 检查功能
- [ ] 能否正常启动
- [ ] 能否检测到 Android 设备
- [ ] 能否打开浏览器界面
- [ ] 能否获取应用列表
- [ ] 能否开始监控

### 3. 测试环境要求
- Windows 7/8/10/11 (64位)
- 已安装 ADB (Android SDK Platform Tools)
- Android 设备已开启 USB 调试

---

## 🎨 添加图标（可选）

### 1. 准备图标文件
- 格式: `.ico`
- 推荐尺寸: 256x256
- 文件名: `icon.ico`

### 2. 放置图标
将 `icon.ico` 放在项目根目录

### 3. 修改打包命令
在 PyInstaller 命令中添加:
```bash
--icon=icon.ico
```

或在 `.spec` 文件中取消注释:
```python
icon='icon.ico'
```

---

## 🚀 优化打包

### 减小文件体积
```bash
pyinstaller --onefile ^
    --name "Android监控" ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module scipy ^
    --exclude-module PIL ^
    --strip ^
    --noupx ^
    start_android_monitor.py
```

### 提升启动速度
使用目录打包（而非单文件）:
```bash
pyinstaller --onedir ^
    --name "Android监控" ^
    start_android_monitor.py
```

**结果:**
- 生成 `dist/Android监控/` 目录
- 包含多个文件，但启动更快
- 体积更大 (~60MB)

---

## ⚠️ 常见问题

### 1. 杀毒软件误报
**现象:** exe 被杀毒软件拦截

**解决方案:**
- 添加到杀毒软件白名单
- 使用 `--upx-exclude` 参数
- 获取代码签名证书

### 2. 无法找到 ADB
**现象:** exe 运行后无法检测设备

**解决方案:**
- 确保 ADB 在系统 PATH 中
- 或将 ADB 和 exe 放在同一目录

### 3. 模板文件未找到
**现象:** 启动报错 "TemplateNotFound"

**解决方案:**
- 检查 `--add-data` 参数是否正确
- 使用 `windows_resource_helper.py` 修复路径

### 4. 打包后文件过大
**现象:** exe 文件超过 50MB

**解决方案:**
- 使用 `--exclude-module` 排除不需要的库
- 检查是否包含了不必要的文件

---

## 📋 打包检查清单

- [ ] Python 3.7+ 已安装
- [ ] PyInstaller 已安装
- [ ] 项目依赖已安装
- [ ] 代码已测试运行正常
- [ ] 已清理旧的打包文件
- [ ] 资源文件路径正确
- [ ] (可选) 图标文件已准备
- [ ] 打包命令已验证
- [ ] 打包后已测试运行

---

## 🎁 分发给用户

### 准备分发包

创建一个文件夹，包含:
```
Android性能监控/
├── Android性能监控.exe      (主程序)
├── README.txt                (使用说明)
├── adb.exe                   (可选: ADB 工具)
├── AdbWinApi.dll            (可选)
└── AdbWinUsbApi.dll         (可选)
```

### 使用说明模板

创建 `README.txt`:
```
Android 性能监控工具
===================

【系统要求】
- Windows 7/8/10/11 (64位)
- Android SDK Platform Tools (ADB)
- Android 设备并开启 USB 调试

【快速开始】
1. 连接 Android 设备到电脑
2. 双击 "Android性能监控.exe"
3. 在弹出的浏览器中使用

【注意事项】
- 首次运行可能被杀毒软件拦截，请添加信任
- 确保 ADB 已安装并在系统 PATH 中
- Android 设备需开启开发者选项和 USB 调试

【技术支持】
如有问题，请访问: [您的项目地址]
```

---

## ✨ 完成！

现在你已经成功将 Android 性能监控工具打包成 Windows exe 文件！

**下一步:**
1. 测试打包后的 exe
2. 分发给用户
3. 收集反馈并改进

**需要帮助?**
- 查看 `WINDOWS_COMPATIBILITY.md` 了解更多细节
- 检查 `build_windows.bat` 自动化脚本
- 参考 `.spec` 配置文件进行自定义

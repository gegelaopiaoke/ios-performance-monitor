# 📱 跨平台性能监控工具

一个支持iOS和Android设备的实时性能监控可视化工具，提供Web界面显示CPU、内存、FPS、线程数等关键指标。

## ✨ 核心特性

### 性能监控
- 🔄 **实时监控**: 每秒采集性能数据，实时更新图表
- 📊 **可视化图表**: 基于Chart.js的动态曲线图显示
- 🌐 **Web界面**: 美观的响应式Web界面，支持拖拽排序
- 📱 **跨平台支持**: 同时支持iOS 15+和Android设备监控
- 🎯 **应用特定监控**: 可指定Bundle ID或包名监控特定应用
- 🔧 **线程详情**: Android支持线程状态和分类统计
- 💾 **数据统计**: 显示当前值、平均值、最大值统计

### 🧠 内存泄漏检测（NEW）
- 🎯 **智能检测**: 基于线性回归的内存趋势分析算法
- 🚨 **分级提醒**: 轻微/警告/严重三级提醒系统
- ⚙️ **灵活配置**: 可调节检测阈值、时间窗口等参数
- 📝 **事件日志**: 自动记录所有泄漏事件到日志文件
- 🔧 **优化建议**: 针对性的代码优化和解决方案
- 🌐 **跨平台**: iOS和Android通用检测算法

### 智能交互
- 🤖 **自动检测**: 智能识别已连接的iOS/Android设备
- 📱 **一键启动**: 统一启动器支持多种启动模式
- 🎨 **美观界面**: 
  - 设备选择后自动加载应用列表
  - 应用列表显示真实名称（如：微信 (com.tencent.mm)）
  - 统计面板固定位置，关键指标集中展示
  - 内存泄漏实时可视化提醒

## 🚀 快速开始

### 环境准备

```bash
# 1. 克隆项目
git clone <repository-url>
cd ios性能

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 🎯 统一启动（推荐）⭐

**一键启动iOS和Android监控**:
```bash
# 交互式启动（自动检测设备）
python start_unified_monitor.py

# 快速启动iOS
python start_unified_monitor.py ios

# 快速启动Android
python start_unified_monitor.py android

# 同时启动两个平台
python start_unified_monitor.py both
```

**访问地址**:
- iOS监控: http://localhost:5002
- Android监控: http://localhost:5003

### iOS设备监控

**系统要求**:
- macOS (推荐) / Linux
- Python 3.13+
- 管理员权限
- iOS 15+ 设备已连接并信任电脑

**启动方法**:
```bash
# 方法1: 统一启动器（推荐）
python start_unified_monitor.py ios

# 方法2: 使用启动脚本
python start_ios_monitor.py

# 方法3: 手动启动
cd ios
python web_visualizer.py
```

访问地址：**http://localhost:5002**

### Android设备监控

**系统要求**:
- Python 3.8+
- Android SDK Platform Tools (ADB)
- Android设备已开启USB调试

**安装ADB**:
```bash
# macOS
brew install android-platform-tools

# Ubuntu/Debian
sudo apt install android-tools-adb
```

**启动方法**:
```bash
# 方法1: 使用启动脚本（推荐）
python start_android_monitor.py

# 方法2: 手动启动
cd android
python android_web_visualizer.py
```

访问地址：**http://localhost:5003**

## 📁 项目结构

```
跨平台性能监控工具/
├── ios/                          # iOS监控模块
│   ├── main.py                   # 原始性能监控脚本（未修改）
│   ├── web_visualizer.py          # iOS Web可视化服务器
│   └── start_web_monitor.py       # iOS子目录启动脚本
├── android/                       # Android监控模块
│   ├── android_main.py            # Android命令行监控脚本
│   ├── android_web_visualizer.py  # Android Web可视化服务器
│   └── start_android_monitor.py   # Android子目录启动脚本
├── templates/                     # Web界面模板
│   ├── index.html                 # iOS可视化界面
│   └── android_index.html         # Android可视化界面
├── static/                       # 静态资源文件
│   └── android_script.js          # Android前端脚本
├── tools/                        # 工具脚本
│   ├── check_tools.sh             # 环境检测工具
│   └── install_ios_tools.sh       # iOS工具链安装
├── docs/                         # 文档目录
│   └── README_Android.md          # Android平台专用文档
├── start_ios_monitor.py          # iOS主启动脚本
├── start_android_monitor.py      # Android主启动脚本
├── requirements.txt              # Python依赖列表
├── README.md                     # 主说明文档
└── CHANGELOG.md                  # 更新记录
```

## 📊 监控指标对比

| 指标类型 | iOS | Android | 说明 |
|---------|-----|---------|------|
| CPU使用率 | ✅ | ✅ | 应用CPU占用百分比 |
| 内存使用量 | ✅ | ✅ | 物理内存占用(MB) |
| 帧率(FPS) | ✅ | ✅ | 应用渲染帧率 |
| 线程数 | ✅(总数) | ✅(详情) | iOS显示总数，Android支持状态分析 |
| 磁盘I/O | ✅ | ✅ | 读写速度监控 |
| 数据统计 | ✅ | ✅ | 当前值/平均值/最大值 |
| 拖拽排序 | ✅ | ✅ | 面板可拖拽重新排列 |

## 🔧 技术实现

### 跨平台架构
- **统一Web框架**: Flask + Socket.IO + Chart.js
- **相同界面设计**: 一致的用户体验和交互方式
- **相同端口规划**: iOS(5002) / Android(5003)
- **模块化设计**: 平台特定逻辑分离，共享Web资源

### 核心逻辑保持一致
- `TunnelManager`: 完全复制原始tunnel管理逻辑
- `PerformanceAnalyzer`: 保持相同的数据收集方式
- 权限检查: 完全相同的管理员权限验证

### Web技术栈
- **后端**: Flask + Socket.IO (实时数据传输)
- **前端**: HTML5 + Chart.js (图表渲染)
- **样式**: CSS3 (Apple Design风格)

### 数据流程
1. Web服务器复制main.py的完整逻辑
2. 通过WebSocket实时推送性能数据
3. 前端Chart.js渲染实时曲线图
4. 同时保持原始console输出

## 📋 系统要求

### 完整功能（iOS + Android）
- **macOS** (推荐) / **Linux**
- Python 3.8+
- 管理员权限
- iOS设备已连接并信任电脑

### Android 监控（Windows 支持）
- **Windows 10/11** / macOS / Linux
- Python 3.8+
- Android SDK Platform Tools (ADB)
- Android设备已开启USB调试

📖 **Windows 用户请查看**: [Windows 平台使用说明](docs/README_Windows.md)

## 🛠️ 依赖包

### macOS/Linux (完整功能)
主要依赖包（安装 `requirements.txt`）:
- `py_ios_device`: iOS设备通信
- `pymobiledevice3`: iOS设备管理
- `flask`: Web框架
- `flask-socketio`: 实时通信
- `psutil`: 系统信息

### Windows (仅 Android)
精简依赖包（安装 `requirements_windows.txt`）:
- `flask`: Web框架
- `flask-socketio`: 实时通信
- `psutil`: 系统信息

## 💡 使用技巧

### 通用技巧
1. **面板拖拽**: 点击面板标题左侧的 ⋮⋮ 图标可拖拽调整显示顺序
2. **数据保留**: 图表最多保留50个数据点，自动滚动显示
3. **实时性**: 数据每秒更新，保持一致的监控频率
4. **数据统计**: 查看当前值、平均值、最大值等统计信息
5. **智能交互**: 
   - 选择设备后自动加载应用列表，无需手动刷新
   - 应用列表显示真实名称，方便快速识别

### iOS特定
- 确保设备通过USB连接并信任电脑
- 需要管理员权限访问iOS设备
- 支持iOS 15+系统（iOS 17+推荐）

### Android特定  
- 开启开发者选项和USB调试
- 安装ADB工具并确保设备授权
- 支持线程详情分析和智能分类
- 应用名称自动识别，显示格式：`应用名称 (包名)`

## 🔍 故障排除

### 连接问题
- 检查iOS设备是否已连接
- 确认设备已信任此电脑
- 验证是否有管理员权限

### 监控问题
- 确认Bundle ID输入正确
- 检查应用是否正在运行
- 查看控制台输出的详细信息

### Web界面问题
- 确认端口5000未被占用
- 检查防火墙设置
- 尝试刷新浏览器页面

## 📝 注意事项

- Web可视化系统完全基于原始main.py逻辑构建
- 原始main.py文件保持不变，可继续单独使用
- Web界面仅增加可视化功能，不影响核心监控逻辑
- 建议在开发和测试环境中使用

## 🤝 技术说明

这个Web可视化系统是在不修改原始`main.py`代码的前提下，完全复制其核心逻辑并增加Web可视化功能。这确保了:

1. **逻辑一致性**: 与原始脚本完全相同的数据收集方式
2. **功能完整性**: 保持所有原有功能不变
3. **扩展性**: 增加了实时图表和Web界面
4. **兼容性**: 原始脚本可继续独立使用

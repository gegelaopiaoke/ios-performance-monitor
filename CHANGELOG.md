# 📋 更新记录 (CHANGELOG)

## [2025.10.14] - 大版本更新：跨平台监控支持 + 端口规范化

### 🎉 新增功能 (New Features)

#### 🤖 Android平台支持
- **新增**: Android性能监控完整功能
  - `android_main.py` - Android性能监控核心脚本
  - `android_web_visualizer.py` - Android Web可视化界面
  - `start_android_monitor.py` - Android监控启动脚本
- **新增**: Android线程详情分析功能
  - 支持线程状态监控（运行中/睡眠中等）
  - 智能线程分类（系统/网络/广告/UI渲染等）
  - 线程分布统计和可视化展示
- **新增**: Android专用Web界面
  - `templates/android_index.html` - Android专用可视化界面
  - `static/android_script.js` - Android前端交互逻辑
  - 完全复用iOS界面设计，保持跨平台一致性

#### 🔧 开发工具增强
- **新增**: `check_tools.sh` - 自动化环境检测工具
- **新增**: `install_ios_tools.sh` - iOS工具链安装脚本
- **新增**: 多个iOS监控变体脚本
  - `ios_device_monitor.py` - 设备监控专用版本
  - `ios_real_monitor.py` - 实时监控优化版本
  - `ios_real_monitor_fixed.py` - 修复版实时监控
  - `ios_simple_monitor.py` - 简化版监控工具

#### 🐛 调试与分析工具
- **新增**: `debug.py` - 综合调试工具
- **新增**: `debug_dvt_output.py` - DVT输出调试
- **新增**: `fixed_process_parser.py` - 进程解析器修复版
- **新增**: `线程分析.py` - 专门的线程分析工具

#### 📚 文档完善
- **新增**: `README_Android.md` - Android平台专用文档
- **新增**: 详细的跨平台使用指南

### 🔧 改进优化 (Improvements)

#### 🌐 端口规范化
- **修改**: iOS监控端口从5001调整为5002
- **规范**: 多平台端口分配规则
  - iOS: 端口5002
  - Android: 端口5003
  - 为未来平台预留端口5004+

#### 🎨 界面优化
- **增强**: `templates/index.html` - iOS界面功能扩展
- **新增**: `templates/index_working.html` - 工作版本界面备份
- **优化**: Web可视化交互体验

#### ⚡ 性能优化
- **改进**: `web_visualizer.py` - Web服务器性能优化
- **增强**: 实时数据传输稳定性
- **优化**: 内存使用和数据处理效率

### 🔄 技术栈更新 (Technical Updates)

#### 📦 依赖管理
- 保持原有依赖版本稳定性
- 新增Android监控所需的ADB工具支持
- 优化虚拟环境配置

#### 🏗️ 架构改进
- **跨平台架构**: 统一的Web可视化框架
- **模块化设计**: iOS和Android监控模块独立
- **代码复用**: 前端界面和交互逻辑共享

### 📊 代码统计 (Code Statistics)

```
文件变更统计：
- 新增文件：18个
- 修改文件：3个
- 总计代码行数：+9,270行
- 核心功能文件：
  * Android监控：901行 (android_web_visualizer.py)
  * 前端脚本：892行 (android_script.js)  
  * 界面模板：3,567行 (index_working.html)
```

### 🎯 功能对比 (Feature Comparison)

| 功能特性 | iOS | Android | 说明 |
|---------|-----|---------|------|
| CPU监控 | ✅ | ✅ | 实时CPU使用率 |
| 内存监控 | ✅ | ✅ | 物理内存占用 |
| FPS监控 | ✅ | ✅ | 应用帧率监控 |
| 线程监控 | ✅ (总数) | ✅ (详情) | Android支持线程详情分析 |
| 磁盘I/O | ✅ | ✅ | 读写速度监控 |
| Web可视化 | ✅ | ✅ | 实时图表展示 |
| 设备管理 | ✅ | ✅ | 多设备支持 |

### 📋 已知问题 (Known Issues)

- iOS平台无法获取单个线程详情（系统限制）
- Android需要ADB工具和设备调试权限
- 部分旧版本Android设备可能存在兼容性问题

### 🔮 下个版本计划 (Next Version)

- [ ] 增加GPU使用率监控
- [ ] 实现电池消耗监控  
- [ ] 添加网络流量监控
- [ ] 支持数据导出和历史记录
- [ ] 实现告警和阈值设置

---

### 🚀 如何升级 (How to Upgrade)

1. **拉取最新代码**：
   ```bash
   git pull origin main
   ```

2. **iOS监控（端口已更新）**：
   ```bash
   python start_web_monitor.py
   # 访问: http://localhost:5002
   ```

3. **Android监控（新功能）**：
   ```bash  
   python start_android_monitor.py
   # 访问: http://localhost:5003
   ```

4. **环境检测**：
   ```bash
   bash check_tools.sh
   ```

---

### 👥 贡献者 (Contributors)

- **万怡昊** - 主要开发者
- 提交时间：2025年10月14日 09:52:52
- 提交ID：4011107

### 📞 支持 (Support)

如遇到问题，请参考：
1. 项目README文档
2. 各平台专用文档
3. 调试工具输出信息
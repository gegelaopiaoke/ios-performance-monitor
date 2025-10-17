# GitHub Actions 自动构建说明

## 📦 自动构建的 exe 文件

此 workflow 会自动构建两个 Windows exe 文件：

1. **Android性能监控.exe** - 轻量版（推荐）
2. **跨平台性能监控.exe** - 完整版

## 🚀 触发方式

### 自动触发
- 推送代码到 `main` 或 `master` 分支
- 创建标签（如 `v1.0.0`）

### 手动触发
1. 进入 GitHub 仓库的 **Actions** 标签
2. 选择 **Build Windows EXE** workflow
3. 点击 **Run workflow** 按钮

## 📥 下载构建产物

构建完成后（约 5-10 分钟）：

1. 在 **Actions** 页面找到完成的构建（绿色 ✅）
2. 点击进入构建详情
3. 滚动到底部的 **Artifacts** 区域
4. 下载：
   - `Android性能监控-Windows.zip`
   - `跨平台性能监控-Windows.zip`
5. 解压得到 `.exe` 文件

## 📋 构建环境

- 操作系统: Windows Server (最新版)
- Python: 3.10
- 打包工具: PyInstaller
- 保留时间: 30 天

## ✅ 构建状态

查看最新构建状态：进入仓库的 Actions 标签页

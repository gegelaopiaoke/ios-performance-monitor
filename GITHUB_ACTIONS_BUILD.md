# 使用 GitHub Actions 自动打包 Windows EXE

## 📋 前置条件

- GitHub 账号
- 项目已上传到 GitHub 仓库

---

## 🚀 使用步骤

### 1. 上传代码到 GitHub

如果还没有创建 GitHub 仓库：

```bash
cd /Users/apple/Downloads/ios性能

# 初始化 Git 仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "准备打包 Windows EXE"

# 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送到 GitHub
git push -u origin main
```

### 2. GitHub Actions 会自动触发构建

推送代码后，GitHub Actions 会自动开始构建 Windows EXE。

或者手动触发：
1. 访问你的 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择 "Build Windows EXE" workflow
4. 点击 "Run workflow" 按钮

### 3. 下载构建好的 EXE

构建完成后（约 5-10 分钟）：

1. 在 "Actions" 页面找到最新的构建
2. 点击进入构建详情
3. 在 "Artifacts" 区域找到：
   - `Android性能监控-Windows` - Android 监控版本
   - `跨平台性能监控-Windows` - 完整版本
4. 点击下载 ZIP 文件
5. 解压后得到 `.exe` 文件

---

## 🏷️ 发布版本（可选）

如果要创建正式版本：

```bash
# 创建标签
git tag -a v1.0.0 -m "发布 1.0.0 版本"

# 推送标签
git push origin v1.0.0
```

GitHub Actions 会自动：
1. 构建 EXE
2. 创建 GitHub Release
3. 上传 EXE 到 Release 页面

---

## 📦 构建产物

GitHub Actions 会自动构建两个版本：

### Android 监控版（推荐）
- 文件名: `Android性能监控.exe`
- 大小: 约 25-30MB
- 功能: Android 设备性能监控

### 统一监控版（完整）
- 文件名: `跨平台性能监控.exe`
- 大小: 约 35-40MB
- 功能: iOS + Android 性能监控

---

## ⚙️ Workflow 配置说明

已创建的 workflow 文件：`.github/workflows/build-windows.yml`

**触发条件:**
- 推送到 `main` 或 `master` 分支
- 创建标签（如 `v1.0.0`）
- 手动触发

**构建环境:**
- Windows Server (最新版)
- Python 3.10
- PyInstaller

**构建时间:**
- Android 版本: 约 5 分钟
- 统一版本: 约 6 分钟

---

## ✅ 优点

- ✅ 完全免费
- ✅ 自动化构建
- ✅ 真实的 Windows 环境
- ✅ 无需本地 Windows 电脑
- ✅ 可重复构建
- ✅ 保留历史版本

---

## 📝 注意事项

1. **首次构建可能较慢** - 需要下载依赖包
2. **构建保留 30 天** - Artifacts 会在 30 天后自动删除
3. **私有仓库限制** - 私有仓库每月有免费构建时长限制
4. **Release 永久保留** - 通过标签触发的 Release 会永久保留

---

## 🔍 查看构建日志

如果构建失败：

1. 进入 Actions 页面
2. 点击失败的构建
3. 查看详细日志
4. 根据错误信息修复问题

---

## 💡 提示

**推荐构建顺序:**
1. 先推送代码，让 GitHub Actions 自动构建
2. 如果构建成功，可以创建标签发布正式版本
3. 从 Artifacts 或 Release 下载 EXE 文件

**本地测试:**
虽然你没有 Windows 电脑，但可以：
- 在 macOS 上测试 Python 代码逻辑
- 使用 GitHub Actions 验证 Windows 打包
- 请有 Windows 电脑的朋友帮忙测试 EXE

---

## 🎯 快速开始

```bash
# 1. 提交并推送代码
git add .
git commit -m "添加 GitHub Actions 自动打包"
git push origin main

# 2. 访问 GitHub Actions 页面查看构建进度
# https://github.com/你的用户名/你的仓库名/actions

# 3. 构建完成后下载 EXE
```

就是这么简单！🎉

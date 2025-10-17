# 如何在没有 Windows 电脑的情况下打包 EXE

## 🎯 最简单的方法：使用 GitHub Actions（推荐）

### 只需 3 步！

#### 1️⃣ 上传代码到 GitHub

```bash
cd /Users/apple/Downloads/ios性能

# 如果还没有 Git 仓库
git init
git add .
git commit -m "准备打包 Windows EXE"

# 关联 GitHub 仓库（先在 GitHub 网站创建仓库）
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

#### 2️⃣ 触发自动打包

推送代码后，GitHub Actions 会自动开始打包。

或手动触发：
1. 打开你的 GitHub 仓库
2. 点击顶部的 **"Actions"** 标签
3. 选择 **"Build Windows EXE"**
4. 点击 **"Run workflow"** 按钮
5. 点击绿色的 **"Run workflow"**

#### 3️⃣ 下载打包好的 EXE

等待 5-10 分钟后：
1. 在 Actions 页面找到完成的构建（绿色 ✅）
2. 点击进入构建详情
3. 滚动到底部找到 **"Artifacts"**
4. 下载你需要的版本：
   - **Android性能监控-Windows.zip** （推荐，轻量版）
   - **跨平台性能监控-Windows.zip** （完整版）
5. 解压 ZIP 文件得到 `.exe`

---

## 📦 会得到什么？

### Android性能监控.exe
- 大小：约 25MB
- 功能：Android 设备性能监控
- 系统要求：Windows 7/8/10/11 + ADB

### 跨平台性能监控.exe
- 大小：约 35MB
- 功能：iOS + Android 性能监控
- 系统要求：Windows 7/8/10/11 + ADB + iTunes

---

## ✅ 优势

- ✅ **完全免费** - GitHub Actions 对公开仓库免费
- ✅ **无需 Windows** - 在云端 Windows 环境自动构建
- ✅ **自动化** - 每次推送代码都会自动打包
- ✅ **可靠** - 使用真实的 Windows 环境

---

## 📱 其他方案

如果不想用 GitHub Actions：

### 方案 A: 借用朋友的 Windows 电脑
1. 把项目文件夹拷贝到 U盘
2. 在 Windows 电脑上双击 `build_windows.bat`
3. 等待打包完成
4. 从 `dist\` 文件夹拿回 exe

### 方案 B: 使用云端 Windows 虚拟机
- Azure、AWS、Google Cloud 都有免费试用
- 创建 Windows 虚拟机
- 上传代码并运行 `build_windows.bat`

---

## ❓ 常见问题

**Q: GitHub Actions 构建失败怎么办？**
A: 点击失败的构建查看日志，通常是依赖问题，可以修改 workflow 配置。

**Q: 私有仓库可以用吗？**
A: 可以，但有每月免费时长限制（2000 分钟）。

**Q: 打包好的 exe 在哪里？**
A: 在 Actions 构建页面的 "Artifacts" 区域下载。

**Q: 可以测试 exe 吗？**
A: 需要找有 Windows 电脑的朋友帮忙测试。

---

## 🎉 总结

**没有 Windows 电脑？没问题！**

只需将代码推送到 GitHub，就能自动在云端 Windows 环境打包成 exe，完全免费！

立即开始：
1. 上传代码到 GitHub ✅
2. GitHub Actions 自动打包 ✅
3. 下载 exe 文件 ✅

就是这么简单！🚀

#!/bin/bash

echo "🛠️  iOS 监控工具自动安装脚本"
echo "=============================="

# 检查操作系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅支持 macOS 系统"
    exit 1
fi

# 安装 Homebrew
if ! command -v brew >/dev/null 2>&1; then
    echo "📦 安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # 设置环境变量
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
        export PATH="/opt/homebrew/bin:$PATH"
    fi

    echo "✅ Homebrew 安装完成"
else
    echo "✅ Homebrew 已安装"
fi

# 安装 Xcode 命令行工具
if ! xcode-select -p >/dev/null 2>&1; then
    echo "🔧 安装 Xcode 命令行工具..."
    sudo xcode-select --install
    echo "⏳ 请在弹出窗口中完成 Xcode 命令行工具安装"
    echo "安装完成后请重新运行此脚本"
    exit 0
else
    echo "✅ Xcode 命令行工具已安装"
fi

# 更新 Homebrew
echo "🔄 更新 Homebrew..."
brew update

# 安装 libimobiledevice
echo "📱 安装 libimobiledevice..."
brew install libimobiledevice ideviceinstaller

# 验证安装
echo ""
echo "🔍 验证安装结果:"

tools=("idevice_id" "ideviceinstaller" "sample")
all_good=true

for tool in "${tools[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "✅ $tool: $(which $tool)"
    else
        echo "❌ $tool: 未找到"
        all_good=false
    fi
done

if $all_good; then
    echo ""
    echo "🎉 所有工具安装成功!"
    echo "💡 现在可以运行: python3 ios_real_monitor_fixed.py <应用名>"
else
    echo ""
    echo "⚠️  部分工具安装失败，请手动检查"
fi

# 检查设备连接
echo ""
echo "📱 检查设备连接:"
devices=$(idevice_id -l 2>/dev/null)
if [ -n "$devices" ]; then
    echo "✅ 找到设备: $devices"
else
    echo "❌ 未找到设备，请连接 iOS 设备"
fi

echo ""
echo "🏁 安装脚本执行完成!"

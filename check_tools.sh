#!/bin/bash

echo "🔍 检查 iOS 监控工具环境"
echo "=========================="

# 检查操作系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此工具仅支持 macOS 系统"
    exit 1
fi
echo "✅ macOS 系统检查通过"

# 检查 Homebrew
if command -v brew >/dev/null 2>&1; then
    echo "✅ Homebrew 已安装: $(brew --version | head -1)"
else
    echo "❌ Homebrew 未安装"
    echo "💡 运行安装脚本: bash install_ios_tools.sh"
fi

# 检查 Xcode 命令行工具
if xcode-select -p >/dev/null 2>&1; then
    echo "✅ Xcode 命令行工具已安装: $(xcode-select -p)"
else
    echo "❌ Xcode 命令行工具未安装"
    echo "💡 运行: sudo xcode-select --install"
fi

# 检查 libimobiledevice 工具
tools=("idevice_id" "ideviceinstaller")
for tool in "${tools[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "✅ $tool 已安装: $(which $tool)"
    else
        echo "❌ $tool 未找到"
        echo "💡 运行: brew install libimobiledevice"
    fi
done

# 检查 sample 工具
if command -v sample >/dev/null 2>&1; then
    echo "✅ sample 工具已安装: $(which sample)"
else
    echo "❌ sample 工具未找到"
    echo "💡 请安装 Xcode 命令行工具"
fi

# 检查设备连接
echo ""
echo "📱 检查 iOS 设备连接:"
if command -v idevice_id >/dev/null 2>&1; then
    devices=$(idevice_id -l 2>/dev/null)
    if [ -n "$devices" ]; then
        echo "✅ 找到设备:"
        echo "$devices" | while read -r device; do
            echo "   📱 $device"
        done
    else
        echo "❌ 未找到连接的设备"
        echo "💡 请确保设备已连接并信任此电脑"
    fi
else
    echo "⚠️  无法检查设备（idevice_id 未安装）"
fi

echo ""
echo "🎯 环境检查完成!"

#!/usr/bin/env python3
# Android性能监控启动脚本

import subprocess
import sys
import os

def main():
    # 切换到项目目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🤖 启动Android性能监控...")
    print("=" * 60)
    print("📋 系统要求:")
    print("• 已安装Android SDK Platform Tools (ADB)")
    print("• Android设备已开启开发者选项和USB调试")
    print("• 设备已通过USB连接到电脑")
    print("=" * 60)
    
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("❌ 需要Python 3.8或更高版本")
            return
        
        # 运行Android性能监控
        subprocess.run([sys.executable, 'android_web_visualizer.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
    except Exception as e:
        print(f"❌ 意外错误: {e}")

if __name__ == '__main__':
    main()
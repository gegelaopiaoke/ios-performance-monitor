#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无密码启动iOS性能监控（跳过权限检查）
"""
import os
import sys
import subprocess
import webbrowser
import time
import threading

def main():
    print("🚀 启动iOS性能监控Web可视化界面（无密码模式）...")
    
    # 检查虚拟环境
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_path):
        print("❌ 未找到虚拟环境，请先运行以下命令创建虚拟环境:")
        print("python3.13 -m venv venv")
        print("source venv/bin/activate")
        print("pip install -r requirements.txt")
        return
    
    # 直接使用虚拟环境的python启动
    python_path = os.path.join(venv_path, 'bin', 'python')
    web_visualizer_path = os.path.join(os.path.dirname(__file__), 'web_visualizer.py')
    
    print("📱 正在启动Web服务器...")
    print("💡 提示: 启动后会自动打开浏览器访问 http://localhost:5001")
    print("🔧 请确保iOS设备已连接并信任此电脑")
    print("⚠️  注意: 如果出现权限问题，可能需要手动授权iOS设备访问")
    print()
    
    # 延迟打开浏览器
    def open_browser():
        time.sleep(3)  # 等待服务器启动
        try:
            webbrowser.open('http://localhost:5001')
            print("🌐 已自动打开浏览器")
        except:
            print("🌐 请手动打开浏览器访问: http://localhost:5001")
    
    # 在后台线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动Web服务器（不需要sudo）
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(__file__)
        subprocess.run([python_path, web_visualizer_path], env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 如果仍有权限问题，请尝试:")
        print("   1. 确保iOS设备已信任此电脑")
        print("   2. 重新连接iOS设备")
        print("   3. 检查Xcode是否已安装并配置正确")

if __name__ == '__main__':
    main()

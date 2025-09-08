#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动输入密码启动iOS性能监控
"""
import os
import sys
import subprocess
import webbrowser
import time
import threading
import pexpect

def main():
    print("🚀 启动iOS性能监控Web可视化界面（自动密码模式）...")
    
    # 检查虚拟环境
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_path):
        print("❌ 未找到虚拟环境，请先运行以下命令创建虚拟环境:")
        print("python3.13 -m venv venv")
        print("source venv/bin/activate")
        print("pip install -r requirements.txt")
        return
    
    python_path = os.path.join(venv_path, 'bin', 'python')
    web_visualizer_path = os.path.join(os.path.dirname(__file__), 'web_visualizer.py')
    
    print("📱 正在启动Web服务器...")
    print("💡 提示: 启动后会自动打开浏览器访问 http://localhost:5001")
    print("🔧 自动输入密码: 123456")
    print()
    
    # 延迟打开浏览器
    def open_browser():
        time.sleep(5)  # 等待服务器启动
        try:
            webbrowser.open('http://localhost:5001')
            print("🌐 已自动打开浏览器")
        except:
            print("🌐 请手动打开浏览器访问: http://localhost:5001")
    
    # 在后台线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 使用sudo启动，自动输入密码
    try:
        cmd = f"sudo {python_path} {web_visualizer_path}"
        child = pexpect.spawn(cmd)
        
        # 等待密码提示并自动输入
        try:
            child.expect('Password:', timeout=10)
            child.sendline('123456')
            print("🔑 密码已自动输入")
        except pexpect.TIMEOUT:
            print("⚠️  未检测到密码提示，可能已有权限")
        
        # 进入交互模式
        child.interact()
        
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请检查:")
        print("   1. 密码是否正确（123456）")
        print("   2. iOS设备是否已连接并信任此电脑")
        print("   3. 是否有sudo权限")

if __name__ == '__main__':
    main()

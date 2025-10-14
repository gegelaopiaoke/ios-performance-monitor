#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS性能监控Web可视化启动脚本
"""
import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("🚀 启动iOS性能监控Web可视化界面...")
    
    # 检查虚拟环境
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_path):
        print("❌ 未找到虚拟环境，请先运行以下命令创建虚拟环境:")
        print("python3.13 -m venv venv")
        print("source venv/bin/activate")
        print("pip install -r requirements.txt")
        return
    
    # 激活虚拟环境并启动Web服务器
    web_visualizer_path = os.path.join(os.path.dirname(__file__), 'web_visualizer.py')
    
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')
        cmd = f'"{activate_script}" && python "{web_visualizer_path}"'
    else:  # macOS/Linux
        activate_script = os.path.join(venv_path, 'bin', 'activate')
        # 直接使用虚拟环境的python，不需要sudo
        python_path = os.path.join(venv_path, 'bin', 'python')
        cmd = f'"{python_path}" "{web_visualizer_path}"'
    
    print("📱 正在启动Web服务器...")
    print("💡 提示: 启动后会自动打开浏览器访问 http://localhost:5002")
    print("🔧 请确保iOS设备已连接并信任此电脑")
    print()
    
    # 延迟打开浏览器
    def open_browser():
        time.sleep(3)  # 等待服务器启动
        try:
            webbrowser.open('http://localhost:5002')
            print("🌐 已自动打开浏览器")
        except:
            print("🌐 请手动打开浏览器访问: http://localhost:5002")
    
    # 在后台线程中打开浏览器
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动Web服务器
    try:
        subprocess.run(cmd, shell=True, check=True)
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请检查是否有管理员权限，以及iOS设备连接状态")

if __name__ == '__main__':
    main()

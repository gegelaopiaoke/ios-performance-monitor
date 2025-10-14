#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS性能监控启动脚本 - 从项目根目录启动
"""
import os
import sys
import subprocess
import webbrowser
import time
import threading

def main():
    print("🍎 启动iOS性能监控Web可视化界面...")
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 检查虚拟环境
    venv_path = os.path.join(project_root, 'venv')
    if not os.path.exists(venv_path):
        print("❌ 未找到虚拟环境，请先运行以下命令创建虚拟环境:")
        print("python3 -m venv venv")
        print("source venv/bin/activate")
        print("pip install -r requirements.txt")
        return
    
    # iOS监控脚本路径
    ios_script_path = os.path.join(project_root, 'ios', 'web_visualizer.py')
    
    if not os.path.exists(ios_script_path):
        print(f"❌ 找不到iOS监控脚本: {ios_script_path}")
        return
    
    # 使用虚拟环境的Python
    if os.name == 'nt':  # Windows
        python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:  # macOS/Linux
        python_path = os.path.join(venv_path, 'bin', 'python')
    
    print("📱 正在启动iOS监控服务器...")
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
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动iOS监控服务器
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = project_root
        subprocess.run([python_path, ios_script_path], env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 iOS监控已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请检查是否有管理员权限，以及iOS设备连接状态")

if __name__ == '__main__':
    main()
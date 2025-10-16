#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一性能监控启动器 - 支持iOS和Android同时监控
内存泄漏检测功能跨平台支持
"""

import os
import sys
import subprocess
import time
import threading
import socket

def get_port_process(port):
    """获取占用端口的进程PID"""
    try:
        import subprocess
        # macOS/Linux
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split()[0])
    except:
        pass
    return None

def kill_process(pid):
    """杀死指定进程"""
    try:
        import subprocess
        subprocess.run(['kill', '-9', str(pid)], timeout=5)
        return True
    except:
        return False

def check_and_handle_port(port, port_name):
    """检查端口并处理占用情况"""
    pid = get_port_process(port)
    
    if pid:
        print(f"\n⚠️  {port_name}端口 {port} 已被进程 {pid} 占用")
        choice = input(f"是否kill掉进程 {pid}? (y/n): ").strip().lower()
        
        if choice == 'y':
            if kill_process(pid):
                print(f"✅ 进程 {pid} 已被终止")
                time.sleep(1)  # 等待端口释放
                return True
            else:
                print(f"❌ 无法终止进程 {pid}")
                return False
        else:
            print(f"❌ 端口 {port} 仍被占用，无法启动")
            return False
    
    return True

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return 'localhost'

def check_ios_device():
    """检查iOS设备连接状态"""
    try:
        # 尝试pymobiledevice3
        result = subprocess.run(
            [sys.executable, '-m', 'pymobiledevice3', 'usbmux', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            devices = json.loads(result.stdout)
            return len(devices) > 0
    except:
        pass
    
    # 尝试tidevice
    try:
        result = subprocess.run(['tidevice', 'list'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except:
        pass
    
    return False

def check_android_device():
    """检查Android设备连接状态"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # 跳过第一行"List of devices attached"
            devices = [line for line in lines[1:] if line.strip() and 'device' in line]
            return len(devices) > 0
    except:
        pass
    return False

def start_ios_monitor():
    """启动iOS监控服务"""
    print("\n🍎 启动iOS性能监控...")
    ios_script = os.path.join(os.path.dirname(__file__), 'ios', 'web_visualizer.py')
    
    try:
        subprocess.run([sys.executable, ios_script])
    except KeyboardInterrupt:
        print("\n⏹️ iOS监控已停止")
    except Exception as e:
        print(f"\n❌ iOS监控启动失败: {e}")

def start_android_monitor():
    """启动Android监控服务"""
    print("\n🤖 启动Android性能监控...")
    android_script = os.path.join(os.path.dirname(__file__), 'android', 'android_web_visualizer.py')
    
    try:
        subprocess.run([sys.executable, android_script])
    except KeyboardInterrupt:
        print("\n⏹️ Android监控已停止")
    except Exception as e:
        print(f"\n❌ Android监控启动失败: {e}")

def show_banner():
    """显示启动横幅"""
    print("=" * 70)
    print("🚀 跨平台性能监控工具 - 统一启动器 v1.1.0")
    print("=" * 70)
    print("✨ 功能特性:")
    print("  • 同时支持iOS和Android设备监控")
    print("  • 智能内存泄漏检测（iOS/Android通用）")
    print("  • 实时性能数据可视化")
    print("  • 灵活的配置和告警系统")
    print("=" * 70)

def detect_devices():
    """检测已连接的设备"""
    print("\n🔍 检测设备连接状态...")
    
    ios_connected = check_ios_device()
    android_connected = check_android_device()
    
    print(f"  {'✅' if ios_connected else '❌'} iOS设备: {'已连接' if ios_connected else '未连接'}")
    print(f"  {'✅' if android_connected else '❌'} Android设备: {'已连接' if android_connected else '未连接'}")
    
    return ios_connected, android_connected

def check_ports():
    """检查端口可用性（仅用于显示状态）"""
    print("\n🔌 检查端口状态...")
    
    ios_port = 5002
    android_port = 5003
    
    ios_pid = get_port_process(ios_port)
    android_pid = get_port_process(android_port)
    
    ios_available = ios_pid is None
    android_available = android_pid is None
    
    if ios_pid:
        print(f"  ❌ iOS端口 {ios_port}: 被进程 {ios_pid} 占用")
    else:
        print(f"  ✅ iOS端口 {ios_port}: 可用")
    
    if android_pid:
        print(f"  ❌ Android端口 {android_port}: 被进程 {android_pid} 占用")
    else:
        print(f"  ✅ Android端口 {android_port}: 可用")
    
    return ios_available, android_available

def show_access_info(local_ip):
    """显示访问信息"""
    print("\n" + "=" * 70)
    print("📱 访问地址:")
    print("-" * 70)
    print(f"🍎 iOS监控:      http://localhost:5002  或  http://{local_ip}:5002")
    print(f"🤖 Android监控:  http://localhost:5003  或  http://{local_ip}:5003")
    print("=" * 70)
    print("\n💡 使用提示:")
    print("  • 在浏览器中打开对应的地址即可查看监控界面")
    print("  • 支持局域网内其他设备访问（使用IP地址）")
    print("  • 按 Ctrl+C 停止所有监控服务")
    print("  • 内存泄漏检测功能已自动启用")
    print("=" * 70)

def interactive_mode():
    """交互式启动模式"""
    show_banner()
    
    # 检测设备
    ios_connected, android_connected = detect_devices()
    
    # 检查端口（仅显示状态）
    check_ports()
    
    print("\n🎯 启动选项:")
    print("  1. 启动iOS监控 (端口 5002)")
    print("  2. 启动Android监控 (端口 5003)")
    print("  3. 同时启动iOS和Android监控")
    print("  4. 自动检测并启动（推荐）")
    print("  0. 退出")
    
    choice = input("\n请选择启动模式 [1-4, 0]: ").strip()
    
    local_ip = get_local_ip()
    
    if choice == '1':
        # 只启动iOS
        if not check_and_handle_port(5002, 'iOS'):
            return
        show_access_info(local_ip)
        print("\n🍎 启动iOS监控服务...")
        start_ios_monitor()
        
    elif choice == '2':
        # 只启动Android
        if not check_and_handle_port(5003, 'Android'):
            return
        show_access_info(local_ip)
        print("\n🤖 启动Android监控服务...")
        start_android_monitor()
        
    elif choice == '3':
        # 同时启动两个服务
        if not check_and_handle_port(5002, 'iOS'):
            return
        if not check_and_handle_port(5003, 'Android'):
            return
        show_access_info(local_ip)
        print("\n🚀 同时启动iOS和Android监控服务...")
        
        # 在单独的线程中启动iOS监控
        ios_thread = threading.Thread(target=start_ios_monitor, daemon=True)
        ios_thread.start()
        
        # 等待iOS服务启动
        time.sleep(2)
        
        # 在主线程中启动Android监控
        start_android_monitor()
        
    elif choice == '4':
        # 自动检测模式
        print("\n🤖 自动检测模式...")
        
        if ios_connected and android_connected:
            print("检测到iOS和Android设备，将同时启动两个监控服务")
            if not check_and_handle_port(5002, 'iOS'):
                return
            if not check_and_handle_port(5003, 'Android'):
                return
            show_access_info(local_ip)
            
            ios_thread = threading.Thread(target=start_ios_monitor, daemon=True)
            ios_thread.start()
            time.sleep(2)
            start_android_monitor()
            
        elif ios_connected:
            print("检测到iOS设备，启动iOS监控")
            if not check_and_handle_port(5002, 'iOS'):
                return
            show_access_info(local_ip)
            start_ios_monitor()
            
        elif android_connected:
            print("检测到Android设备，启动Android监控")
            if not check_and_handle_port(5003, 'Android'):
                return
            show_access_info(local_ip)
            start_android_monitor()
            
        else:
            print("❌ 未检测到任何设备连接")
            print("💡 请确保:")
            print("  • iOS设备已通过USB连接并信任此电脑")
            print("  • Android设备已开启USB调试模式")
            print("  • 已安装必要的工具 (pymobiledevice3/tidevice/adb)")
            
    elif choice == '0':
        print("👋 已退出")
        return
        
    else:
        print("❌ 无效的选择")

def quick_start_mode():
    """快速启动模式（命令行参数）"""
    if len(sys.argv) < 2:
        interactive_mode()
        return
    
    mode = sys.argv[1].lower()
    local_ip = get_local_ip()
    
    show_banner()
    
    if mode in ['ios', 'i']:
        if not check_and_handle_port(5002, 'iOS'):
            return
        show_access_info(local_ip)
        start_ios_monitor()
        
    elif mode in ['android', 'a']:
        if not check_and_handle_port(5003, 'Android'):
            return
        show_access_info(local_ip)
        start_android_monitor()
        
    elif mode in ['both', 'all', 'b']:
        if not check_and_handle_port(5002, 'iOS'):
            return
        if not check_and_handle_port(5003, 'Android'):
            return
        show_access_info(local_ip)
        print("\n🚀 同时启动iOS和Android监控服务...")
        
        ios_thread = threading.Thread(target=start_ios_monitor, daemon=True)
        ios_thread.start()
        time.sleep(2)
        start_android_monitor()
        
    elif mode in ['auto']:
        detect_devices()
        interactive_mode()
        
    else:
        print(f"❌ 未知参数: {mode}")
        print("\n使用方法:")
        print(f"  {sys.argv[0]} ios        # 启动iOS监控")
        print(f"  {sys.argv[0]} android    # 启动Android监控")
        print(f"  {sys.argv[0]} both       # 同时启动两个平台")
        print(f"  {sys.argv[0]} auto       # 自动检测并启动")
        print(f"  {sys.argv[0]}            # 交互式启动")

def main():
    """主函数"""
    try:
        quick_start_mode()
    except KeyboardInterrupt:
        print("\n\n⏹️ 所有监控服务已停止")
        print("👋 感谢使用！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()


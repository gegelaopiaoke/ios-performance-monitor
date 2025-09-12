#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试设备连接和FPS数据获取
"""
import subprocess
import sys
import time

def test_device_connection():
    """测试设备连接"""
    try:
        # 测试设备列表
        print("🔍 测试设备连接...")
        cmd = [sys.executable, "-m", "pymobiledevice3", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"设备列表命令: {' '.join(cmd)}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
            
        # 测试tunnel连接
        print("\n🔍 测试Tunnel连接...")
        cmd = [sys.executable, "-m", "pymobiledevice3", "remote", "start-tunnel"]
        print(f"启动Tunnel命令: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 读取几行输出
        for i in range(20):
            line = process.stdout.readline()
            if line:
                print(f"Tunnel输出: {line.strip()}")
                if "--rsd" in line:
                    print("✅ 成功获取到Tunnel信息")
                    break
            else:
                time.sleep(0.1)
                
        # 终止进程
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == '__main__':
    test_device_connection()
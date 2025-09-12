#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试FPS数据获取
"""
import subprocess
import sys

def test_fps():
    """测试FPS数据获取"""
    try:
        # 运行pymobiledevice3命令获取FPS数据
        cmd = [sys.executable, "-m", "pymobiledevice3", "developer", "dvt", "fps", "--pid", "0"]
        print(f"运行命令: {' '.join(cmd)}")
        
        # 启动进程并读取输出
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 读取几行输出
        for i in range(10):
            line = process.stdout.readline()
            if line:
                print(f"输出: {line.strip()}")
            else:
                break
                
        # 终止进程
        process.terminate()
        process.wait()
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == '__main__':
    print("🔍 测试FPS数据获取...")
    test_fps()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试web_visualizer.py的功能
"""
import requests
import time

def test_web_server():
    """测试Web服务器是否正常运行"""
    try:
        # 测试首页是否可以访问
        response = requests.get('http://localhost:5001/')
        if response.status_code == 200:
            print("✅ Web服务器正常运行")
            print(f"✅ 首页访问成功，状态码: {response.status_code}")
        else:
            print(f"❌ 首页访问失败，状态码: {response.status_code}")
            
        # 测试socket.io是否可以访问
        response = requests.get('http://localhost:5001/socket.io/')
        if response.status_code == 200:
            print("✅ Socket.IO服务正常")
        else:
            print(f"⚠️  Socket.IO服务可能需要通过WebSocket连接，状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == '__main__':
    print("🔍 测试web_visualizer.py功能...")
    test_web_server()
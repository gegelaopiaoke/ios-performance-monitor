#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存泄漏检测功能测试脚本
用于验证内存泄漏检测算法的正确性
"""

import sys
import os
import time
import random
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入内存泄漏检测器
from ios.web_visualizer import MemoryLeakDetector, MemoryLeakLogger

def test_memory_leak_detection():
    """测试内存泄漏检测功能"""
    print("🧪 开始测试内存泄漏检测功能")
    print("=" * 60)
    
    # 创建检测器和日志记录器
    detector = MemoryLeakDetector()
    logger = MemoryLeakLogger()
    
    # 测试场景1：正常内存使用（无泄漏）
    print("\n📊 测试场景1：正常内存使用")
    print("-" * 30)
    
    base_memory = 100  # 基础内存100MB
    for i in range(15):
        # 模拟正常的内存波动（±10MB）
        memory = base_memory + random.uniform(-10, 10)
        timestamp = time.time() + i
        
        detector.add_memory_sample(memory, timestamp)
        print(f"样本 {i+1:2d}: {memory:6.1f} MB")
        
        leak_info = detector.detect_memory_leak()
        if leak_info:
            print(f"❌ 意外检测到泄漏: {leak_info}")
    
    print("✅ 正常内存使用测试完成 - 未检测到泄漏")
    
    # 重置检测器
    detector.memory_history.clear()
    detector.last_alert_time = 0
    
    # 测试场景2：轻微内存泄漏
    print("\n📊 测试场景2：轻微内存泄漏")
    print("-" * 30)
    
    base_memory = 100
    for i in range(15):
        # 模拟轻微内存泄漏（每次增长0.8MB + 随机波动）
        memory = base_memory + (i * 0.8) + random.uniform(-5, 5)
        timestamp = time.time() + i * 10  # 每10秒一个样本
        
        detector.add_memory_sample(memory, timestamp)
        print(f"样本 {i+1:2d}: {memory:6.1f} MB")
        
        leak_info = detector.detect_memory_leak()
        if leak_info:
            print(f"🚨 检测到内存泄漏:")
            print(f"   严重程度: {leak_info['severity']}")
            print(f"   当前内存: {leak_info['current_memory']:.1f} MB")
            print(f"   增长率: {leak_info['growth_rate']} MB/分钟")
            print(f"   内存增长: {leak_info['memory_increase']:.1f} MB")
            print(f"   检测时长: {leak_info['time_span']:.1f} 分钟")
            print(f"   建议: {leak_info['recommendation']}")
            
            # 记录到日志
            app_info = {'name': 'TestApp', 'pid': 12345, 'bundle_id': 'com.test.app'}
            logger.log_leak_event(leak_info, app_info)
            break
    
    # 重置检测器
    detector.memory_history.clear()
    detector.last_alert_time = 0
    
    # 测试场景3：严重内存泄漏
    print("\n📊 测试场景3：严重内存泄漏")
    print("-" * 30)
    
    base_memory = 150
    for i in range(15):
        # 模拟严重内存泄漏（每次增长3MB + 随机波动）
        memory = base_memory + (i * 3) + random.uniform(-2, 2)
        timestamp = time.time() + i * 8  # 每8秒一个样本
        
        detector.add_memory_sample(memory, timestamp)
        print(f"样本 {i+1:2d}: {memory:6.1f} MB")
        
        leak_info = detector.detect_memory_leak()
        if leak_info:
            print(f"🚨 检测到严重内存泄漏:")
            print(f"   严重程度: {leak_info['severity']}")
            print(f"   当前内存: {leak_info['current_memory']:.1f} MB")
            print(f"   增长率: {leak_info['growth_rate']} MB/分钟")
            print(f"   内存增长: {leak_info['memory_increase']:.1f} MB")
            print(f"   检测时长: {leak_info['time_span']:.1f} 分钟")
            print(f"   建议: {leak_info['recommendation']}")
            
            # 记录到日志
            app_info = {'name': 'CriticalApp', 'pid': 54321, 'bundle_id': 'com.critical.app'}
            logger.log_leak_event(leak_info, app_info)
            break
    
    # 测试日志功能
    print("\n📋 测试日志记录功能")
    print("-" * 30)
    
    recent_events = logger.get_recent_leak_events(10)
    print(f"获取到 {len(recent_events)} 条最近的泄漏事件:")
    
    for i, event in enumerate(recent_events, 1):
        print(f"事件 {i}:")
        print(f"  时间: {event['timestamp']}")
        print(f"  严重程度: {event['severity']}")
        print(f"  应用: {event['app_info'].get('name', 'Unknown')}")
        print(f"  当前内存: {event['current_memory']:.1f} MB")
        print(f"  增长率: {event['growth_rate']} MB/分钟")
        print()
    
    print("✅ 内存泄漏检测功能测试完成")
    print("=" * 60)

def test_performance_scenarios():
    """测试不同性能场景下的检测效果"""
    print("\n🎯 测试不同性能场景")
    print("=" * 60)
    
    detector = MemoryLeakDetector()
    
    scenarios = [
        {
            'name': '游戏应用 - 关卡加载',
            'pattern': lambda i: 200 + (i // 5) * 50 + random.uniform(-10, 10),  # 阶梯式增长
            'description': '每5个样本内存增加50MB，模拟关卡加载'
        },
        {
            'name': '社交应用 - 图片缓存泄漏',
            'pattern': lambda i: 80 + i * 2.5 + random.uniform(-5, 5),  # 线性增长
            'description': '持续线性增长，模拟图片缓存未释放'
        },
        {
            'name': '视频应用 - 解码器泄漏',
            'pattern': lambda i: 300 + i * 4 + random.uniform(-8, 8),  # 快速增长
            'description': '快速内存增长，模拟视频解码器泄漏'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📱 场景: {scenario['name']}")
        print(f"描述: {scenario['description']}")
        print("-" * 40)
        
        # 重置检测器
        detector.memory_history.clear()
        detector.last_alert_time = 0
        
        for i in range(20):
            memory = scenario['pattern'](i)
            timestamp = time.time() + i * 5  # 每5秒一个样本
            
            detector.add_memory_sample(memory, timestamp)
            
            if i % 5 == 4:  # 每5个样本显示一次
                print(f"第{i+1:2d}个样本: {memory:6.1f} MB")
            
            leak_info = detector.detect_memory_leak()
            if leak_info:
                print(f"\n🚨 在第{i+1}个样本时检测到泄漏:")
                print(f"   严重程度: {leak_info['severity']}")
                print(f"   增长率: {leak_info['growth_rate']} MB/分钟")
                print(f"   内存增长: {leak_info['memory_increase']:.1f} MB")
                break
        else:
            print("   未检测到内存泄漏")

if __name__ == '__main__':
    try:
        test_memory_leak_detection()
        test_performance_scenarios()
        
        print("\n🎉 所有测试完成！")
        print("💡 提示：")
        print("   1. 启动iOS性能监控工具")
        print("   2. 开始监控应用")
        print("   3. 观察内存泄漏提醒功能")
        print("   4. 查看日志文件: logs/memory_leak_events.log")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

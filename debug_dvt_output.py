#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json

def debug_dvt_output():
    """调试DVT命令的原始输出"""
    try:
        print("🔄 执行DVT proclist命令...")
        result = subprocess.run([
            'pymobiledevice3', 'developer', 'dvt', 'proclist'
        ], capture_output=True, text=True, timeout=30)
        
        print(f"📊 返回码: {result.returncode}")
        print(f"📊 stderr长度: {len(result.stderr)}")
        print(f"📊 stdout长度: {len(result.stdout)}")
        
        if result.stderr:
            print(f"\n❌ 错误输出:")
            print(result.stderr)
        
        if result.stdout:
            print(f"\n📋 原始输出 (前1000字符):")
            print("=" * 50)
            print(result.stdout[:1000])
            print("=" * 50)
            
            # 分析输出格式
            lines = result.stdout.strip().split('\n')
            print(f"\n📊 输出分析:")
            print(f"  - 总行数: {len(lines)}")
            print(f"  - 前5行:")
            for i, line in enumerate(lines[:5]):
                print(f"    {i+1}: {repr(line)}")
            
            # 检查是否是JSON
            try:
                json.loads(result.stdout)
                print("  - 格式: JSON ✅")
            except:
                print("  - 格式: 非JSON")
                
                # 检查是否是表格格式
                has_header = any('PID' in line.upper() for line in lines[:5])
                print(f"  - 是否有表头: {has_header}")
                
                # 检查数字开头的行
                numeric_lines = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
                print(f"  - 数字开头的行: {len(numeric_lines)}")
                if numeric_lines:
                    print(f"    示例: {numeric_lines[0][:50]}...")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    debug_dvt_output()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import re
from typing import List, Dict, Any

def get_process_list_fixed() -> List[Dict[str, Any]]:
    """获取进程列表 - 修复版本"""
    try:
        print("🔄 执行DVT proclist命令...")
        result = subprocess.run([
            'pymobiledevice3', 'developer', 'dvt', 'proclist'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ DVT命令失败: {result.stderr}")
            return []
        
        processes = []
        lines = result.stdout.strip().split('\n')
        print(f"📊 原始输出共 {len(lines)} 行")
        
        # 尝试多种解析方法
        
        # 方法1: JSON解析
        try:
            if result.stdout.strip().startswith('[') or result.stdout.strip().startswith('{'):
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    processes = data
                elif isinstance(data, dict) and 'processes' in data:
                    processes = data['processes']
                print(f"✅ JSON解析成功，找到 {len(processes)} 个进程")
                return processes
        except json.JSONDecodeError:
            print("⚠️  不是JSON格式，尝试其他解析方法")
        
        # 方法2: 表格解析 (PID NAME等列)
        header_found = False
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 查找表头
            if 'PID' in line.upper() and ('NAME' in line.upper() or 'PROCESS' in line.upper()):
                print(f"📋 找到表头: {line}")
                header_found = True
                continue
            
            if header_found and line:
                # 尝试解析进程行
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    pid = int(parts[0])
                    name = ' '.join(parts[1:])
                    processes.append({
                        'pid': pid,
                        'name': name,
                        'bundleIdentifier': name if '.' in name else None
                    })
        
        if processes:
            print(f"✅ 表格解析成功，找到 {len(processes)} 个进程")
            return processes
        
        # 方法3: 正则表达式解析
        print("🔍 尝试正则表达式解析...")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 匹配 PID: 数字 Name: 名称 格式
            match = re.search(r'(?:PID|pid)\s*:?\s*(\d+).*?(?:Name|name|process)\s*:?\s*([^\s]+)', line, re.IGNORECASE)
            if match:
                pid = int(match.group(1))
                name = match.group(2)
                processes.append({
                    'pid': pid,
                    'name': name,
                    'bundleIdentifier': name if '.' in name else None
                })
                continue
            
            # 匹配简单的 数字 名称 格式
            match = re.match(r'^(\d+)\s+(.+)$', line)
            if match:
                pid = int(match.group(1))
                name = match.group(2).strip()
                processes.append({
                    'pid': pid,
                    'name': name,
                    'bundleIdentifier': name if '.' in name else None
                })
        
        if processes:
            print(f"✅ 正则解析成功，找到 {len(processes)} 个进程")
        else:
            print("❌ 所有解析方法都失败了")
            print("前10行原始输出:")
            for i, line in enumerate(lines[:10]):
                print(f"  {i+1}: {repr(line)}")
        
        return processes
        
    except Exception as e:
        print(f"❌ 获取进程列表失败: {e}")
        return []

def test_fixed_parser():
    """测试修复后的解析器"""
    processes = get_process_list_fixed()
    
    if processes:
        print(f"\n🎉 成功解析 {len(processes)} 个进程:")
        print("-" * 60)
        
        app_processes = []
        system_processes = []
        
        for proc in processes[:20]:  # 只显示前20个
            pid = proc.get('pid', 'N/A')
            name = proc.get('name', 'Unknown')
            bundle_id = proc.get('bundleIdentifier', '')
            
            if bundle_id and '.' in bundle_id:
                app_processes.append(proc)
                print(f"📱 {pid:6} | {name}")
            else:
                system_processes.append(proc)
                print(f"⚙️  {pid:6} | {name}")
        
        print(f"\n📊 统计: 应用进程 {len(app_processes)} 个，系统进程 {len(system_processes)} 个")
        
        # 查找目标应用
        target_bundle = "com.newleaf.app.ios.vic"
        target_proc = None
        for proc in processes:
            if proc.get('bundleIdentifier') == target_bundle or target_bundle in proc.get('name', ''):
                target_proc = proc
                break
        
        if target_proc:
            print(f"\n🎯 找到目标应用: {target_proc}")
        else:
            print(f"\n❌ 未找到目标应用: {target_bundle}")
            print("\n所有包含 'vic' 的进程:")
            for proc in processes:
                name = proc.get('name', '').lower()
                bundle = proc.get('bundleIdentifier', '').lower()
                if 'vic' in name or 'vic' in bundle:
                    print(f"  - {proc}")
    else:
        print("❌ 未能解析任何进程")

if __name__ == "__main__":
    test_fixed_parser()

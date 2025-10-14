#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import json
import re
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
import csv

class iOS18ThreadAnalyzer:
    """iOS 18线程性能分析工具 - 完整版"""
    
    def __init__(self):
        print("🚀 初始化iOS线程性能分析工具...")
        self.device_connected = self.check_device_connection()
        self.device_info = {}
        self.apps_cache = {}
        self.processes_cache = {}
        self.monitoring_active = False
        
        if self.device_connected:
            self.load_device_info()
    
    def check_device_connection(self):
        """检查设备连接状态"""
        try:
            result = subprocess.run([
                'pymobiledevice3', 'developer', 'core-device', 'get-device-info'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ 设备连接成功")
                return True
            else:
                print("❌ 设备连接失败")
                return False
                
        except Exception as e:
            print(f"❌ 设备连接检查异常: {e}")
            return False
    
    def load_device_info(self):
        """加载设备信息"""
        try:
            print("📱 加载设备信息...")
            result = subprocess.run([
                'pymobiledevice3', 'developer', 'core-device', 'get-device-info'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.device_info = json.loads(result.stdout)
                cpu_info = self.device_info.get('cpuCount', {})
                print(f"📱 设备名称: {self.device_info.get('name', 'Unknown')}")
                print(f"📱 系统版本: {self.device_info.get('osVersion', 'Unknown')}")
                print(f"📱 CPU核心: {cpu_info.get('logicalCores', 'Unknown')}")
                print(f"📱 设备型号: {self.device_info.get('deviceClass', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ 加载设备信息失败: {e}")
    
    def get_app_list(self, force_refresh=False):
        """获取应用列表"""
        if not force_refresh and self.apps_cache:
            return self.apps_cache
        
        try:
            print("📱 获取应用列表...")
            result = subprocess.run([
                'pymobiledevice3', 'developer', 'core-device', 'list-apps'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                apps_data = json.loads(result.stdout)
                self.apps_cache = {}
                
                for app in apps_data:
                    bundle_id = app.get('bundleIdentifier', '')
                    if bundle_id:
                        self.apps_cache[bundle_id] = {
                            'name': app.get('name', bundle_id),
                            'version': app.get('bundleVersion', ''),
                            'path': app.get('path', ''),
                            'isFirstParty': app.get('isFirstParty', False),
                            'isDeveloperApp': app.get('isDeveloperApp', False)
                        }
                
                print(f"✅ 加载 {len(self.apps_cache)} 个应用")
                return self.apps_cache
            else:
                print(f"❌ 获取应用列表失败: {result.stderr}")
                return {}
                
        except Exception as e:
            print(f"❌ 应用列表获取异常: {e}")
            return {}
    
    def get_process_list(self):
        """获取进程列表"""
        try:
            print("🔄 获取进程列表...")
            result = subprocess.run([
                'pymobiledevice3', 'developer', 'dvt', 'proclist'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # 解析进程列表
                processes = {}
                lines = result.stdout.strip().split('\n')
                
                current_process = {}
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_process.get('pid'):
                            pid = current_process['pid']
                            processes[pid] = current_process
                        current_process = {}
                        continue
                    
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'pid':
                            current_process['pid'] = int(value)
                        elif key == 'name':
                            current_process['name'] = value
                        elif key == 'bundleIdentifier':
                            current_process['bundleIdentifier'] = value
                        elif key == 'isApplication':
                            current_process['isApplication'] = value.lower() == 'true'
                
                # 处理最后一个进程
                if current_process.get('pid'):
                    pid = current_process['pid']
                    processes[pid] = current_process
                
                self.processes_cache = processes
                print(f"✅ 发现 {len(processes)} 个进程")
                return processes
            else:
                print(f"❌ 获取进程列表失败: {result.stderr}")
                return {}
                
        except Exception as e:
            print(f"❌ 进程列表获取异常: {e}")
            return {}
    
    def search_apps(self, keyword=""):
        """搜索应用"""
        apps = self.get_app_list()
        if not keyword:
            return apps
        
        keyword = keyword.lower()
        filtered_apps = {}
        
        for bundle_id, app_info in apps.items():
            if (keyword in bundle_id.lower() or 
                keyword in app_info['name'].lower()):
                filtered_apps[bundle_id] = app_info
        
        return filtered_apps
    
    def get_app_processes(self, bundle_id):
        """获取指定应用的进程"""
        processes = self.get_process_list()
        app_processes = {}
        
        for pid, proc_info in processes.items():
            if proc_info.get('bundleIdentifier') == bundle_id:
                app_processes[pid] = proc_info
        
        return app_processes
    
    def monitor_app_performance(self, bundle_id, duration=60, interval=5):
        """监控应用性能"""
        print(f"🎯 开始监控应用: {bundle_id}")
        print(f"⏱️  监控时长: {duration}秒, 采样间隔: {interval}秒")
        
        # 创建监控数据存储
        monitoring_data = {
            'bundle_id': bundle_id,
            'start_time': datetime.now().isoformat(),
            'device_info': self.device_info,
            'samples': []
        }
        
        self.monitoring_active = True
        start_time = time.time()
        sample_count = 0
        
        try:
            while self.monitoring_active and (time.time() - start_time) < duration:
                sample_count += 1
                print(f"\n📊 采样 #{sample_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # 获取进程信息
                app_processes = self.get_app_processes(bundle_id)
                
                if not app_processes:
                    print(f"⚠️  未找到应用 {bundle_id} 的运行进程")
                else:
                    sample_data = {
                        'timestamp': datetime.now().isoformat(),
                        'processes': app_processes,
                        'process_count': len(app_processes)
                    }
                    
                    monitoring_data['samples'].append(sample_data)
                    
                    # 显示当前状态
                    for pid, proc_info in app_processes.items():
                        print(f"   🔹 PID: {pid}, 名称: {proc_info.get('name', 'Unknown')}")
                
                # 等待下次采样
                if self.monitoring_active:
                    time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n⏹️  用户中断监控")
        finally:
            self.monitoring_active = False
            monitoring_data['end_time'] = datetime.now().isoformat()
            monitoring_data['total_samples'] = len(monitoring_data['samples'])
            
            # 保存监控数据
            self.save_monitoring_data(monitoring_data)
            return monitoring_data
    
    def save_monitoring_data(self, data):
        """保存监控数据"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            bundle_id = data['bundle_id'].replace('.', '_')
            
            # 保存JSON格式
            json_filename = f"/Users/apple/Downloads/ios性能/monitor_{bundle_id}_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 保存CSV格式
            csv_filename = f"/Users/apple/Downloads/ios性能/monitor_{bundle_id}_{timestamp}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['时间戳', '进程数量', 'PID列表', '进程名称列表'])
                
                for sample in data['samples']:
                    pids = list(sample['processes'].keys())
                    names = [proc['name'] for proc in sample['processes'].values()]
                    
                    writer.writerow([
                        sample['timestamp'],
                        sample['process_count'],
                        ','.join(map(str, pids)),
                        ','.join(names)
                    ])
            
            print(f"💾 监控数据已保存:")
            print(f"   📄 JSON: {json_filename}")
            print(f"   📊 CSV: {csv_filename}")
            
        except Exception as e:
            print(f"❌ 保存监控数据失败: {e}")
    
    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("\n" + "="*70)
            print("🎯 iOS线程性能分析工具 - 完整版")
            print("="*70)
            print("1. 设备信息")
            print("2. 应用列表")
            print("3. 进程列表") 
            print("4. 搜索应用")
            print("5. 查看应用进程")
            print("6. 监控应用性能")
            print("7. 刷新缓存")
            print("0. 退出")
            
            try:
                choice = input("\n请选择操作 (0-7): ").strip()
                
                if choice == '0':
                    print("👋 再见！")
                    break
                elif choice == '1':
                    self.show_device_info()
                elif choice == '2':
                    self.show_app_list()
                elif choice == '3':
                    self.show_process_list()
                elif choice == '4':
                    self.search_and_show_apps()
                elif choice == '5':
                    self.show_app_processes_interactive()
                elif choice == '6':
                    self.monitor_app_interactive()
                elif choice == '7':
                    self.refresh_cache()
                else:
                    print("❌ 无效选择")
                    
            except KeyboardInterrupt:
                print("\n👋 用户退出")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")
    
    def show_device_info(self):
        """显示设备信息"""
        if not self.device_info:
            self.load_device_info()
        
        print("\n📱 设备信息:")
        print("-" * 50)
        for key, value in self.device_info.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
    
    def show_app_list(self):
        """显示应用列表"""
        apps = self.get_app_list()
        
        print(f"\n📱 应用列表 (共{len(apps)}个):")
        print("-" * 80)
        
        count = 0
        for bundle_id, app_info in apps.items():
            count += 1
            name = app_info['name']
            version = app_info['version']
            is_first_party = "🍎" if app_info['isFirstParty'] else "📱"
            
            print(f"{count:3d}. {is_first_party} {name}")
            print(f"     Bundle ID: {bundle_id}")
            print(f"     版本: {version}")
            print()
            
            if count >= 20:
                more = input("显示更多? (y/n): ").strip().lower()
                if more != 'y':
                    break
    
    def show_process_list(self):
        """显示进程列表"""
        processes = self.get_process_list()
        
        print(f"\n🔄 进程列表 (共{len(processes)}个):")
        print("-" * 80)
        
        # 按应用分组
        app_processes = {}
        system_processes = {}
        
        for pid, proc_info in processes.items():
            if proc_info.get('isApplication', False):
                bundle_id = proc_info.get('bundleIdentifier', 'Unknown')
                if bundle_id not in app_processes:
                    app_processes[bundle_id] = []
                app_processes[bundle_id].append((pid, proc_info))
            else:
                system_processes[pid] = proc_info
        
        # 显示应用进程
        print("📱 应用进程:")
        for bundle_id, procs in app_processes.items():
            app_name = self.apps_cache.get(bundle_id, {}).get('name', bundle_id)
            print(f"  🔹 {app_name} ({bundle_id})")
            for pid, proc_info in procs:
                print(f"     PID: {pid}, 名称: {proc_info.get('name', 'Unknown')}")
        
        # 显示系统进程（前10个）
        print(f"\n⚙️  系统进程 (显示前10个，共{len(system_processes)}个):")
        count = 0
        for pid, proc_info in system_processes.items():
            count += 1
            print(f"  PID: {pid}, 名称: {proc_info.get('name', 'Unknown')}")
            if count >= 10:
                break
    
    def search_and_show_apps(self):
        """搜索并显示应用"""
        keyword = input("请输入搜索关键词: ").strip()
        apps = self.search_apps(keyword)
        
        if not apps:
            print("❌ 未找到匹配的应用")
            return
        
        print(f"\n🔍 搜索结果 (共{len(apps)}个):")
        print("-" * 80)
        
        for i, (bundle_id, app_info) in enumerate(apps.items(), 1):
            name = app_info['name']
            version = app_info['version']
            is_first_party = "🍎" if app_info['isFirstParty'] else "📱"
            
            print(f"{i:2d}. {is_first_party} {name}")
            print(f"    Bundle ID: {bundle_id}")
            print(f"    版本: {version}")
            print()
    
    def show_app_processes_interactive(self):
        """交互式显示应用进程"""
        bundle_id = input("请输入应用Bundle ID: ").strip()
        if not bundle_id:
            return
        
        app_processes = self.get_app_processes(bundle_id)
        
        if not app_processes:
            print(f"❌ 未找到应用 {bundle_id} 的运行进程")
            return
        
        app_name = self.apps_cache.get(bundle_id, {}).get('name', bundle_id)
        print(f"\n🔹 应用: {app_name}")
        print(f"Bundle ID: {bundle_id}")
        print(f"运行进程 (共{len(app_processes)}个):")
        print("-" * 50)
        
        for pid, proc_info in app_processes.items():
            print(f"PID: {pid}")
            print(f"名称: {proc_info.get('name', 'Unknown')}")
            print(f"是否应用: {proc_info.get('isApplication', False)}")
            print()
    
    def monitor_app_interactive(self):
        """交互式监控应用"""
        bundle_id = input("请输入要监控的应用Bundle ID: ").strip()
        if not bundle_id:
            return
        
        # 检查应用是否存在
        if bundle_id not in self.apps_cache:
            print(f"❌ 未找到应用: {bundle_id}")
            return
        
        try:
            duration = int(input("监控时长(秒，默认60): ").strip() or "60")
            interval = int(input("采样间隔(秒，默认5): ").strip() or "5")
        except ValueError:
            print("❌ 输入无效，使用默认值")
            duration = 60
            interval = 5
        
        app_name = self.apps_cache[bundle_id]['name']
        print(f"\n🎯 准备监控应用: {app_name}")
        print("按 Ctrl+C 可随时停止监控")
        
        input("按回车开始监控...")
        
        monitoring_data = self.monitor_app_performance(bundle_id, duration, interval)
        
        # 显示监控总结
        print(f"\n📊 监控总结:")
        print(f"应用: {app_name} ({bundle_id})")
        print(f"总采样次数: {monitoring_data['total_samples']}")
        print(f"监控时长: {duration}秒")
    
    def refresh_cache(self):
        """刷新缓存"""
        print("🔄 刷新缓存...")
        self.apps_cache = {}
        self.processes_cache = {}
        self.get_app_list(force_refresh=True)
        print("✅ 缓存已刷新")

def main():
    try:
        analyzer = iOS18ThreadAnalyzer()
        if analyzer.device_connected:
            analyzer.interactive_menu()
        else:
            print("❌ 设备未连接，无法启动分析工具")
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")

if __name__ == "__main__":
    main()

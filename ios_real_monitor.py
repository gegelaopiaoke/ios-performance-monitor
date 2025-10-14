#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS 真实设备线程监控工具 - 纯真实数据版本
只获取真实数据，不要任何模拟或演示
"""

import subprocess
import json
import time
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Optional


class iOSRealThreadMonitor:
    def __init__(self):
        self.device_id = None
        self.target_pid = None
        self.bundle_id = None

    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """获取工具的真实路径"""
        possible_paths = [
            tool_name,  # PATH中
            f'/opt/homebrew/bin/{tool_name}',  # M1 Mac
            f'/usr/local/bin/{tool_name}',  # Intel Mac
            f'/usr/bin/{tool_name}',  # 系统
            f'/Applications/Xcode.app/Contents/Developer/usr/bin/{tool_name}'  # Xcode
        ]

        for path in possible_paths:
            try:
                result = subprocess.run([path, '--help'],
                                        capture_output=True,
                                        timeout=2)
                if result.returncode == 0 or 'usage' in result.stderr.decode('utf-8', errors='ignore').lower():
                    return path
            except:
                continue
        return None

    def find_device(self) -> bool:
        """查找真实iOS设备"""
        idevice_id = self.get_tool_path('idevice_id')
        if not idevice_id:
            print("❌ 找不到 idevice_id 工具")
            return False

        try:
            result = subprocess.run([idevice_id, '-l'],
                                    capture_output=True,
                                    text=True,
                                    timeout=10)

            if result.returncode == 0 and result.stdout.strip():
                self.device_id = result.stdout.strip().split('\n')[0]
                print(f"📱 设备: {self.device_id}")
                return True
            else:
                print("❌ 没有找到连接的iOS设备")
                return False

        except Exception as e:
            print(f"❌ 设备查找失败: {e}")
            return False

    def find_app_bundle_id(self, app_name: str) -> bool:
        """查找真实应用Bundle ID"""
        installer = self.get_tool_path('ideviceinstaller')
        if not installer:
            print("❌ 找不到 ideviceinstaller 工具")
            return False

        try:
            result = subprocess.run([installer, '-u', self.device_id, '-l'],
                                    capture_output=True,
                                    text=True,
                                    timeout=30)

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if app_name.lower() in line.lower():
                        parts = line.split(' - ')
                        if len(parts) >= 2:
                            self.bundle_id = parts[0].strip()
                            print(f"📦 Bundle ID: {self.bundle_id}")
                            return True

            print(f"❌ 未找到应用: {app_name}")
            return False

        except Exception as e:
            print(f"❌ 应用查找失败: {e}")
            return False

    def get_real_pid(self) -> bool:
        """获取真实应用PID"""
        try:
            # 方法1: 通过idevicedebug启动并获取PID
            debug_tool = self.get_tool_path('idevicedebug')
            if debug_tool:
                print(f"🚀 启动应用: {self.bundle_id}")

                # 启动应用
                process = subprocess.Popen([
                    debug_tool, '-u', self.device_id, 'run', self.bundle_id
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                time.sleep(2)  # 等待应用启动

                # 方法2: 通过syslog获取PID
                syslog = self.get_tool_path('idevicesyslog')
                if syslog:
                    syslog_process = subprocess.Popen([
                        syslog, '-u', self.device_id
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                    start_time = time.time()
                    while time.time() - start_time < 15:
                        line = syslog_process.stdout.readline()
                        if line and self.bundle_id in line:
                            # 查找PID模式
                            pid_patterns = [
                                r'\[(\d+)\]',  # [PID]
                                r'pid=(\d+)',  # pid=PID
                                r'process (\d+)',  # process PID
                            ]

                            for pattern in pid_patterns:
                                match = re.search(pattern, line)
                                if match:
                                    self.target_pid = int(match.group(1))
                                    print(f"🎯 找到PID: {self.target_pid}")
                                    syslog_process.terminate()
                                    return True

                    syslog_process.terminate()

                process.terminate()

            print("❌ 无法自动获取PID")
            return False

        except Exception as e:
            print(f"❌ PID获取失败: {e}")
            return False

    def get_real_threads(self) -> List[Dict]:
        """获取真实线程数据"""
        sample_tool = self.get_tool_path('sample')
        if not sample_tool:
            print("❌ 找不到 sample 工具")
            return []

        try:
            print("🔍 采集线程数据...")
            result = subprocess.run([
                sample_tool, str(self.target_pid), '3', '-mayDie'
            ], capture_output=True, text=True, timeout=45)

            if result.returncode == 0:
                return self.parse_real_sample_output(result.stdout)
            else:
                print(f"❌ Sample失败: {result.stderr}")
                return []

        except subprocess.TimeoutExpired:
            print("❌ Sample超时")
            return []
        except Exception as e:
            print(f"❌ 线程采集失败: {e}")
            return []

    def parse_real_sample_output(self, output: str) -> List[Dict]:
        """解析真实的sample输出"""
        threads = []
        lines = output.split('\n')
        current_thread = None

        for line in lines:
            line = line.strip()

            # 线程开始标记
            if line.startswith('Thread '):
                if current_thread:
                    threads.append(current_thread)

                # 解析线程信息
                thread_match = re.match(r'Thread (\d+)(?:\s+(.+?))?:', line)
                if thread_match:
                    tid = thread_match.group(1)
                    name = thread_match.group(2) if thread_match.group(2) else f"Thread-{tid}"

                    current_thread = {
                        'tid': tid,
                        'name': name.strip(),
                        'state': 'unknown',
                        'cpu_usage': 0.0,
                        'stack_frames': []
                    }
                continue

            # CPU使用率
            if current_thread and 'CPU usage' in line:
                cpu_match = re.search(r'(\d+\.\d+)%', line)
                if cpu_match:
                    current_thread['cpu_usage'] = float(cpu_match.group(1))
                continue

            # 线程状态
            if current_thread and 'State:' in line:
                state_match = re.search(r'State:\s*(\w+)', line)
                if state_match:
                    current_thread['state'] = state_match.group(1).lower()
                continue

            # 调用栈
            if current_thread and (line.startswith('0x') or '+' in line):
                current_thread['stack_frames'].append(line)

        if current_thread:
            threads.append(current_thread)

        return threads

    def display_real_results(self, threads: List[Dict]):
        """显示真实结果"""
        if not threads:
            print("❌ 没有获取到任何线程数据")
            return

        print(f"\n📊 真实线程数据 - PID: {self.target_pid}")
        print(f"📱 设备: {self.device_id}")
        print(f"📦 应用: {self.bundle_id}")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)

        # 按CPU使用率排序
        threads_sorted = sorted(threads, key=lambda x: x['cpu_usage'], reverse=True)

        for thread in threads_sorted:
            tid = thread['tid']
            name = thread['name']
            state = thread['state']
            cpu = thread['cpu_usage']

            state_icon = {'running': '🟢', 'waiting': '🟡', 'blocked': '🔴'}.get(state, '⚪')

            print(f"{state_icon} TID: {tid:<4} | {name:<50} | {state:<8} | CPU: {cpu:>6.1f}%")

            # 显示关键调用栈
            frames = thread['stack_frames']
            if frames:
                print("   📚 关键调用栈:")
                for i, frame in enumerate(frames[:4]):
                    print(f"      {frame}")
                if len(frames) > 4:
                    print(f"      ... (+{len(frames) - 4} 更多)")
            print()

        # 统计
        total_cpu = sum(t['cpu_usage'] for t in threads)
        print("=" * 100)
        print(f"📈 统计: {len(threads)} 个线程, 总CPU: {total_cpu:.1f}%")

    def monitor_real(self, app_name: str, duration: int, interval: int):
        """真实监控主流程"""
        print("🚀 iOS真实线程监控")
        print("=" * 30)

        # 1. 查找设备
        if not self.find_device():
            print("💡 请确保iOS设备已连接并信任此电脑")
            return

        # 2. 查找应用
        if not self.find_app_bundle_id(app_name):
            print("💡 请确保应用已安装在设备上")
            return

        # 3. 获取PID
        if not self.get_real_pid():
            print("💡 请手动启动应用后重试")
            return

        # 4. 开始监控
        start_time = time.time()
        sample_count = 0

        try:
            while time.time() - start_time < duration:
                sample_count += 1
                print(f"\n🔄 第 {sample_count} 次采样")

                threads = self.get_real_threads()
                self.display_real_results(threads)

                if time.time() - start_time < duration:
                    print(f"⏳ 等待 {interval} 秒...")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⏹️  监控停止")


def main():
    if len(sys.argv) < 2:
        print("📱 iOS真实线程监控工具")
        print("用法: python3 ios_real_monitor.py <应用名> [时长] [间隔]")
        print("示例: python3 ios_real_monitor.py ReelShort 30 5")
        return

    app_name = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    monitor = iOSRealThreadMonitor()
    monitor.monitor_real(app_name, duration, interval)


if __name__ == "__main__":
    main()

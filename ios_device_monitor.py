#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import time
import sys
import os
from datetime import datetime
import threading
import signal
import re


class iOSDeviceMonitor:
    def __init__(self, bundle_id, duration=60, interval=5):
        self.bundle_id = bundle_id
        self.duration = duration
        self.interval = interval
        self.device_id = None
        self.data_points = []
        self.running = True

    def signal_handler(self, signum, frame):
        """处理中断信号"""
        print("\n🛑 收到中断信号，正在停止监控...")
        self.running = False

    def check_tools(self):
        """检查必需的工具"""
        required_tools = [
            'idevice_id',
            'ideviceinfo',
            'idevicesyslog'
        ]

        missing_tools = []

        for tool in required_tools:
            try:
                result = subprocess.run(['which', tool],
                                        capture_output=True, text=True)
                if result.returncode != 0:
                    missing_tools.append(tool)
            except:
                missing_tools.append(tool)

        if missing_tools:
            print(f"❌ 缺少工具: {', '.join(missing_tools)}")
            print("💡 请安装 libimobiledevice:")
            print("   brew install libimobiledevice")
            return False

        print("✅ 所有工具检查通过")
        return True

    def check_device(self):
        """检查设备连接"""
        try:
            result = subprocess.run(['idevice_id', '-l'],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                device_id = result.stdout.strip().split('\n')[0]
                self.device_id = device_id
                print(f"📱 找到设备: {device_id}")
                return True
            else:
                print("❌ 未找到连接的设备")
                return False
        except subprocess.TimeoutExpired:
            print("❌ 设备检查超时")
            return False
        except Exception as e:
            print(f"❌ 设备检查失败: {e}")
            return False

    def get_device_info(self):
        """获取设备基本信息"""
        try:
            result = subprocess.run(['ideviceinfo', '-u', self.device_id],
                                    capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                info = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                return info
            return {}
        except Exception as e:
            print(f"⚠️ 获取设备信息失败: {e}")
            return {}

    def get_system_stats(self):
        """通过系统日志获取性能信息"""
        try:
            # 使用 idevicesyslog 获取系统日志
            cmd = ['idevicesyslog', '-u', self.device_id]

            # 启动日志进程
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)

            # 收集3秒的日志数据
            time.sleep(3)
            process.terminate()

            try:
                stdout, stderr = process.communicate(timeout=2)

                if stdout:
                    lines = stdout.split('\n')

                    # 分析日志中的性能相关信息
                    cpu_mentions = len([l for l in lines if 'cpu' in l.lower()])
                    memory_mentions = len([l for l in lines if 'memory' in l.lower() or 'mem' in l.lower()])
                    app_mentions = len([l for l in lines if self.bundle_id in l])

                    return {
                        'success': True,
                        'total_lines': len(lines),
                        'cpu_mentions': cpu_mentions,
                        'memory_mentions': memory_mentions,
                        'app_mentions': app_mentions,
                        'has_data': len(lines) > 10
                    }

            except subprocess.TimeoutExpired:
                process.kill()

        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': False, 'error': 'No data collected'}

    def get_top_like_info(self):
        """尝试获取类似top的信息"""
        try:
            # 尝试使用 instruments 命令行工具（如果可用）
            instruments_cmd = ['xcrun', 'instruments', '-l']

            result = subprocess.run(instruments_cmd, capture_output=True,
                                    text=True, timeout=10)

            if result.returncode == 0:
                return {
                    'success': True,
                    'method': 'instruments',
                    'available_templates': len(result.stdout.split('\n'))
                }
        except:
            pass

        # 尝试其他方法
        try:
            # 检查是否有 ios-deploy
            result = subprocess.run(['which', 'ios-deploy'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                return {
                    'success': True,
                    'method': 'ios-deploy',
                    'tool_available': True
                }
        except:
            pass

        return {'success': False, 'error': 'No suitable tools found'}

    def collect_data_point(self, iteration):
        """收集一个数据点"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 方法1: 系统日志分析
        print(f"   🔄 方法1: 分析系统日志...")
        syslog_data = self.get_system_stats()

        # 方法2: 检查可用工具
        print(f"   🔄 方法2: 检查性能工具...")
        tools_data = self.get_top_like_info()

        # 方法3: 设备信息（每5次采样获取一次）
        device_info = {}
        if iteration % 5 == 1:
            print(f"   🔄 方法3: 获取设备信息...")
            device_info = self.get_device_info()

        data_point = {
            'iteration': iteration,
            'timestamp': timestamp,
            'syslog': syslog_data,
            'tools': tools_data,
            'device_info': device_info,
            'bundle_id': self.bundle_id
        }

        self.data_points.append(data_point)
        return data_point

    def display_data_point(self, data):
        """显示数据点信息"""
        syslog = data['syslog']
        tools = data['tools']

        if syslog.get('success'):
            print(f"   ✅ 系统日志采集成功")
            print(f"      📝 日志行数: {syslog['total_lines']}")
            print(f"      🔄 CPU相关: {syslog['cpu_mentions']} 条")
            print(f"      💾 内存相关: {syslog['memory_mentions']} 条")
            print(f"      📱 应用相关: {syslog['app_mentions']} 条")
        else:
            print(f"   ❌ 系统日志采集失败: {syslog.get('error', 'Unknown')}")

        if tools.get('success'):
            print(f"   ✅ 性能工具检查: {tools.get('method', 'Unknown')}")
        else:
            print(f"   ⚠️ 性能工具: {tools.get('error', 'Not available')}")

        if data['device_info']:
            device_name = data['device_info'].get('DeviceName', 'Unknown')
            ios_version = data['device_info'].get('ProductVersion', 'Unknown')
            print(f"   📱 设备: {device_name} (iOS {ios_version})")

    def run_monitoring(self):
        """运行监控"""
        print(f"🎯 开始监控")
        print(f"📱 设备: {self.device_id}")
        print(f"📦 Bundle ID: {self.bundle_id}")
        print(f"⏱️ 监控时长: {self.duration}秒，间隔: {self.interval}秒")
        print(f"💡 请确保目标应用正在前台运行")
        print("=" * 60)

        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)

        start_time = time.time()
        iteration = 0

        while self.running and (time.time() - start_time) < self.duration:
            iteration += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            elapsed = int(time.time() - start_time)
            remaining = self.duration - elapsed

            print(f"\n📊 第 {iteration} 次采样 - {current_time} (剩余 {remaining}秒)")

            data = self.collect_data_point(iteration)
            self.display_data_point(data)

            # 等待下一次采样
            if self.running and (time.time() - start_time) < self.duration:
                print(f"   ⏳ 等待 {self.interval} 秒...")
                time.sleep(self.interval)

        if not self.running:
            print("\n🛑 监控被用户中断")
        else:
            print("\n⏰ 监控时间结束")

        self.generate_report()

    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 60)
        print("📈 监控报告")
        print("=" * 60)

        print(f"📦 Bundle ID: {self.bundle_id}")
        print(f"📱 设备: {self.device_id}")
        print(f"⏱️ 监控时长: {self.duration}秒")
        print(f"🔄 采样间隔: {self.interval}秒")
        print(f"📊 总采样次数: {len(self.data_points)}")

        if self.data_points:
            # 统计系统日志数据
            successful_syslog = [d for d in self.data_points if d['syslog'].get('success')]

            if successful_syslog:
                total_lines = sum(d['syslog']['total_lines'] for d in successful_syslog)
                total_cpu = sum(d['syslog']['cpu_mentions'] for d in successful_syslog)
                total_memory = sum(d['syslog']['memory_mentions'] for d in successful_syslog)
                total_app = sum(d['syslog']['app_mentions'] for d in successful_syslog)

                print(f"\n📊 系统日志统计:")
                print(f"  ✅ 成功采样: {len(successful_syslog)}")
                print(f"  📝 总日志行数: {total_lines}")
                print(f"  🔄 CPU相关日志: {total_cpu}")
                print(f"  💾 内存相关日志: {total_memory}")
                print(f"  📱 应用相关日志: {total_app}")

                if total_app > 0:
                    print(f"  🎯 应用活跃度: 高 ({total_app} 条相关日志)")
                elif total_lines > 100:
                    print(f"  🎯 系统活跃度: 正常")
                else:
                    print(f"  🎯 系统活跃度: 低")

            # 设备信息
            device_info_points = [d for d in self.data_points if d['device_info']]
            if device_info_points:
                info = device_info_points[0]['device_info']
                print(f"\n📱 设备信息:")
                print(f"  设备名称: {info.get('DeviceName', 'Unknown')}")
                print(f"  iOS版本: {info.get('ProductVersion', 'Unknown')}")
                print(f"  设备型号: {info.get('ProductType', 'Unknown')}")

        print("\n💡 监控建议:")
        print("  1. 如果应用相关日志较少，请确保应用在前台运行")
        print("  2. 可以在应用中进行一些操作来增加活动")
        print("  3. 考虑使用 Xcode Instruments 进行更详细的性能分析")
        print("  4. 检查应用是否有崩溃或异常日志")


def main():
    print("🚀 iOS 设备监控工具")
    print("=" * 40)

    if len(sys.argv) < 2:
        print("❌ 用法错误")
        print("用法: python3 script.py <bundle_id> [duration] [interval]")
        print("示例: python3 script.py com.newleaf.app.ios.vic 30 5")
        sys.exit(1)

    bundle_id = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    monitor = iOSDeviceMonitor(bundle_id, duration, interval)

    # 检查环境
    if not monitor.check_tools():
        sys.exit(1)

    if not monitor.check_device():
        sys.exit(1)

    # 开始监控
    try:
        monitor.run_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 用户中断监控")
    except Exception as e:
        print(f"\n❌ 监控过程中出错: {e}")


if __name__ == "__main__":
    main()

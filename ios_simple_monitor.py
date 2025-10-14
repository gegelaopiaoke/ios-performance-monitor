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


class iOSSimpleMonitor:
    def __init__(self, bundle_id, duration=60, interval=5):
        self.bundle_id = bundle_id
        self.duration = duration
        self.interval = interval
        self.device_id = "00008140-00162DD030A2201C"
        self.data_points = []
        self.running = True

    def signal_handler(self, signum, frame):
        """处理中断信号"""
        print("\n🛑 收到中断信号，正在停止监控...")
        self.running = False

    def check_tools(self):
        """检查必需的工具"""
        tools = {
            'sample': '/usr/bin/sample',
            'idevice_id': None
        }

        # 检查 sample
        if not os.path.exists('/usr/bin/sample'):
            print("❌ sample 工具未找到")
            return False

        # 检查 idevice_id
        try:
            result = subprocess.run(['which', 'idevice_id'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                tools['idevice_id'] = result.stdout.strip()
            else:
                print("❌ idevice_id 工具未找到")
                return False
        except:
            print("❌ 无法检查 idevice_id")
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

    def get_process_info(self):
        """使用 sample 获取进程信息"""
        try:
            # 尝试使用 sample 命令监控系统
            cmd = ['sample', 'SpringBoard', '1', '-mayDie']

            print(f"🔍 执行命令: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return {
                    'success': True,
                    'output_lines': len(result.stdout.split('\n')),
                    'has_data': len(result.stdout) > 100
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def collect_sample_data(self, iteration):
        """收集采样数据"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 尝试多种采样方式
        methods = [
            ['sample', 'SpringBoard', '1', '-mayDie'],
            ['sample', 'kernel_task', '1', '-mayDie'],
            ['sample', '1', '1']  # 采样进程ID 1
        ]

        for i, cmd in enumerate(methods):
            try:
                print(f"   🔄 尝试方法 {i + 1}: {' '.join(cmd)}")

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)

                if result.returncode == 0 and len(result.stdout) > 50:
                    lines = result.stdout.split('\n')
                    data_point = {
                        'iteration': iteration,
                        'timestamp': timestamp,
                        'method': i + 1,
                        'success': True,
                        'output_lines': len(lines),
                        'sample_size': len(result.stdout),
                        'has_thread_info': 'thread' in result.stdout.lower(),
                        'has_cpu_info': 'cpu' in result.stdout.lower() or '%' in result.stdout
                    }

                    # 尝试提取一些基本信息
                    if 'CPU usage' in result.stdout:
                        data_point['cpu_mentioned'] = True

                    self.data_points.append(data_point)
                    return data_point

            except subprocess.TimeoutExpired:
                print(f"   ⚠️ 方法 {i + 1} 超时")
                continue
            except Exception as e:
                print(f"   ⚠️ 方法 {i + 1} 出错: {e}")
                continue

        # 如果所有方法都失败，记录失败
        failed_point = {
            'iteration': iteration,
            'timestamp': timestamp,
            'success': False,
            'error': 'All methods failed'
        }
        self.data_points.append(failed_point)
        return failed_point

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

            data = self.collect_sample_data(iteration)

            if data['success']:
                print(f"   ✅ 采样成功")
                print(f"   📝 数据行数: {data['output_lines']}")
                print(f"   📏 数据大小: {data['sample_size']} 字符")
                print(f"   🧵 包含线程信息: {'是' if data.get('has_thread_info') else '否'}")
                print(f"   🔄 包含CPU信息: {'是' if data.get('has_cpu_info') else '否'}")
            else:
                print(f"   ❌ 采样失败: {data.get('error', 'Unknown error')}")

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
            successful = [d for d in self.data_points if d.get('success', False)]
            failed = [d for d in self.data_points if not d.get('success', False)]

            print(f"✅ 成功采样: {len(successful)}")
            print(f"❌ 失败采样: {len(failed)}")

            if successful:
                print("\n📊 成功采样详情:")
                for data in successful:
                    print(f"  {data['iteration']}. {data['timestamp']} - "
                          f"方法{data['method']} - "
                          f"{data['output_lines']}行/{data['sample_size']}字符")

                # 统计信息
                total_lines = sum(d['output_lines'] for d in successful)
                avg_lines = total_lines / len(successful) if successful else 0
                print(f"\n📈 统计信息:")
                print(f"  平均数据行数: {avg_lines:.1f}")
                print(f"  总数据行数: {total_lines}")

            if failed:
                print("\n❌ 失败采样:")
                for data in failed:
                    print(f"  {data['iteration']}. {data['timestamp']} - {data.get('error', 'Unknown')}")

        print("\n💡 使用建议:")
        print("  1. 确保目标应用在前台运行")
        print("  2. 保持设备解锁状态")
        print("  3. 在监控期间正常使用应用")
        print("  4. 如果采样失败较多，可以尝试重启应用")


def main():
    print("🚀 iOS 简化监控工具")
    print("=" * 40)

    if len(sys.argv) < 2:
        print("❌ 用法错误")
        print("用法: python3 script.py <bundle_id> [duration] [interval]")
        print("示例: python3 script.py com.newleaf.app.ios.vic 30 5")
        sys.exit(1)

    bundle_id = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    monitor = iOSSimpleMonitor(bundle_id, duration, interval)

    # 检查环境
    if not monitor.check_tools():
        print("❌ 工具检查失败")
        sys.exit(1)

    if not monitor.check_device():
        print("❌ 设备检查失败")
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
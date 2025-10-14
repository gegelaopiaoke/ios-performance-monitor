# Android性能监控命令行版本
# 基于iOS main.py的逻辑，完全保持原始逻辑不变

import json
import os
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime

class AndroidDeviceManager(object):
    def __init__(self):
        self.device_id = None
    
    def check_adb(self):
        """检查ADB是否可用"""
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_connected_devices(self):
        """获取连接的设备"""
        try:
            subprocess.run(['adb', 'start-server'], capture_output=True, timeout=5)
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]
            
            for line in lines:
                if line.strip() and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'device':
                        devices.append(parts[0])
            
            return devices
        except:
            return []

class AndroidPerformanceAnalyzer(object):
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.is_monitoring = False
    
    def get_app_pid(self, package_name):
        """获取应用PID"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'pidof', package_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
            return None
        except:
            return None
    
    def get_cpu_usage(self, pid):
        """获取CPU使用率"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'top', '-p', str(pid), '-n', '1'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if str(pid) in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            cpu_str = parts[8]
                            if '%' in cpu_str:
                                return float(cpu_str.replace('%', ''))
            return 0.0
        except:
            return 0.0
    
    def get_memory_usage(self, package_name):
        """获取内存使用"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'dumpsys', 'meminfo', package_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'TOTAL' in line and 'kB' in line:
                        parts = line.split()
                        for part in parts:
                            if part.isdigit():
                                return int(part) / 1024  # 转换为MB
            return 0.0
        except:
            return 0.0
    
    def get_thread_count(self, pid):
        """获取线程数"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'ls', '/proc/{}/task'.format(pid)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                threads = result.stdout.strip().split('\n')
                return len([t for t in threads if t.strip().isdigit()])
            return 0
        except:
            return 0
    
    def get_disk_io(self, pid):
        """获取磁盘I/O"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'cat', '/proc/{}/io'.format(pid)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                disk_reads = 0
                disk_writes = 0
                
                for line in lines:
                    if line.startswith('read_bytes:'):
                        disk_reads = int(line.split(':')[1].strip()) / (1024 * 1024)
                    elif line.startswith('write_bytes:'):
                        disk_writes = int(line.split(':')[1].strip()) / (1024 * 1024)
                
                return disk_reads, disk_writes
            
            return 0.0, 0.0
        except:
            return 0.0, 0.0
    
    def get_fps(self, package_name):
        """获取FPS"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'dumpsys', 'gfxinfo', package_name, 'framestats'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                frame_times = []
                
                for line in lines:
                    if line.startswith('0,'):
                        parts = line.split(',')
                        if len(parts) >= 3:
                            try:
                                frame_time = float(parts[2]) - float(parts[1])
                                if frame_time > 0:
                                    frame_times.append(frame_time)
                            except:
                                continue
                
                if frame_times:
                    avg_frame_time = sum(frame_times) / len(frame_times)
                    fps = 1000000000 / avg_frame_time if avg_frame_time > 0 else 0
                    return min(60, max(0, fps))
            
            return 0
        except:
            return 0
    
    def monitor_app_performance(self, package_name):
        """监控应用性能 - 与iOS版本逻辑完全一致"""
        if not package_name:
            print("❌ 请提供应用包名")
            return
        
        print(f"📱 开始监控Android应用 {package_name}")
        
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                pid = self.get_app_pid(package_name)
                
                if pid is None:
                    print(f"⚠️ 应用 {package_name} 未运行")
                    time.sleep(1)
                    continue
                
                # 获取性能数据
                cpu = self.get_cpu_usage(pid)
                memory = self.get_memory_usage(package_name)
                threads = self.get_thread_count(pid)
                disk_reads, disk_writes = self.get_disk_io(pid)
                fps = self.get_fps(package_name)
                
                # 输出格式与iOS版本完全一致
                data = {
                    "Pid": pid,
                    "Name": package_name,
                    "CPU": f"{cpu:.2f} %",
                    "Memory": f"{memory:.2f} MB",
                    "DiskReads": f"{disk_reads:.2f} MB",
                    "DiskWrites": f"{disk_writes:.2f} MB",
                    "Threads": threads,
                    "FPS": fps,
                    "Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(json.dumps(data))
                
                time.sleep(1)  # 1秒间隔，与iOS版本保持一致
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 监控时出错: {e}")
                time.sleep(1)

def check_admin():
    """检查管理员权限"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

if __name__ == '__main__':
    device_id = ""  # 目标设备
    package_name = ""  # 目标应用包名
    
    if len(sys.argv) >= 3:
        device_id = sys.argv[1]
        package_name = sys.argv[2]
    elif len(sys.argv) >= 2:
        package_name = sys.argv[1]
    
    if not package_name:
        print("用法: python android_main.py [device_id] <package_name>")
        print("示例: python android_main.py com.example.app")
        print("示例: python android_main.py emulator-5554 com.example.app")
        sys.exit(1)
    
    # 检查ADB
    device_manager = AndroidDeviceManager()
    if not device_manager.check_adb():
        print("❌ ADB未安装或不可用，请安装Android SDK Platform Tools")
        sys.exit(1)
    
    # 获取设备列表
    devices = device_manager.get_connected_devices()
    if not devices:
        print("❌ 未找到连接的Android设备")
        sys.exit(1)
    
    # 如果没有指定设备，使用第一个设备
    if not device_id and devices:
        device_id = devices[0]
        print(f"📱 自动选择设备: {device_id}")
    
    # 开始监控
    performance_analyzer = AndroidPerformanceAnalyzer(device_id)
    performance_analyzer.monitor_app_performance(package_name)
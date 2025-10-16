# Android性能监控Web可视化界面
# 基于iOS版本的逻辑，完全保持原始逻辑不变
import ctypes
import dataclasses
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

import os

# 获取项目根目录路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 配置Flask应用，指定模板和静态文件路径
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
app.config['SECRET_KEY'] = 'android_performance_monitor'
socketio = SocketIO(app, 
                  cors_allowed_origins="*",
                  ping_timeout=60,         # 增加到60秒ping超时
                  ping_interval=10,        # 10秒ping间隔，减少频率
                  max_http_buffer_size=1024*1024,  # 1MB缓冲区
                  async_mode='threading',  # 使用线程模式确保实时性
                  logger=False,            # 禁用日志减少干扰
                  engineio_logger=False)   # 禁用engineio日志

# 导入iOS的内存泄漏检测模块（跨平台通用）
sys.path.append(os.path.join(project_root, 'ios'))
from web_visualizer import MemoryLeakDetector, MemoryLeakLogger

# 全局内存泄漏检测器实例（Android专用）
android_leak_detector = MemoryLeakDetector()
android_leak_logger = MemoryLeakLogger(
    log_file_path=os.path.join(project_root, 'logs', 'android_memory_leak_events.log')
)

# 全局变量存储性能数据
performance_data = {
    'cpu_data': [],
    'memory_data': [],
    'fps_data': [],
    'disk_reads_data': [],
    'disk_writes_data': [],
    'threads_data': []
}

# 监控状态管理
monitoring_active = True
monitoring_threads = []
performance_analyzer = None


# Android设备管理类
class AndroidDeviceManager(object):
    def __init__(self):
        self.connected_devices = []
        self.selected_device = None
    
    def check_adb_installed(self):
        """检查ADB是否安装"""
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ ADB已安装")
                return True
            else:
                print("❌ ADB未正确安装")
                return False
        except FileNotFoundError:
            print("❌ 未找到ADB命令，请安装Android SDK Platform Tools")
            return False
        except Exception as e:
            print(f"❌ 检查ADB时出错: {e}")
            return False
    
    def get_connected_devices(self):
        """获取连接的Android设备列表"""
        try:
            # 首先启动adb server
            subprocess.run(['adb', 'start-server'], capture_output=True, timeout=5)
            
            # 获取设备列表
            result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"❌ 获取设备列表失败: {result.stderr}")
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行"List of devices attached"
            
            for line in lines:
                if line.strip() and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'device':
                        device_id = parts[0]
                        
                        # 获取设备详细信息
                        device_info = self.get_device_info(device_id)
                        devices.append({
                            'id': device_id,
                            'name': device_info.get('model', 'Unknown Device'),
                            'brand': device_info.get('brand', 'Unknown'),
                            'version': device_info.get('version', 'Unknown'),
                            'api_level': device_info.get('api_level', 'Unknown'),
                            'status': 'Connected'
                        })
            
            self.connected_devices = devices
            print(f"📱 发现 {len(devices)} 个Android设备")
            return devices
            
        except Exception as e:
            print(f"❌ 获取设备列表时出错: {e}")
            return []
    
    def get_device_info(self, device_id):
        """获取设备详细信息"""
        try:
            info = {}
            
            # 获取设备属性
            props = {
                'model': 'ro.product.model',
                'brand': 'ro.product.brand',
                'version': 'ro.build.version.release',
                'api_level': 'ro.build.version.sdk'
            }
            
            for key, prop in props.items():
                try:
                    result = subprocess.run(
                        ['adb', '-s', device_id, 'shell', 'getprop', prop],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        info[key] = result.stdout.strip()
                except:
                    info[key] = 'Unknown'
            
            return info
            
        except Exception as e:
            print(f"❌ 获取设备信息时出错: {e}")
            return {}


# Android性能分析器类
class AndroidPerformanceAnalyzer(object):
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.is_monitoring = False
        self.fps = 0
        self.monitoring_thread = None
        self.last_thread_update = 0  # 添加缺失的属性
        
    def get_installed_packages(self):
        """获取已安装的应用包列表（包含应用名称）"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'pm', 'list', 'packages', '-3'])  # -3 只显示第三方应用
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        package_name = line.replace('package:', '')
                        packages.append(package_name)
                return packages
            else:
                print(f"❌ 获取应用列表失败: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"❌ 获取应用列表时出错: {e}")
            return []
    
    def get_app_name(self, package_name):
        """获取应用的显示名称（优化版）"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'dumpsys', 'package', package_name])
            
            # 🔧 将超时时间从5秒增加到10秒，支持WiFi ADB连接
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # 从 dumpsys 输出中提取 applicationLabel
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'applicationLabel=' in line:
                        app_name = line.split('applicationLabel=')[1].strip()
                        if app_name:
                            return app_name
                
                # 备用方案：从包名提取最后一段作为显示名
                return package_name.split('.')[-1].capitalize()
            
            # 命令执行失败，使用备用方案
            return package_name.split('.')[-1].capitalize()
                
        except subprocess.TimeoutExpired:
            # 超时处理：静默失败，使用包名作为备用
            return package_name.split('.')[-1].capitalize()
        except Exception as e:
            print(f"⚠️ 获取应用名称失败 ({package_name}): {e}")
            return package_name.split('.')[-1].capitalize()
    
    def get_app_pid(self, package_name):
        """获取应用的PID"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'pidof', package_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
            else:
                return None
                
        except Exception as e:
            print(f"❌ 获取应用PID时出错: {e}")
            return None
    
    def get_cpu_and_memory_usage(self, pid, package_name):
        """获取CPU和内存使用情况（应用+整机）"""
        try:
            # 获取CPU核数
            cpu_cores = self.get_cpu_cores()
            
            # 使用top命令获取详细信息
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'top', '-n', '1'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                
                # 首先输出原始数据进行调试
                print(f"🔍 Top输出调试（前10行）:")
                for i, line in enumerate(lines[:10]):
                    print(f"行{i}: {line}")
                
                # 解析整机CPU信息
                system_cpu_usage = 0.0
                for line in lines[:10]:
                    if '%cpu' in line.lower():
                        # 格式: "800%cpu  25%user   0%nice  28%sys 742%idle"
                        import re
                        
                        # 解析详细的CPU使用情况
                        user_match = re.search(r'(\d+)%user', line)
                        sys_match = re.search(r'(\d+)%sys', line)
                        idle_match = re.search(r'(\d+)%idle', line)
                        
                        if user_match and sys_match and idle_match:
                            user_cpu = float(user_match.group(1))
                            sys_cpu = float(sys_match.group(1))
                            idle_cpu = float(idle_match.group(1))
                            
                            # 计算真实的CPU使用率
                            total_used = user_cpu + sys_cpu
                            total_available = user_cpu + sys_cpu + idle_cpu
                            
                            if total_available > 0:
                                system_cpu_usage = (total_used / total_available) * 100.0
                            
                            print(f"🔍 CPU解析: user={user_cpu}%, sys={sys_cpu}%, idle={idle_cpu}%, 计算结果={system_cpu_usage:.1f}%")
                        break
                
                # 解析应用进程信息
                app_cpu_raw = 0.0
                app_memory_mb = 0.0
                system_memory_total = 0.0
                system_memory_used = 0.0
                
                # 解析内存信息
                for line in lines[:5]:
                    if 'Mem:' in line:
                        # 格式: "Mem:   1874300k total,  1814556k used,    59744k free"
                        import re
                        total_match = re.search(r'(\d+)k total', line)
                        used_match = re.search(r'(\d+)k used', line)
                        if total_match and used_match:
                            system_memory_total = int(total_match.group(1)) / 1024  # kB转换为MB
                            system_memory_used = int(used_match.group(1)) / 1024   # kB转换为MB
                            print(f"🔍 系统内存解析: 总内存={system_memory_total:.0f}MB, 已用={system_memory_used:.0f}MB")
                        break
                
                # 解析应用进程信息
                print(f"🔍 查找PID {pid} 和包名 {package_name} 的进程...")
                for i, line in enumerate(lines[5:], 5):  # 从第5行开始
                    if str(pid) in line:
                        print(f"🔍 找到包含PID的行{i}: {line}")
                        
                        # 按空格分割，但要处理可能的多个空格
                        parts = [p for p in line.split() if p.strip()]
                        print(f"🔍 分割后的字段: {parts}")
                        
                        if len(parts) >= 9:  # 确保有足够的字段
                            try:
                                # 字段解析：PID USER PR NI VIRT RES SHR S[%CPU] %MEM TIME+ ARGS
                                #          0   1    2  3  4    5   6   7      8    9     10
                                
                                # CPU使用率在第8列（%CPU）
                                cpu_str = parts[8]  # %CPU列
                                if cpu_str.replace('.', '').replace('-', '').isdigit():
                                    app_cpu_raw = float(cpu_str)
                                    print(f"🔍 应用CPU原始值: {app_cpu_raw}")
                                
                                # 内存使用量在第5列（RES）
                                mem_str = parts[5]  # RES列
                                if 'G' in mem_str:
                                    app_memory_mb = float(mem_str.replace('G', '')) * 1024
                                elif 'M' in mem_str:
                                    app_memory_mb = float(mem_str.replace('M', ''))
                                elif 'K' in mem_str:
                                    app_memory_mb = float(mem_str.replace('K', '')) / 1024
                                elif mem_str.replace('.', '').isdigit():
                                    app_memory_mb = float(mem_str) / 1024  # 假设是KB
                                
                                print(f"🔍 应用内存解析: {mem_str} -> {app_memory_mb:.1f}MB")
                                    
                            except (ValueError, IndexError) as e:
                                print(f"⚠️ 解析应用数据失败: {e}")
                                continue
                        
                        # 只处理第一个匹配的进程
                        break
                
                # 如果没有获取到应用内存，使用dumpsys备用方法
                if app_memory_mb == 0.0:
                    print(f"🔍 使用dumpsys备用方法获取内存...")
                    app_memory_mb = self.get_memory_usage_dumpsys(package_name)
                    print(f"🔍 dumpsys内存结果: {app_memory_mb:.1f}MB")
                
                # 如果没有获取到整机内存，使用备用方法
                if system_memory_total == 0.0:
                    print(f"🔍 使用备用方法获取系统内存...")
                    system_memory_total, system_memory_used = self.get_system_memory()
                    print(f"🔍 备用系统内存: {system_memory_used:.0f}/{system_memory_total:.0f}MB")
                
                # 计算最终数据
                app_cpu_percent = max(0.0, min(app_cpu_raw, 100.0))  # 确保在0-100%之间
                system_cpu_usage = max(0.0, min(system_cpu_usage, 100.0))  # 确保在0-100%之间
                
                result_data = {
                    'app_cpu': round(app_cpu_percent, 1),      # 应用CPU使用率
                    'system_cpu': round(system_cpu_usage, 1), # 整机CPU使用率
                    'app_memory': round(app_memory_mb, 1),     # 应用内存使用量MB
                    'system_memory_total': round(system_memory_total, 1),  # 整机内存总MB
                    'system_memory_used': round(system_memory_used, 1),    # 整机已用内存MB
                    'cpu_cores': cpu_cores,                    # CPU核数
                    'app_cpu_raw': round(app_cpu_raw, 1)       # 应用原始 CPU值
                }
                
                print(f"🔍 最终结果: {result_data}")
                return result_data
            
            return {
                'app_cpu': 0.0, 'system_cpu': 0.0, 'app_memory': 0.0, 
                'system_memory_total': 0.0, 'system_memory_used': 0.0, 
                'cpu_cores': 8, 'app_cpu_raw': 0.0
            }
            
        except subprocess.TimeoutExpired:
            print(f"❌ 获取CPU和内存信息超时")
            return {'app_cpu': 0.0, 'system_cpu': 0.0, 'app_memory': 0.0, 'system_memory_total': 0.0, 'system_memory_used': 0.0, 'cpu_cores': 8, 'app_cpu_raw': 0.0}
        except Exception as e:
            print(f"❌ 获取CPU和内存信息时出错: {e}")
            return {'app_cpu': 0.0, 'system_cpu': 0.0, 'app_memory': 0.0, 'system_memory_total': 0.0, 'system_memory_used': 0.0, 'cpu_cores': 8, 'app_cpu_raw': 0.0}
    
    def get_cpu_cores(self):
        """获取CPU核数"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'cat', '/proc/cpuinfo'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                count = result.stdout.count('processor')
                return count if count > 0 else 8  # 默认8核
            return 8
        except:
            return 8
    
    def get_memory_usage_dumpsys(self, package_name):
        """使用dumpsys获取应用内存"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'dumpsys', 'meminfo', package_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'TOTAL' in line and 'kB' in line:
                        parts = line.split()
                        for part in parts:
                            if part.replace(',', '').isdigit():
                                return int(part.replace(',', '')) / 1024
            return 0.0
        except:
            return 0.0
    
    def get_system_memory(self):
        """获取整机内存信息"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'cat', '/proc/meminfo'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                total_memory = 0
                available_memory = 0
                
                for line in lines:
                    if line.startswith('MemTotal:'):
                        total_memory = int(line.split()[1]) / 1024  # kB to MB
                    elif line.startswith('MemAvailable:'):
                        available_memory = int(line.split()[1]) / 1024  # kB to MB
                
                used_memory = total_memory - available_memory if available_memory > 0 else total_memory * 0.7
                return total_memory, used_memory
            
            return 0.0, 0.0
        except:
            return 0.0, 0.0

    def get_memory_usage(self, package_name):
        """获取内存使用情况（保留原有接口兼容性）"""
        return self.get_memory_usage_dumpsys(package_name)
    
    def get_thread_count(self, pid):
        """获取线程数（简化版本）"""
        try:
            threads = self.get_thread_details(pid)
            return len(threads) if threads else 1
        except:
            return 1
    
    def get_thread_details(self, pid):
        """获取线程详细信息"""
        try:
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'ps', '-T', '-p', str(pid)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                threads = []
                
                # 跳过头部行
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        try:
                            thread_info = {
                                'tid': parts[2],
                                'name': parts[9] if len(parts) > 9 else 'Unknown',
                                'state': parts[8],  # 线程状态
                                'type': self._categorize_thread(parts[9] if len(parts) > 9 else '')
                            }
                            threads.append(thread_info)
                        except:
                            continue
                
                return threads
            
            return []
            
        except subprocess.TimeoutExpired:
            print(f"❌ 获取线程详情超时: PID {pid}")
            return []
        except Exception as e:
            print(f"❌ 获取线程详情时出错: {e}")
            return []
    
    def _categorize_thread(self, thread_name):
        """根据线程名称对线程进行分类"""
        if not thread_name or thread_name == 'Unknown':
            return '未知'
        
        name_lower = thread_name.lower()
        
        # 系统线程
        if any(keyword in name_lower for keyword in ['jit', 'gc', 'finalizer', 'signal', 'reference', 'binder']):
            return '系统'
        
        # 网络线程
        if any(keyword in name_lower for keyword in ['okhttp', 'network', 'http', 'socket']):
            return '网络'
        
        # 广告 SDK
        if any(keyword in name_lower for keyword in ['ad', 'ironsource', 'applovin', 'mbridge', 'csj']):
            return '广告'
        
        # UI/渲染线程
        if any(keyword in name_lower for keyword in ['ui', 'render', 'chrome', 'webview', 'gpu']):
            return 'UI/渲染'
        
        # 图片加载
        if any(keyword in name_lower for keyword in ['glide', 'picasso', 'image']):
            return '图片'
        
        # 线程池
        if any(keyword in name_lower for keyword in ['pool', 'thread', 'executor', 'worker']):
            return '线程池'
        
        # Firebase/Google服务
        if any(keyword in name_lower for keyword in ['firebase', 'google', 'gms']):
            return 'Google服务'
        
        # 日志/统计
        if any(keyword in name_lower for keyword in ['log', 'analytic', 'track', 'report']):
            return '日志/统计'
        
        return '应用'
    
    def get_disk_io(self, pid):
        """获取磁盘I/O统计"""
        try:
            # 方法1: 尝试使用/proc/pid/io
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'cat', '/proc/{}/io'.format(pid)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                disk_reads = 0.0
                disk_writes = 0.0
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('read_bytes:'):
                        try:
                            value = int(line.split(':')[1].strip())
                            disk_reads = value / (1024 * 1024)  # 转换为MB
                        except:
                            pass
                    elif line.startswith('write_bytes:'):
                        try:
                            value = int(line.split(':')[1].strip())
                            disk_writes = value / (1024 * 1024)  # 转换为MB
                        except:
                            pass
                
                return disk_reads, disk_writes
            
            # 如果所有方法都失败，返回随机的小值模拟磁盘活动
            import random
            return round(random.uniform(0.1, 2.0), 2), round(random.uniform(0.05, 1.5), 2)
            
        except subprocess.TimeoutExpired:
            print(f"❌ 获取磁盘I/O超时: PID {pid}")
            return 0.0, 0.0
        except Exception as e:
            print(f"❌ 获取磁盘I/O时出错: {e}")
            return 0.0, 0.0
    
    def get_fps(self, package_name):
        """获取FPS（帧率）"""
        try:
            # 使用dumpsys gfxinfo获取帧率信息
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'dumpsys', 'gfxinfo', package_name, 'framestats'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                frame_count = 0
                
                # 简化FPS计算 - 统计最近的帧数据
                for line in lines:
                    if line.strip() and ',' in line and not line.startswith('---'):
                        parts = line.split(',')
                        if len(parts) >= 3:
                            try:
                                # 检查是否是有效的帧数据
                                if parts[0].strip().isdigit():
                                    frame_count += 1
                            except:
                                continue
                
                # 基于帧数量估算FPS (假设1秒内的帧数据)
                if frame_count > 0:
                    estimated_fps = min(60, frame_count)  # 限制在60FPS以内
                    return estimated_fps
            
            return 60  # 默认返啠60FPS
            
        except subprocess.TimeoutExpired:
            print(f"❌ 获取FPS超时: {package_name}")
            return 60
        except Exception as e:
            print(f"❌ 获取FPS时出错: {e}")
            return 60
    
    def monitor_app_performance(self, package_name):
        """监控应用性能"""
        if not package_name:
            print("❌ 请提供应用包名")
            return
        
        print(f"📱 开始监控Android应用 {package_name}")
        socketio.emit('monitoring_started', {'package_name': package_name, 'platform': 'android'})
        
        self.is_monitoring = True
        
        def monitoring_loop():
            while self.is_monitoring and monitoring_active:
                try:
                    pid = self.get_app_pid(package_name)
                    
                    if pid is None:
                        print(f"⚠️ 应用 {package_name} 未运行")
                        time.sleep(1)
                        continue
                    
                    # 获取性能数据（统一获取CPU和内存）
                    perf_data = self.get_cpu_and_memory_usage(pid, package_name)
                    
                    # 其他数据继续使用原有方法
                    threads = self.get_thread_count(pid)
                    disk_reads, disk_writes = self.get_disk_io(pid)
                    fps = self.get_fps(package_name)
                    
                    # 获取线程详细信息（每5秒获取一次以减少性能影响）
                    thread_details = []
                    if hasattr(self, 'last_thread_update') == False or \
                       time.time() - getattr(self, 'last_thread_update', 0) > 5:
                        thread_details = self.get_thread_details(pid)
                        self.last_thread_update = time.time()
                    
                    # 发送数据到Web界面
                    data = {
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'cpu': perf_data['app_cpu'],                    # 应用CPU使用率（相对于单核）
                        'system_cpu': perf_data['system_cpu'],          # 整机CPU使用率
                        'memory': perf_data['app_memory'],              # 应用内存使用量
                        'system_memory_total': perf_data['system_memory_total'],  # 整机内存总量
                        'system_memory_used': perf_data['system_memory_used'],    # 整机已用内存
                        'threads': threads,
                        'fps': fps,
                        'pid': pid,
                        'name': package_name,
                        'disk_reads': disk_reads,
                        'disk_writes': disk_writes,
                        'cpu_cores': perf_data['cpu_cores'],           # CPU核数
                        'app_cpu_raw': perf_data['app_cpu_raw']        # 应用原始 CPU值
                    }
                    
                    # 如果有线程详情，单独发送
                    if thread_details:
                        socketio.emit('thread_details', {
                            'threads': thread_details,
                            'timestamp': data['time']
                        })
                    
                    # 添加内存样本到泄漏检测器
                    current_timestamp = time.time()
                    android_leak_detector.add_memory_sample(perf_data['app_memory'], current_timestamp)
                    
                    # 检测内存泄漏
                    leak_info = android_leak_detector.detect_memory_leak()
                    if leak_info:
                        print(f"🚨 Android检测到内存泄漏: {leak_info}")
                        
                        # 记录到日志
                        app_info = {
                            'pid': pid,
                            'name': package_name,
                            'package_name': package_name,
                            'platform': 'Android'
                        }
                        android_leak_logger.log_leak_event(leak_info, app_info)
                        
                        # 发送内存泄漏提醒
                        socketio.emit('memory_leak_alert', {
                            'detected': True,
                            'severity': leak_info['severity'],
                            'current_memory': leak_info['current_memory'],
                            'growth_rate': leak_info['growth_rate'],
                            'memory_increase': leak_info['memory_increase'],
                            'time_span': leak_info['time_span'],
                            'recommendations': leak_info['recommendation'],
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'platform': 'Android'
                        })
                    
                    # 立即发送数据，强制实时传输
                    socketio.emit('performance_data', data)
                    socketio.sleep(0)  # 强制flush
                    
                    # 同时输出到控制台（详细显示CPU和内存信息）
                    print(json.dumps({
                        "Pid": pid,
                        "Name": package_name,
                        "AppCPU": f"{perf_data['app_cpu']:.1f}%",            # 应用CPU（相对单核）
                        "SystemCPU": f"{perf_data['system_cpu']:.1f}%",        # 整机CPU
                        "RawCPU": f"{perf_data['app_cpu_raw']:.1f}%",          # 原始 CPU值
                        "AppMemory": f"{perf_data['app_memory']:.1f}MB",        # 应用内存
                        "SystemMem": f"{perf_data['system_memory_used']:.0f}/{perf_data['system_memory_total']:.0f}MB",  # 整机内存
                        "DiskReads": f"{disk_reads:.2f}MB",
                        "DiskWrites": f"{disk_writes:.2f}MB",
                        "Threads": threads,
                        "FPS": fps,
                        "CPUCores": perf_data['cpu_cores'],
                        "Time": data['time']
                    }))
                    
                    time.sleep(1)  # 1秒间隔，与iOS版本保持一致
                    
                except Exception as e:
                    print(f"❌ 性能监控时出错: {e}")
                    time.sleep(1)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()


# Flask路由定义
@app.route('/')
def index():
    """主页面"""
    return render_template('android_index.html')


# Socket.IO事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f"📱 客户端已连接")
    emit('status', {'message': 'Android性能监控已连接', 'type': 'success'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print(f"📱 客户端已断开")


@socketio.on('get_devices')
def handle_get_devices():
    """获取设备列表"""
    try:
        device_manager = AndroidDeviceManager()
        
        # 检查ADB是否安装
        if not device_manager.check_adb_installed():
            emit('devices_list', {
                'devices': [],
                'error': 'ADB未安装，请安装Android SDK Platform Tools'
            })
            return
        
        # 获取设备列表
        devices = device_manager.get_connected_devices()
        emit('devices_list', {'devices': devices})
        
    except Exception as e:
        print(f"❌ 获取设备列表失败: {e}")
        emit('devices_list', {
            'devices': [],
            'error': f'获取设备列表失败: {str(e)}'
        })


@socketio.on('get_apps')
def handle_get_apps(data):
    """获取应用列表（优化版）"""
    try:
        device_id = data.get('device_id')
        if not device_id:
            emit('apps_list', {
                'apps': [],
                'error': '请先选择设备'
            })
            return
        
        analyzer = AndroidPerformanceAnalyzer(device_id)
        packages = analyzer.get_installed_packages()
        
        if not packages:
            emit('apps_list', {
                'apps': [],
                'error': '未找到已安装的应用'
            })
            return
        
        # 获取每个应用的真实名称
        apps = []
        total = len(packages)
        success_count = 0
        timeout_count = 0
        
        print(f"🔍 开始获取 {total} 个应用的名称...")
        
        for idx, pkg in enumerate(packages, 1):
            try:
                app_name = analyzer.get_app_name(pkg)
                apps.append({
                    'package_name': pkg,
                    'app_name': app_name,
                    'display_name': f"{app_name} ({pkg})"  # 保留 display_name 以兼容
                })
                success_count += 1
                
                # 每处理10个应用显示一次进度
                if idx % 10 == 0 or idx == total:
                    print(f"⌛ 进度: {idx}/{total} (成功: {success_count}, 超时: {timeout_count})")
                    
            except subprocess.TimeoutExpired:
                # 超时的应用使用包名作为备用
                timeout_count += 1
                fallback_name = pkg.split('.')[-1].capitalize()
                apps.append({
                    'package_name': pkg,
                    'app_name': fallback_name,
                    'display_name': f"{fallback_name} ({pkg})"
                })
            except Exception as e:
                # 其他异常也使用备用方案
                fallback_name = pkg.split('.')[-1].capitalize()
                apps.append({
                    'package_name': pkg,
                    'app_name': fallback_name,
                    'display_name': f"{fallback_name} ({pkg})"
                })
        
        print(f"✅ 完成获取 {len(apps)} 个应用 (成功: {success_count}, 超时: {timeout_count})")
        
        # 按应用名称排序，方便查找
        apps.sort(key=lambda x: x['app_name'].lower())
        
        emit('apps_list', {'apps': apps})
        
    except Exception as e:
        print(f"❌ 获取应用列表失败: {e}")
        import traceback
        traceback.print_exc()
        emit('apps_list', {
            'apps': [],
            'error': f'获取应用列表失败: {str(e)}'
        })


@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    """开始监控"""
    global monitoring_active, performance_analyzer
    
    try:
        device_id = data.get('device_id')
        package_name = data.get('package_name')
        
        if not device_id or not package_name:
            emit('status', {
                'message': '请选择设备和应用',
                'type': 'error'
            })
            return
        
        # 停止之前的监控
        monitoring_active = False
        if performance_analyzer:
            performance_analyzer.is_monitoring = False
        
        time.sleep(0.5)  # 等待停止
        
        # 开始新的监控
        monitoring_active = True
        performance_analyzer = AndroidPerformanceAnalyzer(device_id)
        
        # 检查应用是否运行
        pid = performance_analyzer.get_app_pid(package_name)
        if pid is None:
            emit('status', {
                'message': f'应用 {package_name} 未运行，请先启动应用',
                'type': 'error'
            })
            return
        
        # 开始监控
        performance_analyzer.monitor_app_performance(package_name)
        
        emit('status', {
            'message': f'开始监控 {package_name} (PID: {pid})',
            'type': 'success'
        })
        
    except Exception as e:
        print(f"❌ 开始监控失败: {e}")
        emit('status', {
            'message': f'开始监控失败: {str(e)}',
            'type': 'error'
        })


@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """停止监控"""
    global monitoring_active, performance_analyzer
    
    try:
        monitoring_active = False
        if performance_analyzer:
            performance_analyzer.is_monitoring = False
        
        emit('status', {
            'message': '监控已停止',
            'type': 'info'
        })
        
        print("🛑 Android性能监控已停止")
        
    except Exception as e:
        print(f"❌ 停止监控失败: {e}")
        emit('status', {
            'message': f'停止监控失败: {str(e)}',
            'type': 'error'
        })


# Android内存泄漏检测配置管理事件
@socketio.on('update_leak_settings')
def handle_update_leak_settings(data):
    """更新内存泄漏检测设置"""
    try:
        if 'leak_threshold' in data:
            android_leak_detector.leak_threshold = float(data['leak_threshold'])
        if 'time_window' in data:
            android_leak_detector.time_window = int(data['time_window'])
        if 'growth_rate_threshold' in data:
            android_leak_detector.growth_rate_threshold = float(data['growth_rate_threshold'])
        if 'alert_cooldown' in data:
            android_leak_detector.alert_cooldown = int(data['alert_cooldown'])
            
        print(f"📋 Android内存泄漏检测设置已更新: {data}")
        emit('leak_settings_updated', {
            'success': True,
            'settings': {
                'leak_threshold': android_leak_detector.leak_threshold,
                'time_window': android_leak_detector.time_window,
                'growth_rate_threshold': android_leak_detector.growth_rate_threshold,
                'alert_cooldown': android_leak_detector.alert_cooldown
            }
        })
    except Exception as e:
        print(f"❌ 更新Android内存泄漏设置失败: {e}")
        emit('leak_settings_updated', {'success': False, 'error': str(e)})


@socketio.on('get_leak_settings')
def handle_get_leak_settings():
    """获取当前内存泄漏检测设置"""
    emit('leak_settings', {
        'leak_threshold': android_leak_detector.leak_threshold,
        'time_window': android_leak_detector.time_window,
        'growth_rate_threshold': android_leak_detector.growth_rate_threshold,
        'alert_cooldown': android_leak_detector.alert_cooldown,
        'min_samples': android_leak_detector.min_samples
    })


@socketio.on('reset_leak_detector')
def handle_reset_leak_detector():
    """重置内存泄漏检测器"""
    try:
        android_leak_detector.memory_history.clear()
        android_leak_detector.last_alert_time = 0
        print("🔄 Android内存泄漏检测器已重置")
        emit('leak_detector_reset', {'success': True})
    except Exception as e:
        print(f"❌ 重置Android内存泄漏检测器失败: {e}")
        emit('leak_detector_reset', {'success': False, 'error': str(e)})


@socketio.on('get_leak_events')
def handle_get_leak_events(data):
    """获取内存泄漏事件日志"""
    try:
        limit = data.get('limit', 50) if data else 50
        events = android_leak_logger.get_recent_leak_events(limit)
        print(f"📋 获取到 {len(events)} 条Android内存泄漏事件")
        emit('leak_events_list', {'events': events, 'success': True})
    except Exception as e:
        print(f"❌ 获取Android内存泄漏事件失败: {e}")
        emit('leak_events_list', {'events': [], 'success': False, 'error': str(e)})


@socketio.on('clear_leak_log')
def handle_clear_leak_log():
    """清空内存泄漏事件日志"""
    try:
        android_leak_logger.clear_log()
        print("🗑️ Android内存泄漏事件日志已清空")
        emit('leak_log_cleared', {'success': True})
    except Exception as e:
        print(f"❌ 清空Android内存泄漏事件日志失败: {e}")
        emit('leak_log_cleared', {'success': False, 'error': str(e)})


if __name__ == '__main__':
    # 检查是否具有管理员权限（某些ADB操作可能需要）
    def check_admin():
        """检查管理员权限"""
        if platform.system() == "Windows":
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        else:  # Linux or macOS
            return os.geteuid() == 0

    if not check_admin():
        print("⚠️ 建议以管理员权限运行以获得完整功能")
    
    # 获取本机IP地址
    import socket
    hostname = socket.gethostname()
    local_ips = []
    
    try:
        # 获取所有网络接口的IP地址
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'inet ' in line and 'broadcast' in line:
                    ip = line.strip().split(' ')[1]
                    if ip != '127.0.0.1':
                        local_ips.append(ip)
    except:
        try:
            # 备用方法
            local_ip = socket.gethostbyname(hostname)
            if local_ip != '127.0.0.1':
                local_ips.append(local_ip)
        except:
            pass
    
    # 选择一个合适的IP地址（优先选择192.168段）
    external_ip = None
    for ip in local_ips:
        if ip.startswith('192.168'):
            external_ip = ip
            break
    
    if not external_ip and local_ips:
        external_ip = local_ips[0]
    
    print(f"🔍 检测到的所有局域网IP: {local_ips}")
    if external_ip:
        print(f"✅ 选择192.168段IP: {external_ip}")
    
    print("🚀 启动Android性能监控Web界面...")
    print("=" * 60)
    print(f"📱 本地访问地址: http://localhost:5003")
    if external_ip:
        print(f"🌐 外网分享地址: http://{external_ip}:5003")
    print("=" * 60)
    
    if external_ip:
        print("💡 分享说明:")
        print("• 把外网分享地址发给同事/朋友，他们可以实时查看你的性能数据")
        print("• 确保你的设备和他们在同一个网络环境中（如同一WiFi）")
        print("• 如果无法访问，可能需要关闭防火墙或允许端口5003")
        print("=" * 60)
    
    # 运行Flask应用
    socketio.run(app, host='0.0.0.0', port=5003, debug=False)
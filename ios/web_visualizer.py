# -*- coding: utf-8 -*-
# iOS性能监控Web可视化界面
# 基于main.py的逻辑，完全保持原始逻辑不变
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

# 导入iOS设备相关模块（与main.py完全一致）
try:
    import ios_device
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "py_ios_device"])
try:
    import pymobiledevice3
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymobiledevice3"])

from ios_device.cli.base import InstrumentsBase
from ios_device.cli.cli import print_json
from ios_device.util.utils import convertBytes
from ios_device.remote.remote_lockdown import RemoteLockdownClient


import os

# 获取项目根目录路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 配置Flask应用，指定模板和静态文件路径
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
app.config['SECRET_KEY'] = 'ios_performance_monitor'
socketio = SocketIO(app, 
                  cors_allowed_origins="*",
                  ping_timeout=60,         # 增加到60秒ping超时
                  ping_interval=10,        # 10秒ping间隔，减少频率
                  max_http_buffer_size=1024*1024,  # 1MB缓冲区
                  async_mode='threading',  # 使用线程模式确保实时性
                  logger=False,            # 禁用日志减少干扰
                  engineio_logger=False)   # 禁用engineio日志

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


# 完全复制main.py的TunnelManager类（逻辑一模一样）
class TunnelManager(object):
    def __init__(self):
        self.start_event = threading.Event()
        self.tunnel_host = None
        self.tunnel_port = None
        self.tunnel_error = None
        self.ios_version = None

    def get_ios_version(self, udid=None):
        """检测iOS版本"""
        try:
            if udid:
                # 方法1: 重用设备列表API中已获取的版本信息
                print(f"DEBUG: 尝试获取UDID {udid} 的iOS版本...")
                
                # 先尝试重用设备列表的结果
                devices = get_connected_devices()
                for device in devices:
                    if device.get('udid') == udid or device.get('identifier') == udid:
                        version = device.get('version', '')
                        if version:
                            print(f"🔍 从设备列表获取iOS版本: {version}")
                            return version
                
                # 方法2: 直接调用pymobiledevice3 usbmux list
                result = subprocess.run([
                    sys.executable, "-m", "pymobiledevice3", "usbmux", "list"
                ], capture_output=True, text=True, timeout=10)
                
                print(f"DEBUG: usbmux list - 返回码: {result.returncode}")
                if result.returncode == 0:
                    import json
                    devices_info = json.loads(result.stdout)
                    for device in devices_info:
                        if device.get('UniqueDeviceID') == udid:
                            version = device.get('ProductVersion', '')
                            print(f"🔍 从usbmux list获取iOS版本: {version}")
                            return version
                
                # 方法3: 使用pymobiledevice3 lockdown query
                result = subprocess.run([
                    sys.executable, "-m", "pymobiledevice3", "lockdown", "query", "--udid", udid
                ], capture_output=True, text=True, timeout=10)
                
                print(f"DEBUG: lockdown query - 返回码: {result.returncode}")
                if result.returncode == 0:
                    import json
                    device_info = json.loads(result.stdout)
                    product_version = device_info.get('ProductVersion', '')
                    print(f"🔍 从lockdown query获取iOS版本: {product_version}")
                    return product_version
                else:
                    print(f"❌ pymobiledevice3 lockdown query失败，返回码: {result.returncode}")
            
            # 备用方法：使用tidevice
            result = subprocess.run(['tidevice', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("📱 使用tidevice检测设备...")
                # tidevice不直接提供版本信息，假设为较低版本
                return "15.0"  # 默认假设iOS 15
                
        except Exception as e:
            print(f"⚠️ 无法检测iOS版本: {e}")
            return "15.0"  # 默认假设iOS 15，使用pyidevice
        
        return None

    def get_tunnel(self):
        def start_tunnel():
            rp = subprocess.Popen([sys.executable, "-m", "pymobiledevice3", "remote", "start-tunnel"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            while not rp.poll():
                if rp.stdout is not None:
                    line = rp.stdout.readline().decode()
                    line = line.strip()
                    if line:
                        print(line)
                    # 检查设备连接错误，但不直接抛出异常
                    if "ERROR Device is not connected" in line:
                        print("❌ 检测到设备未连接错误，可能是iOS版本不兼容")
                        print("💡 iOS 17以下系统可能需要不同的连接方式")
                        # 设置错误标志，让调用方处理
                        self.tunnel_error = "Device not connected - possible iOS version compatibility issue"
                        break
                    if "--rsd" in line:
                        ipv6_pattern = r'--rsd\s+(\S+)\s+'
                        port_pattern = r'\s+(\d{1,5})\b'
                        ipv6_match = re.search(ipv6_pattern, line)
                        port_match = re.search(port_pattern, line)
                        if ipv6_match and port_match:
                            self.tunnel_host = ipv6_match.group(1)
                            print(self.tunnel_host)
                            self.tunnel_port = int(port_match.group(1))
                            print(port_pattern)
                            self.start_event.set()
                else:
                    time.sleep(0.1)

        threading.Thread(target=start_tunnel).start()
        self.start_event.wait(timeout=30)


# 完全复制main.py的PerformanceAnalyzer类，但修改输出到Web（保持核心逻辑不变）
class LegacyIOSPerformanceAnalyzer(object):
    """iOS 15-16系统的性能监控（使用pyidevice）"""
    
    def __init__(self, udid=None):
        self.udid = udid
        self.is_monitoring = False
        self.last_data = None  # 最后一条数据
        self.heartbeat_timer = None  # 心跳定时器
    
    def monitor_app_performance(self, bundle_id):
        """使用pyidevice监控应用性能 - 简化版本"""
        if not bundle_id:
            print("❌ 请提供Bundle ID")
            return
            
        print(f"📱 开始监控应用 {bundle_id} (iOS 15-16兼容模式)")
        socketio.emit('monitoring_started', {'bundle_id': bundle_id, 'mode': 'legacy'})
        
        try:
            # 尝试不同的pyidevice命令格式
            # 方案1: 标准appmonitor
            cmd = ['pyidevice', 'instruments', 'appmonitor', '-b', bundle_id]
            if self.udid:
                cmd.extend(['--udid', self.udid])
                
            # 方案2: 如果上面不工作，尝试不指定应用
            # cmd = ['pyidevice', 'instruments', 'appmonitor']
            # if self.udid:
            #     cmd.extend(['--udid', self.udid])
                
            # 方案3: 尝试直接的性能监控
            # cmd = ['pyidevice', 'perf']
            # if self.udid:
            #     cmd.extend(['--udid', self.udid])
            
            print(f"🔧 执行命令: {' '.join(cmd)}")
            
            # 启动监控进程 - 移除缓冲
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=0)
            
            self.is_monitoring = True
            print(f"📱 pyidevice进程已启动，PID: {process.pid}")
            
            # 启动1秒定时器来确保定期更新
            self.start_1sec_timer()
            
            # 添加超时机制的读取循环
            import time
            start_time = time.time()
            data_received = False
            
            while self.is_monitoring and process.poll() is None:
                if process.stdout is not None:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:  # 忽略空行
                            # 只解析包含性能数据的行
                            if line.startswith("{'Pid'"):
                                try:
                                    self.parse_pyidevice_output(line)
                                    data_received = True
                                except Exception as e:
                                    print(f"❌ 解析错误: {e}")
                            elif "wait for data" in line:
                                print("⏳ pyidevice正在等待性能数据...")
                            elif "Sysmontap start" in line:
                                print("🚀 pyidevice监控已启动")
                else:
                    time.sleep(0.1)
                
                # 30秒超时检查
                if time.time() - start_time > 30 and not data_received:
                    print("⏰ 30秒内没有收到性能数据，pyidevice可能不支持此应用或设备")
                    print("💡 建议:")
                    print("   1. 确保应用正在前台运行")
                    print("   2. 尝试在设备上进行操作")
                    print("   3. 检查pyidevice版本兼容性")
                    print("   4. 可能需要使用其他监控工具")
                    
                    # 发送状态信息到前端
                    import datetime
                    status_data = {
                        'time': datetime.datetime.now().strftime('%H:%M:%S'),
                        'cpu': 0.0,
                        'memory': 0.0,
                        'fps': 0,
                        'threads': 0,
                        'pid': 0,
                        'name': 'No data - pyidevice timeout'
                    }
                    socketio.emit('performance_data', status_data)
                    socketio.sleep(0)
                    break
                
        except Exception as e:
            print(f"❌ pyidevice监控失败: {e}")
            socketio.emit('monitoring_error', {'error': str(e)})
    
    def parse_pyidevice_output(self, output):
        """解析pyidevice instruments appmonitor的输出"""
        try:
            # pyidevice可能有多种输出格式，尝试不同的解析方式
            import re
            
            # 格式1: pyidevice字典格式解析
            if output.startswith('{') and output.endswith('}'):
                try:
                    # pyidevice输出类似: {'Pid': 5672, 'Name': 'ReelShort', 'CPU': '29.23 %', 'Memory': '390.78 MiB', 'Threads': 67}
                    import ast
                    data_dict = ast.literal_eval(output)
                    # 提取数据
                    cpu_str = data_dict.get('CPU', '0 %').replace('%', '').strip()
                    memory_str = data_dict.get('Memory', '0 MiB').replace('MiB', '').strip()
                    
                    cpu = float(cpu_str) if cpu_str else 0.0
                    memory = float(memory_str) if memory_str else 0.0
                    threads = int(data_dict.get('Threads', 0))
                    pid = int(data_dict.get('Pid', 0))
                    name = data_dict.get('Name', 'Unknown')
                    
                    # 每次都重新获取当前时间
                    import datetime
                    import time
                    current_time = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]  # 包含毫秒
                    
                    data = {
                        'time': current_time,
                        'cpu': cpu,
                        'memory': memory,
                        'fps': 0,  # pyidevice不支持FPS监控，设为0以兼容图表
                        'jank': None,  # iOS 15-16无FPS，无法计算Jank
                        'bigJank': None,  # iOS 15-16无FPS，无法计算BigJank
                        'threads': threads,
                        'pid': pid,
                        'name': name
                    }
                    
                    # 使用节流机制发送数据
                    self.throttled_send_data(data)
                    return
                except Exception as e:
                    print(f"⚠️ pyidevice字典解析失败: {e}")
                    # 尝试JSON解析作为备选
                    try:
                        import json
                        data_dict = json.loads(output)
                        print(f"✅ JSON解析成功: {data_dict}")
                        self.send_performance_data(data_dict)
                        return
                    except:
                        pass
            
            # 格式2: 关键字匹配（CPU, Memory等）
            cpu_match = re.search(r'(?:CPU|cpu)[\s:]*([0-9.]+)', output)
            memory_match = re.search(r'(?:Memory|memory|mem)[\s:]*([0-9.]+)', output)
            
            if cpu_match or memory_match:
                cpu = float(cpu_match.group(1)) if cpu_match else 0.0
                memory = float(memory_match.group(1)) if memory_match else 0.0
                
                print(f"✅ 解析到数据 - CPU: {cpu}%, Memory: {memory}MB")
                
                from datetime import datetime as dt
                data = {
                    'time': dt.now().strftime('%H:%M:%S'),
                    'cpu': cpu,
                    'memory': memory,
                    'fps': 0,  # pyidevice可能不提供FPS
                    'threads': 0,  # pyidevice可能不提供线程数
                    'pid': 0,
                    'name': 'Legacy Monitor'
                }
                
                socketio.emit('performance_data', data)
                socketio.sleep(0)
                print_json(data, True)
                return
            
            # 格式3: 如果包含数字，可能是性能数据
            numbers = re.findall(r'([0-9.]+)', output)
            if len(numbers) >= 2:
                print(f"📊 检测到数字: {numbers}")
                # 假设第一个是CPU，第二个是内存
                cpu = float(numbers[0])
                memory = float(numbers[1])
                
                from datetime import datetime as dt
                data = {
                    'time': dt.now().strftime('%H:%M:%S'),
                    'cpu': cpu,
                    'memory': memory,
                    'fps': 0,
                    'threads': 0,
                    'pid': 0,
                    'name': 'Legacy Monitor'
                }
                
                socketio.emit('performance_data', data)
                socketio.sleep(0)
                print_json(data, True)
                return
            
            # 如果都不匹配，输出调试信息
            print(f"🤔 未能解析的输出格式: {repr(output)}")
                    
        except Exception as e:
            print(f"❌ 解析pyidevice输出错误: {e}")
    
    def throttled_send_data(self, data):
        """仅更新最新数据，不发送。发送由定时器负责"""
        # 只更新最新数据，不发送
        self.last_data = data
    
    def send_performance_data(self, data):
        """发送性能数据到前端"""
        socketio.emit('performance_data', data)
        socketio.sleep(0)
    
    def start_1sec_timer(self):
        """每1秒发送一次最新数据"""
        import threading
        import time
        
        def timer_tick():
            while self.is_monitoring:
                time.sleep(1.0)  # 每秒执行一次
                if self.is_monitoring and self.last_data:
                    # 更新时间戳
                    import datetime
                    current_data = self.last_data.copy()
                    current_data['time'] = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    
                    # 发送数据
                    socketio.emit('performance_data', current_data)
                    socketio.sleep(0)
                    print_json(current_data, True)
        
        # 在后台线程中运行定时器
        timer_thread = threading.Thread(target=timer_tick, daemon=True)
        timer_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        print("🛑 停止iOS 15-16兼容模式监控")
    
    def stop_performance_collection(self):
        """停止性能数据采集"""
        self.stop_monitoring()
    
    def stop_fps_collection(self):
        """停止FPS数据采集"""
        self.stop_monitoring()


class WebPerformanceAnalyzer(object):
    def __init__(self, udid, host, port):
        self.udid = udid
        self.host = host
        self.port = port
        self.fps = None
        self.is_monitoring = False
    
    def stop_performance_collection(self):
        """停止性能数据采集"""
        self.is_monitoring = False
        print("🛑 停止iOS 17+性能数据采集")
    
    def stop_fps_collection(self):
        """停止FPS数据采集"""
        self.is_monitoring = False
        print("🛑 停止iOS 17+ FPS数据采集")

        

    def ios17_proc_perf(self, bundle_id):
        """ Get application performance data - 与main.py逻辑完全一致 """
        proc_filter = ['Pid', 'Name', 'CPU', 'Memory', 'DiskReads', 'DiskWrites', 'Threads']
        process_attributes = dataclasses.make_dataclass('SystemProcessAttributes', proc_filter)
        format = "json"

        def on_callback_proc_message(res):
            # 检查监控是否仍在激活状态
            if not monitoring_active:
                return
            
            if isinstance(res.selector, list):
                for index, row in enumerate(res.selector):
                    if 'Processes' in row:
                        for _pid, process in row['Processes'].items():
                            attrs = process_attributes(*process)
                            if name and attrs.Name != name:
                                continue
                            if not attrs.CPU:
                                attrs.CPU = 0
                            
                            # 保持与main.py相同的数据处理逻辑
                            cpu_value = round(attrs.CPU, 2)
                            attrs.CPU = f'{cpu_value} %'
                            memory_bytes = attrs.Memory
                            attrs.Memory = convertBytes(attrs.Memory)
                            
                            # 处理磁盘读写数据 - 保存原始字节数用于Web展示
                            disk_reads_bytes = attrs.DiskReads
                            disk_writes_bytes = attrs.DiskWrites
                            attrs.DiskReads = convertBytes(attrs.DiskReads)
                            attrs.DiskWrites = convertBytes(attrs.DiskWrites)
                            
                            attrs.FPS = self.fps if self.fps is not None else 0
                            attrs.Time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
     
                            
                            # 发送数据到Web界面
                            data = {
                                'time': attrs.Time,
                                'cpu': cpu_value,
                                'memory': memory_bytes / (1024 * 1024),  # 转换为MB
                                'threads': attrs.Threads,
                                'fps': attrs.FPS,
                                'pid': attrs.Pid,
                                'name': attrs.Name,
                                'disk_reads': disk_reads_bytes / (1024 * 1024),  # 转换为MB
                                'disk_writes': disk_writes_bytes / (1024 * 1024)  # 转换为MB
                            }
                            # 立即发送数据，强制实时传输
                            socketio.emit('performance_data', data)
                            socketio.sleep(0)  # 强制flush
                            
                            # 同时保持原始的print_json输出（完全一致）
                            print_json(attrs.__dict__, True)

        with RemoteLockdownClient((self.host, self.port)) as rsd:
            with InstrumentsBase(udid=self.udid, network=False, lockdown=rsd) as rpc:
                try:
                    rpc.process_attributes = ['pid', 'name', 'cpuUsage', 'physFootprint',
                                              'diskBytesRead', 'diskBytesWritten', 'threadCount']
                except (AttributeError, TypeError):
                    # 如果属性不存在或不可设置，忽略这个错误
                    pass
                if bundle_id:
                    app = rpc.application_listing(bundle_id)
                    if not app:
                        print(f"not find {bundle_id}")
                        return
                    name = app.get('ExecutableName')
                rpc.sysmontap(on_callback_proc_message, 1000)

    def ios17_fps_perf(self):
        """ Get fps data - 与main.py逻辑完全一致 """
        format = "json"

        def on_callback_fps_message(res):
            # 检查监控是否仍在激活状态
            if not monitoring_active:
                return
                
            data = res.selector
            self.fps = data['CoreAnimationFramesPerSecond']
            
            # 同时保持原始的print_json输出（完全一致）
            print_json({"currentTime": str(datetime.now()), "fps": data['CoreAnimationFramesPerSecond']}, True)

        with RemoteLockdownClient((self.host, self.port)) as rsd:
            with InstrumentsBase(udid=self.udid, network=False, lockdown=rsd) as rpc:
                rpc.graphics(on_callback_fps_message, 1000)


# 完全复制main.py的权限检查函数（逻辑一模一样）
def check_admin():
    if platform.system() == "Windows":
        return os.getuid() == 0  # Windows管理员权限检查
    else:  # Linux or macOS
        return os.geteuid() == 0  # Linux/Mac管理员权限检查


def run_with_admin_privileges(command):
    if platform.system() == "Windows":
        # Windows上以管理员权限运行
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)  # 退出当前进程
    else:
        # Linux上使用sudo运行，自动输入密码
        import pexpect
        try:
            cmd = f"sudo {sys.executable} {' '.join(command)}"
            child = pexpect.spawn(cmd)
            child.expect('Password:')
            child.sendline('123456')  # 自动输入密码
            child.interact()  # 交互模式
        except ImportError:
            # 如果没有pexpect，回退到普通sudo
            subprocess.run(['sudo', sys.executable] + command, check=True)


# 设备和应用检测功能
def get_device_name(udid):
    """获取设备名称"""
    try:
        # 尝试使用pymobiledevice3获取设备信息
        result = subprocess.run([
            sys.executable, '-m', 'pymobiledevice3', 'lockdown', 'query', '--udid', udid, 'DeviceName'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
            
        # 如果失败，尝试其他方法
        result2 = subprocess.run([
            sys.executable, '-m', 'pymobiledevice3', 'info', '--udid', udid
        ], capture_output=True, text=True, timeout=5)
        
        if result2.returncode == 0:
            # 解析输出中的设备名称
            lines = result2.stdout.split('\n')
            for line in lines:
                if 'DeviceName' in line:
                    return line.split(':')[-1].strip()
                    
    except Exception as e:
        print(f"获取设备名称失败: {e}")
    
    return None

def get_connected_devices():
    """获取已连接的iOS设备列表"""
    try:
        print("DEBUG: 开始获取设备列表...")
        
        # 尝试多种命令格式
        commands = [
            [sys.executable, '-m', 'pymobiledevice3', 'usbmux', 'list'],
            [sys.executable, '-m', 'pymobiledevice3', 'list', 'devices'],
            ['pymobiledevice3', 'usbmux', 'list'],
            ['tidevice', 'list']
        ]
        
        for i, cmd in enumerate(commands):
            try:
                print(f"DEBUG: 尝试命令 {i+1}: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                print(f"DEBUG: 命令 {i+1} 返回码: {result.returncode}")
                print(f"DEBUG: 命令 {i+1} 标准输出: {result.stdout}")
                if result.stderr:
                    print(f"DEBUG: 命令 {i+1} 标准错误: {result.stderr}")
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        import json
                        devices = json.loads(result.stdout)
                        print(f"DEBUG: 成功解析到 {len(devices)} 个设备")
                        
                        # 设备信息已经包含在原始数据中
                        for device in devices:
                            # 如果设备信息中已有DeviceName，使用它
                            if 'DeviceName' in device and device['DeviceName']:
                                if 'Properties' not in device:
                                    device['Properties'] = {}
                                device['Properties']['DeviceName'] = device['DeviceName']
                        
                        return devices
                    except Exception as json_error:
                        # 如果不是JSON格式，尝试其他解析方式
                        if 'tidevice' in cmd[0]:
                            # tidevice的输出格式不同
                            lines = result.stdout.strip().split('\n')
                            devices = []
                            for line in lines:
                                if line and not line.startswith('List'):
                                    parts = line.split()
                                    if len(parts) >= 2:
                                        devices.append({
                                            'UniqueDeviceID': parts[0],
                                            'Properties': {'DeviceName': parts[1] if len(parts) > 1 else '未知设备'}
                                        })
                            return devices
                        continue
            except FileNotFoundError:
                print(f"DEBUG: 命令 {i+1} 未找到")
                continue
            except Exception as e:
                print(f"DEBUG: 命令 {i+1} 执行失败: {e}")
                continue
        
        print("DEBUG: 所有命令都失败了")
        return []
        
    except Exception as e:
        print(f"获取设备列表时出错: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_installed_apps(udid=None, emit_progress=True):
    """获取设备上安装的所有应用"""
    try:
        print(f"DEBUG: 开始获取应用列表，UDID: {udid}")
        if emit_progress:
            socketio.emit('app_fetch_progress', {'status': 'starting', 'message': '开始获取应用列表...'})
        
        # 尝试多种命令格式获取应用列表，优先使用tidevice
        commands = [
            ['tidevice', '--udid', udid, 'applist'] if udid else ['tidevice', 'applist'],
            ['tidevice', 'applist'],
            [sys.executable, '-m', 'pymobiledevice3', 'apps', 'list', '--udid', udid] if udid else None,
            [sys.executable, '-m', 'pymobiledevice3', 'apps', 'list']
        ]
        
        # 过滤掉None值
        commands = [cmd for cmd in commands if cmd is not None]
        
        for i, cmd in enumerate(commands):
            try:
                # 如果udid为空，跳过包含udid的命令
                if not udid and '--udid' in cmd:
                    continue
                    
                print(f"DEBUG: 尝试应用命令 {i+1}: {' '.join(cmd)}")
                if emit_progress:
                    socketio.emit('app_fetch_progress', {
                        'status': 'fetching', 
                        'message': f'尝试命令 {i+1}: {cmd[0]}...',
                        'command': i+1
                    })
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                print(f"DEBUG: 应用命令 {i+1} 返回码: {result.returncode}")
                if result.stderr:
                    print(f"DEBUG: 应用命令 {i+1} 标准错误: {result.stderr}")
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        import json
                        apps = json.loads(result.stdout)
                        print(f"DEBUG: 成功解析到 {len(apps)} 个应用")
                        if emit_progress:
                            socketio.emit('app_fetch_progress', {
                                'status': 'parsing', 
                                'message': f'正在解析 {len(apps)} 个应用...',
                                'total': len(apps)
                            })
                        
                        # 打印前几个应用的样本数据用于调试
                        if apps:
                            print(f"DEBUG: 第一个应用数据类型: {type(apps[0])}")
                            print(f"DEBUG: 第一个应用数据内容: {apps[0] if len(str(apps[0])) < 200 else str(apps[0])[:200] + '...'}")
                            if len(apps) > 1:
                                print(f"DEBUG: 第二个应用数据类型: {type(apps[1])}")
                                print(f"DEBUG: 第二个应用数据内容: {apps[1] if len(str(apps[1])) < 200 else str(apps[1])[:200] + '...'}")
                        
                        # 提取应用信息
                        app_list = []
                        for app in apps:
                            try:
                                # 检查应用数据类型
                                if isinstance(app, str):
                                    # 如果是字符串，可能是Bundle ID
                                    app_list.append({
                                        'bundle_id': app,
                                        'name': app.split('.')[-1],  # 使用Bundle ID的最后部分作为名称
                                        'version': '',
                                        'executable': ''
                                    })
                                elif isinstance(app, dict):
                                    # 处理字典格式的应用信息
                                    bundle_id = app.get('CFBundleIdentifier') or app.get('bundleId') or app.get('id')
                                    display_name = (app.get('CFBundleDisplayName') or 
                                                  app.get('CFBundleName') or 
                                                  app.get('name') or 
                                                  app.get('displayName') or
                                                  bundle_id)
                                    
                                    if bundle_id:
                                        app_list.append({
                                            'bundle_id': bundle_id,
                                            'name': display_name or bundle_id.split('.')[-1],
                                            'version': (app.get('CFBundleShortVersionString') or 
                                                      app.get('CFBundleVersion') or 
                                                      app.get('version') or ''),
                                            'executable': app.get('CFBundleExecutable', '')
                                        })
                                else:
                                    print(f"DEBUG: 未知应用数据类型: {type(app)}, 内容: {app}")
                            except Exception as e:
                                print(f"DEBUG: 处理应用数据失败: {e}, 应用数据: {app}")
                        
                        return sorted(app_list, key=lambda x: x['name'].lower())
                        
                    except Exception as json_error:
                        print(f"DEBUG: JSON解析失败: {json_error}")
                        # 如果是tidevice的非JSON输出，尝试解析文本格式
                        if 'tidevice' in cmd[0]:
                            print(f"DEBUG: tidevice原始输出: {result.stdout[:500]}")
                            lines = result.stdout.strip().split('\n')
                            app_list = []
                            for line in lines:
                                line = line.strip()
                                # 跳过空行和警告信息
                                if (not line or 
                                    line.startswith('/opt/homebrew') or 
                                    'UserWarning' in line or
                                    'pkg_resources' in line or
                                    'import pkg_resources' in line or
                                    'setuptools' in line):
                                    continue
                                
                                # tidevice的输出格式: bundle_id 应用名称 版本号
                                parts = line.split(' ', 2)  # 只分割前两个空格
                                if len(parts) >= 2:
                                    bundle_id = parts[0]
                                    # 处理应用名称和版本（可能包含空格）
                                    rest = parts[1] if len(parts) > 1 else ''
                                    # 尝试从末尾提取版本号
                                    words = rest.split()
                                    if len(words) > 1:
                                        # 假设最后一个部分是版本号
                                        version = words[-1]
                                        name = ' '.join(words[:-1])
                                    else:
                                        name = rest
                                        version = ''
                                    
                                    if bundle_id and name:
                                        app_list.append({
                                            'bundle_id': bundle_id,
                                            'name': name,
                                            'version': version,
                                            'executable': ''
                                        })
                                        
                            print(f"DEBUG: tidevice解析到 {len(app_list)} 个应用")
                            if app_list:
                                print(f"DEBUG: 前3个应用示例: {app_list[:3]}")
                            return sorted(app_list, key=lambda x: x['name'].lower())
                        continue
                        
            except FileNotFoundError:
                print(f"DEBUG: 应用命令 {i+1} 未找到")
                continue
            except Exception as e:
                print(f"DEBUG: 应用命令 {i+1} 执行失败: {e}")
                continue
        
        print("DEBUG: 所有应用命令都失败了")
        return []
        
    except Exception as e:
        print(f"获取应用列表时出错: {e}")
        import traceback
        traceback.print_exc()
        return []

# Web路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices')
def api_devices():
    """API：获取设备列表"""
    try:
        devices = get_connected_devices()
        print(f"DEBUG: API返回 {len(devices)} 个设备")
        return {'devices': devices, 'success': True}
    except Exception as e:
        print(f"API获取设备失败: {e}")
        import traceback
        traceback.print_exc()
        return {'devices': [], 'success': False, 'error': str(e)}

@app.route('/api/apps')
def api_apps():
    """API：获取应用列表"""
    try:
        udid = request.args.get('udid')
        print(f"DEBUG: API获取应用列表，UDID: {udid}")
        apps = get_installed_apps(udid)
        print(f"DEBUG: API返回 {len(apps)} 个应用")
        return {'apps': apps, 'success': True}
    except Exception as e:
        print(f"API获取应用失败: {e}")
        import traceback
        traceback.print_exc()
        return {'apps': [], 'success': False, 'error': str(e)}

@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    global monitoring_active, monitoring_threads, performance_analyzer
    udid = data.get('udid', '')
    bundle_id = data.get('bundle_id', '')
    
    # 重置监控状态
    monitoring_active = True
    
    def start_performance_monitoring():
        global performance_analyzer
        
        # 首先检测iOS版本
        tunnel_manager = TunnelManager()
        ios_version = tunnel_manager.get_ios_version(udid)
        print(f"🔍 版本检测结果: '{ios_version}'")
        
        # 判断iOS版本：15.x和16.x使用pyidevice，17+使用pymobiledevice3
        # 注意：26.x实际上是iOS 17.x的内部版本号
        is_legacy = False
        if ios_version:
            version_parts = ios_version.split('.')
            if version_parts[0].isdigit():
                major_version = int(version_parts[0])
                # 只有15和16才是legacy
                is_legacy = major_version in [15, 16]
        
        if is_legacy:
            # iOS 15-16：使用pyidevice
            print(f"🔄 检测到iOS {ios_version}，使用pyidevice兼容模式")
            performance_analyzer = LegacyIOSPerformanceAnalyzer(udid)
            
            # 启动pyidevice监控
            monitoring_thread = threading.Thread(target=performance_analyzer.monitor_app_performance, args=(bundle_id,))
            monitoring_thread.start()
            monitoring_threads.append(monitoring_thread)
            
            return  # iOS 15-16模式不需要执行后续的iOS 17代码
            
        else:
            # iOS 17+：使用pymobiledevice3隧道模式
            print(f"🔄 检测到iOS {ios_version or '17+'}，使用pymobiledevice3隧道模式")
            tunnel_manager.get_tunnel()
            
            if tunnel_manager.tunnel_error:
                print(f"❌ 隧道创建失败: {tunnel_manager.tunnel_error}")
                socketio.emit('monitoring_error', {'error': tunnel_manager.tunnel_error})
                return
                
            performance_analyzer = WebPerformanceAnalyzer(udid, tunnel_manager.tunnel_host, tunnel_manager.tunnel_port)
            
            # 与main.py完全一致的线程启动方式（仅iOS 17+）
            proc_thread = threading.Thread(target=performance_analyzer.ios17_proc_perf, args=(bundle_id,))
            fps_thread = threading.Thread(target=performance_analyzer.ios17_fps_perf)
            
            proc_thread.start()
            time.sleep(0.1)
            fps_thread.start()
            
            # 存储线程引用
            monitoring_threads.clear()
            monitoring_threads.append(proc_thread)
            monitoring_threads.append(fps_thread)
    
    # 在后台启动性能监控
    threading.Thread(target=start_performance_monitoring).start()
    emit('monitoring_started', {'status': 'success'})


@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    global monitoring_active, monitoring_threads, performance_analyzer
    print("DEBUG: 收到停止监控请求")
    
    # 设置监控为非激活状态
    monitoring_active = False
    
    # 停止performance_analyzer的监控
    if performance_analyzer:
        try:
            # 如果analyzer有停止方法，调用它们
            if hasattr(performance_analyzer, 'stop_performance_collection'):
                performance_analyzer.stop_performance_collection()
            if hasattr(performance_analyzer, 'stop_fps_collection'):
                performance_analyzer.stop_fps_collection()
            print("DEBUG: 已调用performance_analyzer的停止方法")
        except Exception as e:
            print(f"DEBUG: 停止performance_analyzer时出错: {e}")
    
    # 等待线程结束
    for thread in monitoring_threads:
        if thread.is_alive():
            print(f"DEBUG: 等待线程 {thread} 结束")
            thread.join(timeout=2.0)
            if thread.is_alive():
                print(f"DEBUG: 线程 {thread} 仍在运行")
    
    monitoring_threads.clear()
    performance_analyzer = None
    emit('monitoring_stopped', {'status': 'success'})
    print("DEBUG: 监控已完全停止")


@socketio.on('get_devices')
def handle_get_devices():
    """获取设备列表"""
    try:
        devices = get_connected_devices()
        print(f"DEBUG: Socket.IO返回 {len(devices)} 个设备")
        emit('devices_list', devices)
    except Exception as e:
        print(f"Socket.IO获取设备失败: {e}")
        emit('devices_list', [])


@socketio.on('get_apps')
def handle_get_apps(data):
    """获取应用列表"""
    try:
        udid = data.get('udid') if data else None
        print(f"DEBUG: Socket.IO获取应用列表，UDID: {udid}")
        apps = get_installed_apps(udid, emit_progress=False)
        print(f"DEBUG: Socket.IO返回 {len(apps)} 个应用")
        emit('apps_list', {'apps': apps})
    except Exception as e:
        print(f"Socket.IO获取应用失败: {e}")
        emit('apps_list', {'apps': [], 'error': str(e)})


if __name__ == '__main__':
    # 权限检查，自动输入密码
    if not check_admin():
        print("没有管理员权限，正在以管理员权限运行...")
        run_with_admin_privileges(sys.argv)
        sys.exit()
    
    import socket
    
    # 获取本机局域网IP地址
    def is_private_ip(ip_str):
        """判断是否为私有IP地址（局域网IP）"""
        try:
            ip_parts = [int(x) for x in ip_str.split('.')]
            if len(ip_parts) != 4:
                return False
            
            # 检查私有IP地址范围
            # 10.0.0.0 - 10.255.255.255 (10/8)
            if ip_parts[0] == 10:
                return True
            
            # 172.16.0.0 - 172.31.255.255 (172.16/12)
            if ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
                return True
            
            # 192.168.0.0 - 192.168.255.255 (192.168/16)
            if ip_parts[0] == 192 and ip_parts[1] == 168:
                return True
            
            return False
        except:
            return False

    def get_local_ip():
        """获取本机局域网IP地址，优先选择172段IP"""
        found_ips = []
        
        # 方法1: 通过ifconfig命令获取所有网络接口
        try:
            import subprocess
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'inet ' in line and '127.0.0.1' not in line and '169.254' not in line:
                    # 提取IP地址
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1]
                            # 移除可能的子网掩码
                            if '/' in ip:
                                ip = ip.split('/')[0]
                            
                            # 验证是否为有效的局域网IP
                            if is_private_ip(ip) and ip.count('.') == 3:
                                found_ips.append(ip)
        except Exception:
            pass
        
        # 方法2: 通过socket连接方式获取默认路由IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # 添加到候选列表
            if is_private_ip(local_ip) and local_ip not in found_ips:
                found_ips.append(local_ip)
        except Exception:
            pass
        
        # 方法3: 通过主机名获取IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if is_private_ip(local_ip) and local_ip not in found_ips:
                found_ips.append(local_ip)
        except Exception:
            pass
        
        # 打印调试信息
        print(f"🔍 检测到的所有局域网IP: {found_ips}")
        
        # 优先级排序：172 > 10 > 192.168
        for ip in found_ips:
            if ip.startswith('172.'):
                print(f"✅ 选择172段IP: {ip}")
                return ip
        
        for ip in found_ips:
            if ip.startswith('10.'):
                print(f"✅ 选择10段IP: {ip}")
                return ip
        
        for ip in found_ips:
            if ip.startswith('192.168.'):
                print(f"✅ 选择192.168段IP: {ip}")
                return ip
        
        print("❌ 未找到局域网IP，使用localhost")
        return 'localhost'
    
    local_ip = get_local_ip()
    
    print("🚀 启动iOS性能监控Web界面...")
    print("="*60)
    print(f"📱 本地访问地址: http://localhost:5002")
    print(f"🌐 外网分享地址: http://{local_ip}:5002")
    print("="*60)
    print("💡 分享说明:")
    print("• 把外网分享地址发给同事/朋友，他们可以实时查看你的性能数据")
    print("• 确保你的设备和他们在同一个网络环境中（如同一WiFi）")
    print("• 如果无法访问，可能需要关闭防火墙或允许端口5002")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)

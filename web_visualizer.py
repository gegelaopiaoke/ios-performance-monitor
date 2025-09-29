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


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ios_performance_monitor'
socketio = SocketIO(app, 
                  cors_allowed_origins="*",
                  ping_timeout=5,          # 5秒ping超时
                  ping_interval=1,         # 1秒ping间隔
                  max_http_buffer_size=1024*1024,  # 1MB缓冲区
                  async_mode='threading')  # 使用线程模式确保实时性

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

# 测试场景管理
current_test_scenario = None
scenario_automation = None


# 完全复制main.py的TunnelManager类（逻辑一模一样）
class TunnelManager(object):
    def __init__(self):
        self.start_event = threading.Event()
        self.tunnel_host = None
        self.tunnel_port = None

    def get_tunnel(self):
        def start_tunnel():
            rp = subprocess.Popen([sys.executable, "-m", "pymobiledevice3", "remote", "start-tunnel"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            while not rp.poll():
                line = rp.stdout.readline().decode()
                line = line.strip()
                if line:
                    print(line)
                assert "ERROR Device is not connected" not in line, "ERROR Device is not connected"
                if "--rsd" in line:
                    ipv6_pattern = r'--rsd\s+(\S+)\s+'
                    port_pattern = r'\s+(\d{1,5})\b'
                    self.tunnel_host = re.search(ipv6_pattern, line).group(1)
                    print(self.tunnel_host)
                    self.tunnel_port = int(re.search(port_pattern, line).group(1))
                    print(port_pattern)
                    self.start_event.set()

        threading.Thread(target=start_tunnel).start()
        self.start_event.wait(timeout=30)


# 完全复制main.py的PerformanceAnalyzer类，但修改输出到Web（保持核心逻辑不变）
class WebPerformanceAnalyzer(object):
    def __init__(self, udid, host, port):
        self.udid = udid
        self.host = host
        self.port = port
        self.fps = None

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
                                'name': attrs.Name
                            }
                            # 立即发送数据，强制实时传输
                            socketio.emit('performance_data', data)
                            socketio.sleep(0)  # 强制flush
                            
                            # 同时保持原始的print_json输出（完全一致）
                            print_json(attrs.__dict__, format)

        with RemoteLockdownClient((self.host, self.port)) as rsd:
            with InstrumentsBase(udid=self.udid, network=False, lockdown=rsd) as rpc:
                rpc.process_attributes = ['pid', 'name', 'cpuUsage', 'physFootprint',
                                          'diskBytesRead', 'diskBytesWritten', 'threadCount']
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
            print_json({"currentTime": str(datetime.now()), "fps": data['CoreAnimationFramesPerSecond']}, format)

        with RemoteLockdownClient((self.host, self.port)) as rsd:
            with InstrumentsBase(udid=self.udid, network=False, lockdown=rsd) as rpc:
                rpc.graphics(on_callback_fps_message, 1000)


# 真正的iOS应用自动化控制类
class iOSAutomationController:
    def __init__(self, udid=None):
        self.udid = udid
        
    def connect(self):
        """连接到iOS设备"""
        try:
            # 检查设备连接状态
            result = subprocess.run([
                sys.executable, '-m', 'pymobiledevice3', 'usbmux', 'list'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # 如果没有指定UDID，尝试使用第一个设备
                if not self.udid or self.udid.strip() == '':
                    import json
                    devices = json.loads(result.stdout)
                    if devices:
                        self.udid = devices[0]['UniqueDeviceID']
                        print(f"自动检测到设备: {self.udid}")
                    else:
                        print("未找到连接的iOS设备")
                        return False
                
                # 检查指定的设备是否存在
                if self.udid in result.stdout:
                    print(f"设备 {self.udid} 连接成功")
                    return True
                else:
                    print(f"设备 {self.udid} 未找到或未连接")
                    return False
            else:
                print(f"无法获取设备列表: {result.stderr}")
                return False
        except Exception as e:
            print(f"连接设备失败: {e}")
            return False
    
    def terminate_app(self, bundle_id):
        """终止指定应用"""
        try:
            # 首先获取应用的PID
            print(f"🔍 查找应用 {bundle_id} 的进程ID...")
            result_pid = subprocess.run([
                sys.executable, '-m', 'pymobiledevice3', 'developer', 'dvt', 
                'process-id-for-bundle-id', bundle_id
            ], capture_output=True, text=True, timeout=10)
            
            if result_pid.returncode == 0 and result_pid.stdout.strip():
                pid = result_pid.stdout.strip()
                print(f"📍 找到应用PID: {pid}")
                
                # 使用PID终止应用
                result_kill = subprocess.run([
                    sys.executable, '-m', 'pymobiledevice3', 'developer', 'dvt', 'kill', pid
                ], capture_output=True, text=True, timeout=10)
                
                if result_kill.returncode == 0:
                    print(f"✅ 应用 {bundle_id} (PID: {pid}) 已终止")
                else:
                    print(f"⚠️ 终止应用失败: {result_kill.stderr}")
            else:
                print(f"ℹ️ 应用 {bundle_id} 未运行或无法找到进程")
            
        except Exception as e:
            print(f"❌ 终止应用时出错: {e}")
    
    def launch_app_real_device(self, bundle_id):
        """在真实设备上启动应用"""
        try:
            print(f"🚀 正在启动应用: {bundle_id}")
            
            # 方法1: 尝试使用tidevice（如果可用）
            print("🔧 尝试使用tidevice启动...")
            result_tidevice = subprocess.run([
                'tidevice', 'launch', bundle_id
            ], capture_output=True, text=True, timeout=15)
            
            print(f"tidevice返回码: {result_tidevice.returncode}")
            if result_tidevice.stdout:
                print(f"tidevice输出: {result_tidevice.stdout}")
            if result_tidevice.stderr and "error" not in result_tidevice.stderr.lower():
                print(f"tidevice信息: {result_tidevice.stderr}")
            
            if result_tidevice.returncode == 0:
                print(f"✅ 应用 {bundle_id} 通过tidevice启动成功！")
                return True
            
            # 方法2: 使用pymobiledevice3 (tunnel方式)
            print("📱 尝试pymobiledevice3 tunnel方式...")
            result = subprocess.run([
                sys.executable, '-m', 'pymobiledevice3', 'developer', 'dvt', 'launch',
                '--tunnel', self.udid,
                '--kill-existing',
                bundle_id
            ], capture_output=True, text=True, timeout=20)
            
            print(f"tunnel方法返回码: {result.returncode}")
            
            # 检查是否真的启动了（通过查看进程）
            if result.returncode == 0:
                time.sleep(2)  # 等待应用启动
                # 验证应用是否真的在运行
                if self.verify_app_running(bundle_id):
                    print(f"✅ 应用 {bundle_id} 确实启动成功！")
                    return True
                else:
                    print(f"⚠️ 命令成功但应用未运行，可能是假成功")
            
            # 方法3: 简单粗暴的方法 - 模拟用户点击
            print("📲 尝试模拟用户操作启动应用...")
            print("💡 提示: 请手动在手机上点击ReelShort应用启动")
            print("⏰ 等待5秒供您手动启动...")
            time.sleep(5)
            
            if self.verify_app_running(bundle_id):
                print(f"✅ 检测到应用 {bundle_id} 已运行！")
                return True
            
            print(f"❌ 所有自动启动方法都失败了")
            return False
            
        except subprocess.TimeoutExpired:
            print("⏰ 应用启动命令超时")
            return False
        except Exception as e:
            print(f"❌ 启动应用时出错: {e}")
            return False
    
    def verify_app_running(self, bundle_id):
        """验证应用是否真的在运行"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pymobiledevice3', 'developer', 'dvt', 
                'process-id-for-bundle-id', bundle_id
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"🔍 发现应用进程: PID {result.stdout.strip()}")
                return True
            return False
        except:
            return False


# 测试场景自动化类
class TestScenarioAutomation:
    def __init__(self, udid, bundle_id):
        self.udid = udid
        self.bundle_id = bundle_id
        self.controller = iOSAutomationController(udid)
        self.is_running = False
        
    def run_app_launch_test(self):
        """运行真正的应用启动测试"""
        self.is_running = True
        
        try:
            # 发送测试开始信号
            socketio.emit('scenario_event', {
                'type': 'test_start',
                'message': '开始应用启动测试...'
            })
            
            # 连接设备
            if not self.controller.connect():
                socketio.emit('scenario_event', {
                    'type': 'error',
                    'message': '无法连接到iOS设备'
                })
                return False
            
            # 执行3次启动测试
            for i in range(3):
                if not self.is_running:
                    break
                    
                socketio.emit('scenario_event', {
                    'type': 'progress',
                    'message': f'第{i+1}次启动测试...',
                    'progress': (i / 3) * 100
                })
                
                # 先终止应用
                self.controller.terminate_app(self.bundle_id)
                time.sleep(2)
                
                # 记录启动开始时间
                start_time = time.time()
                
                # 尝试启动应用
                success = self.controller.launch_app_real_device(self.bundle_id)
                
                # 如果自动启动失败，给用户手动启动的机会
                if not success:
                    socketio.emit('scenario_event', {
                        'type': 'manual_prompt',
                        'message': f'自动启动失败，请手动在手机上点击ReelShort应用启动'
                    })
                    
                    # 等待用户手动启动，最多等待10秒
                    manual_start_time = time.time()
                    for wait_sec in range(10):
                        if self.controller.verify_app_running(self.bundle_id):
                            success = True
                            break
                        time.sleep(1)
                    
                    if success:
                        socketio.emit('scenario_event', {
                            'type': 'manual_success',
                            'message': '检测到应用已手动启动'
                        })
                
                if success:
                    launch_time = (time.time() - start_time) * 1000  # 转换为毫秒
                    socketio.emit('scenario_event', {
                        'type': 'launch_result',
                        'message': f'第{i+1}次启动成功，耗时: {launch_time:.0f}ms',
                        'launch_time': launch_time
                    })
                else:
                    socketio.emit('scenario_event', {
                        'type': 'error',
                        'message': f'第{i+1}次启动失败（包括手动启动）'
                    })
                
                # 等待应用稳定
                time.sleep(3)
            
            socketio.emit('scenario_event', {
                'type': 'test_complete',
                'message': '应用启动测试完成'
            })
            
            return True
            
        except Exception as e:
            socketio.emit('scenario_event', {
                'type': 'error',
                'message': f'测试过程中出错: {str(e)}'
            })
            return False
        finally:
            self.is_running = False
    
    def stop(self):
        """停止测试"""
        self.is_running = False


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
                    except json.JSONDecodeError:
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
                        
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON解析失败: {e}")
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
        # 完全复制main.py的主要逻辑
        tunnel_manager = TunnelManager()
        tunnel_manager.get_tunnel()
        performance_analyzer = WebPerformanceAnalyzer(udid, tunnel_manager.tunnel_host, tunnel_manager.tunnel_port)
        
        # 与main.py完全一致的线程启动方式
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


@socketio.on('start_test_scenario')
def handle_start_test_scenario(data):
    global current_test_scenario, scenario_automation, monitoring_active
    
    scenario_type = data.get('scenario_type', '')
    udid = data.get('udid', '')
    bundle_id = data.get('bundle_id', '')
    
    print(f"DEBUG: 收到测试场景请求 - 类型: {scenario_type}, 应用: {bundle_id}")
    
    # 检查是否正在监控中
    if not monitoring_active:
        emit('scenario_error', {'message': '请先开始性能监控，然后再进行测试场景'})
        return
    
    if current_test_scenario:
        emit('scenario_error', {'message': '已有测试场景在运行中'})
        return
    
    if scenario_type == 'app_launch':
        # 创建应用启动测试自动化
        scenario_automation = TestScenarioAutomation(udid, bundle_id)
        current_test_scenario = scenario_type
        
        # 在后台运行测试，同时继续性能监控
        def run_test():
            global current_test_scenario, scenario_automation
            try:
                # 发送测试开始标记到性能数据流
                socketio.emit('test_marker', {
                    'type': 'test_start',
                    'scenario': 'app_launch',
                    'message': '开始应用启动测试'
                })
                
                scenario_automation.run_app_launch_test()
                
                # 发送测试结束标记
                socketio.emit('test_marker', {
                    'type': 'test_end',
                    'scenario': 'app_launch',
                    'message': '应用启动测试完成'
                })
            finally:
                current_test_scenario = None
                scenario_automation = None
        
        threading.Thread(target=run_test).start()
        emit('scenario_started', {'status': 'success', 'type': scenario_type})
    
    else:
        # 其他测试场景保持原有的计时器模式
        current_test_scenario = scenario_type
        emit('scenario_started', {'status': 'success', 'type': scenario_type})


@socketio.on('stop_test_scenario')
def handle_stop_test_scenario():
    global current_test_scenario, scenario_automation
    
    print("DEBUG: 收到停止测试场景请求")
    
    if scenario_automation:
        scenario_automation.stop()
    
    current_test_scenario = None
    scenario_automation = None
    
    emit('scenario_stopped', {'status': 'success'})


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
    print(f"📱 本地访问地址: http://localhost:5001")
    print(f"🌐 外网分享地址: http://{local_ip}:5001")
    print("="*60)
    print("💡 分享说明:")
    print("• 把外网分享地址发给同事/朋友，他们可以实时查看你的性能数据")
    print("• 确保你的设备和他们在同一个网络环境中（如同一WiFi）")
    print("• 如果无法访问，可能需要关闭防火墙或允许端口5001")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)

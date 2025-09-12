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
from ios_device.util.utils import convertBytes
from ios_device.remote.remote_lockdown import RemoteLockdownClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ios_performance_monitor'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储性能数据
performance_data = {
    'cpu_data': [],
    'memory_data': [],
    'fps_data': [],
    'disk_reads_data': [],
    'disk_writes_data': [],
    'threads_data': []
}

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

        def on_callback_proc_message(res):
            if isinstance(res.selector, list):
                for index, row in enumerate(res.selector):
                    if 'Processes' in row:
                        for _pid, process in row['Processes'].items():
                            attrs = process_attributes(*process)
                            if name and attrs.Name != name:
                                continue
                            if not attrs.CPU:
                                attrs.CPU = 0
                            cpu_value = round(attrs.CPU, 2)
                            attrs.CPU = f'{round(attrs.CPU, 2)} %'
                            memory_bytes = attrs.Memory
                            attrs.Memory = convertBytes(attrs.Memory)
                            attrs.DiskReads = convertBytes(attrs.DiskReads)
                            attrs.DiskWrites = convertBytes(attrs.DiskWrites)
                            attrs.FPS = self.fps
                            attrs.Time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            # 发送数据到Web界面
                            # current_time = datetime.now().strftime('%H:%M:%S')
                            data = {
                                'time': attrs.Time,
                                'cpu': cpu_value,
                                'memory': memory_bytes / (1024 * 1024),  # 转换为MB
                                'threads': attrs.Threads,
                                'fps': attrs.FPS,
                                'pid': attrs.Pid,
                                'name': attrs.Name
                            }
                            socketio.emit('performance_data', data)

                            # 同时保持原始的print_json输出（完全一致）
                            print(json.dumps(attrs.__dict__))

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

        def on_callback_fps_message(res):
            data = res.selector
            self.fps = data['CoreAnimationFramesPerSecond']
            # fps_value = data['CoreAnimationFramesPerSecond']
            # current_time = datetime.now()
            
            # # 发送数据到Web界面
            # fps_data = {
            #     'time': current_time.strftime('%H:%M:%S'),
            #     'fps': fps_value
            # }
            # socketio.emit('fps_data', fps_data)
            
            # 同时保持原始的print_json输出（完全一致）
            # print(json.dumps({"currentTime": str(current_time), "fps": fps_value}))

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


# Web路由
@app.route('/')
def index():
    return render_template('index2.html')

@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    udid = data.get('udid', '')
    bundle_id = data.get('bundle_id', '')
    
    def start_performance_monitoring():
        # 完全复制main.py的主要逻辑
        tunnel_manager = TunnelManager()
        tunnel_manager.get_tunnel()
        performance_analyzer = WebPerformanceAnalyzer(udid, tunnel_manager.tunnel_host, tunnel_manager.tunnel_port)
        
        # 与main.py完全一致的线程启动方式
        threading.Thread(target=performance_analyzer.ios17_proc_perf, args=(bundle_id,)).start()
        time.sleep(0.1)
        threading.Thread(target=performance_analyzer.ios17_fps_perf).start()
    
    # 在后台启动性能监控
    threading.Thread(target=start_performance_monitoring).start()
    emit('monitoring_started', {'status': 'success'})


if __name__ == '__main__':
    # 权限检查，自动输入密码
    if not check_admin():
        print("没有管理员权限，正在以管理员权限运行...")
        run_with_admin_privileges(sys.argv)
        sys.exit()
    
    print("启动iOS性能监控Web界面...")
    print("访问地址: http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

// Android性能监控JavaScript
// Socket.IO连接
const socket = io();

// 全局变量
let isMonitoring = false;
let cpuChart, memoryChart, fpsChart, threadsChart, diskReadsChart, diskWritesChart;
let allTimeLabels = []; // 存储所有时间标签
let allCpuData = []; // 存储所有CPU数据
let allMemoryData = []; // 存储所有内存数据
let allFpsData = []; // 存储所有FPS数据
let allThreadsData = []; // 存储所有线程数据
let allDiskReadsData = []; // 存储所有磁盘读取数据
let allDiskWritesData = []; // 存储所有磁盘写入数据
let allApps = []; // 存储完整应用列表用于搜索

// 性能统计数据
let performanceStats = {
    cpu: { current: 0, avg: 0, max: 0, sum: 0, count: 0 },
    memory: { current: 0, avg: 0, max: 0, sum: 0, count: 0 },
    fps: { current: 0, avg: 0, min: Infinity, sum: 0, count: 0 },
    threads: { current: 0, avg: 0, max: 0, sum: 0, count: 0 },
    disk_reads: { current: 0, avg: 0, max: 0, sum: 0, count: 0 },
    disk_writes: { current: 0, avg: 0, max: 0, sum: 0, count: 0 }
};

// 拖拽功能
function initDragAndDrop() {
    const container = document.querySelector('.container');
    if (!container) {
        console.warn('容器元素未找到，跳过拖拽初始化');
        return;
    }
    
    const panels = document.querySelectorAll('.controls, .chart-container, .statistics-panel, .thread-distribution');
    if (!panels || panels.length === 0) {
        console.warn('面板元素未找到，跳过拖拽初始化');
        return;
    }
    
    panels.forEach(panel => {
        // 🔒 关键修改1：禁止统计面板被拖拽，保证它固定在图表上方
        if (panel.id === 'statisticsPanel') {
            panel.setAttribute('draggable', 'false');
            panel.style.cursor = 'default';
            return; // 跳过统计面板，不添加拖拽事件
        }
        
        panel.addEventListener('dragstart', handleDragStart);
        panel.addEventListener('dragend', handleDragEnd);
    });
    
    container.addEventListener('dragover', handleDragOver);
    container.addEventListener('drop', handleDrop);
}

function handleDragStart(e) {
    e.dataTransfer.setData('text/plain', e.target.id);
    e.target.classList.add('dragging');
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
}

function handleDrop(e) {
    e.preventDefault();
    const draggedId = e.dataTransfer.getData('text/plain');
    const draggedElement = document.getElementById(draggedId);
    const afterElement = getDragAfterElement(e.target.closest('.container'), e.clientY);
    
    if (afterElement == null) {
        e.target.closest('.container').appendChild(draggedElement);
    } else {
        e.target.closest('.container').insertBefore(draggedElement, afterElement);
    }
    
    savePanelOrder();
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.controls:not(.dragging), .chart-container:not(.dragging), .statistics-panel:not(.dragging), .thread-distribution:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function savePanelOrder() {
    const panels = document.querySelectorAll('.controls, .chart-container, .statistics-panel, .thread-distribution');
    const order = [];
    
    panels.forEach(panel => {
        // 🔒 关键修改2：排除统计面板，不保存它的位置
        if (panel.id && panel.id !== 'statisticsPanel') {
            order.push(panel.id);
        }
    });
    
    localStorage.setItem('androidPanelOrder', JSON.stringify(order));
    console.log('已保存面板顺序（排除统计面板）:', order);
}

function restorePanelOrder() {
    const savedOrder = localStorage.getItem('androidPanelOrder');
    if (!savedOrder) return;
    
    try {
        const order = JSON.parse(savedOrder);
        const container = document.querySelector('.container');
        
        if (!container) {
            console.warn('容器元素未找到，无法恢复面板顺序');
            return;
        }
        
        // 找到所有面板（排除统计面板）
        const panels = {};
        document.querySelectorAll('.controls, .chart-container, .statistics-panel, .thread-distribution').forEach(panel => {
            if (panel.id && panel.id !== 'statisticsPanel') {
                // 🔒 关键修改3：排除统计面板，保证它不被移动
                panels[panel.id] = panel;
            }
        });
        
        // 按保存的顺序重新排列（不包括统计面板）
        order.forEach(id => {
            if (panels[id]) {
                container.appendChild(panels[id]);
            }
        });
        
        console.log('已恢复面板顺序（统计面板保持固定位置）');
    } catch (error) {
        console.log('恢复面板顺序失败:', error);
    }
}

// 图表配置
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false
        }
    },
    scales: {
        x: {
            display: true,
            title: {
                display: true,
                text: '时间'
            }
        },
        y: {
            display: true,
            beginAtZero: true
        }
    },
    elements: {
        line: {
            tension: 0.4
        },
        point: {
            radius: 3
        }
    }
};

// 初始化图表
function initCharts() {
    const cpuCtx = document.getElementById('cpuChart').getContext('2d');
    cpuChart = new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU使用率 (%)',
                data: [],
                borderColor: '#ff3b30',
                backgroundColor: 'rgba(255, 59, 48, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: 'CPU使用率 (%)'
                    }
                }
            }
        }
    });

    const memoryCtx = document.getElementById('memoryChart').getContext('2d');
    memoryChart = new Chart(memoryCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '内存使用 (MB)',
                data: [],
                borderColor: '#007aff',
                backgroundColor: 'rgba(0, 122, 255, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: '内存使用 (MB)'
                    }
                }
            }
        }
    });

    const fpsCtx = document.getElementById('fpsChart').getContext('2d');
    fpsChart = new Chart(fpsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'FPS',
                data: [],
                borderColor: '#34c759',
                backgroundColor: 'rgba(52, 199, 89, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    min: 0,
                    max: 60,
                    title: {
                        display: true,
                        text: 'FPS'
                    }
                }
            }
        }
    });

    const threadsCtx = document.getElementById('threadsChart').getContext('2d');
    threadsChart = new Chart(threadsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '线程数',
                data: [],
                borderColor: '#ff9500',
                backgroundColor: 'rgba(255, 149, 0, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: '线程数'
                    }
                }
            }
        }
    });

    const diskReadsCtx = document.getElementById('diskReadsChart').getContext('2d');
    diskReadsChart = new Chart(diskReadsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '磁盘读取 (MB)',
                data: [],
                borderColor: '#af52de',
                backgroundColor: 'rgba(175, 82, 222, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: '磁盘读取 (MB)'
                    }
                }
            }
        }
    });

    const diskWritesCtx = document.getElementById('diskWritesChart').getContext('2d');
    diskWritesChart = new Chart(diskWritesCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '磁盘写入 (MB)',
                data: [],
                borderColor: '#ff2d92',
                backgroundColor: 'rgba(255, 45, 146, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: '磁盘写入 (MB)'
                    }
                }
            }
        }
    });
}

// 显示状态消息
function showStatus(message, type) {
    const statusElement = document.getElementById('status');
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
    statusElement.classList.remove('hidden');
    
    setTimeout(() => {
        statusElement.classList.add('hidden');
    }, 5000);
}

// 添加数据到图表
function addDataToChart(chart, label, data) {
    // 确保数据是数字类型
    const numericData = typeof data === 'number' ? data : parseFloat(data) || 0;
    
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(numericData);
    
    // 保持图表数据量在合理范围
    if (chart.data.labels.length > 50) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.update('none');
}

// 开始监控
function startMonitoring() {
    const deviceId = document.getElementById('deviceSelect').value;
    const packageName = document.getElementById('packageSelect').value;
    
    if (!deviceId) {
        showStatus('请先选择设备', 'error');
        return;
    }
    
    if (!packageName) {
        showStatus('请先选择应用', 'error');
        return;
    }
    
    socket.emit('start_monitoring', {
        device_id: deviceId,
        package_name: packageName
    });
}

// 停止监控
function stopMonitoring() {
    socket.emit('stop_monitoring');
}

// 刷新设备列表
function refreshDevices() {
    showStatus('正在刷新设备列表...', 'info');
    socket.emit('get_devices');
}

// 设备选择变更时自动获取应用列表
function onDeviceChanged() {
    const deviceId = document.getElementById('deviceSelect').value;
    if (deviceId) {
        // 自动获取应用列表
        refreshApps();
    } else {
        // 清空应用列表
        const packageSelect = document.getElementById('packageSelect');
        packageSelect.innerHTML = '<option value="">请先选择设备</option>';
        allApps = []; // 清空应用列表
    }
}

// 刷新应用列表
function refreshApps() {
    const deviceId = document.getElementById('deviceSelect').value;
    if (!deviceId) {
        showStatus('请先选择设备', 'error');
        return;
    }
    
    showStatus('正在获取应用列表...', 'info');
    socket.emit('get_apps', { device_id: deviceId });
}

// 搜索应用功能
function filterApps() {
    const searchInput = document.getElementById('appSearch');
    const packageSelect = document.getElementById('packageSelect');
    
    if (!searchInput || !packageSelect) return;
    
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    // 清空当前选项
    packageSelect.innerHTML = '';
    
    // 如果搜索条件为空，显示所有应用
    const filteredApps = searchTerm === '' 
        ? allApps 
        : allApps.filter(app => {
            const appName = (app.app_name || '').toLowerCase();
            const packageName = (app.package_name || '').toLowerCase();
            return appName.includes(searchTerm) || packageName.includes(searchTerm);
        });
    
    // 显示过滤后的应用
    if (filteredApps.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = searchTerm === '' ? '请先选择设备' : '未找到匹配的应用';
        packageSelect.appendChild(option);
    } else {
        filteredApps.forEach(app => {
            const option = document.createElement('option');
            option.value = app.package_name;
            option.textContent = `${app.app_name} (${app.package_name})`;
            packageSelect.appendChild(option);
        });
    }
}

// 更新性能统计
function updatePerformanceStats(cpu, memory, fps, threads, diskReads, diskWrites) {
    // 更新CPU统计
    performanceStats.cpu.current = cpu;
    performanceStats.cpu.sum += cpu;
    performanceStats.cpu.count++;
    performanceStats.cpu.avg = performanceStats.cpu.sum / performanceStats.cpu.count;
    performanceStats.cpu.max = Math.max(performanceStats.cpu.max, cpu);
    
    // 更新内存统计
    performanceStats.memory.current = memory;
    performanceStats.memory.sum += memory;
    performanceStats.memory.count++;
    performanceStats.memory.avg = performanceStats.memory.sum / performanceStats.memory.count;
    performanceStats.memory.max = Math.max(performanceStats.memory.max, memory);
    
    // 更新FPS统计
    if (fps > 0) {
        performanceStats.fps.current = fps;
        performanceStats.fps.sum += fps;
        performanceStats.fps.count++;
        performanceStats.fps.avg = performanceStats.fps.sum / performanceStats.fps.count;
        performanceStats.fps.min = Math.min(performanceStats.fps.min, fps);
    }
    
    // 更新线程统计
    performanceStats.threads.current = threads;
    performanceStats.threads.sum += threads;
    performanceStats.threads.count++;
    performanceStats.threads.avg = performanceStats.threads.sum / performanceStats.threads.count;
    performanceStats.threads.max = Math.max(performanceStats.threads.max, threads);
    
    // 更新磁盘读写统计
    if (typeof diskReads === 'number') {
        performanceStats.disk_reads.current = diskReads;
        performanceStats.disk_reads.sum += diskReads;
        performanceStats.disk_reads.count++;
        performanceStats.disk_reads.avg = performanceStats.disk_reads.sum / performanceStats.disk_reads.count;
        performanceStats.disk_reads.max = Math.max(performanceStats.disk_reads.max, diskReads);
    }
    
    if (typeof diskWrites === 'number') {
        performanceStats.disk_writes.current = diskWrites;
        performanceStats.disk_writes.sum += diskWrites;
        performanceStats.disk_writes.count++;
        performanceStats.disk_writes.avg = performanceStats.disk_writes.sum / performanceStats.disk_writes.count;
        performanceStats.disk_writes.max = Math.max(performanceStats.disk_writes.max, diskWrites);
    }
    
    updateStatisticsDisplay();
}

// 更新统计显示
function updateStatisticsDisplay() {
    document.getElementById('statCpuCurrent').textContent = `${performanceStats.cpu.current.toFixed(1)}%`;
    document.getElementById('statCpuAvg').textContent = `${performanceStats.cpu.avg.toFixed(1)}%`;
    document.getElementById('statCpuMax').textContent = `${performanceStats.cpu.max.toFixed(1)}%`;
    
    document.getElementById('statMemoryCurrent').textContent = `${performanceStats.memory.current.toFixed(1)}MB`;
    document.getElementById('statMemoryAvg').textContent = `${performanceStats.memory.avg.toFixed(1)}MB`;
    document.getElementById('statMemoryMax').textContent = `${performanceStats.memory.max.toFixed(1)}MB`;
    
    if (performanceStats.fps.count > 0) {
        document.getElementById('statFpsCurrent').textContent = `${performanceStats.fps.current}FPS`;
        document.getElementById('statFpsAvg').textContent = `${performanceStats.fps.avg.toFixed(1)}FPS`;
        document.getElementById('statFpsMin').textContent = `${performanceStats.fps.min === Infinity ? 0 : performanceStats.fps.min}FPS`;
    }
    
    document.getElementById('statThreadsCurrent').textContent = performanceStats.threads.current;
    document.getElementById('statThreadsAvg').textContent = performanceStats.threads.avg.toFixed(1);
    document.getElementById('statThreadsMax').textContent = performanceStats.threads.max;
    
    // 更新磁盘读取统计显示
    if (performanceStats.disk_reads.count > 0) {
        document.getElementById('statDiskReadsCurrent').textContent = `${performanceStats.disk_reads.current.toFixed(2)}MB`;
        document.getElementById('statDiskReadsAvg').textContent = `${performanceStats.disk_reads.avg.toFixed(2)}MB`;
        document.getElementById('statDiskReadsMax').textContent = `${performanceStats.disk_reads.max.toFixed(2)}MB`;
    }
    
    // 更新磁盘写入统计显示
    if (performanceStats.disk_writes.count > 0) {
        document.getElementById('statDiskWritesCurrent').textContent = `${performanceStats.disk_writes.current.toFixed(2)}MB`;
        document.getElementById('statDiskWritesAvg').textContent = `${performanceStats.disk_writes.avg.toFixed(2)}MB`;
        document.getElementById('statDiskWritesMax').textContent = `${performanceStats.disk_writes.max.toFixed(2)}MB`;
    }
}

// Socket.IO事件监听器
socket.on('devices_list', function(data) {
    const deviceSelect = document.getElementById('deviceSelect');
    deviceSelect.innerHTML = '<option value="">请选择设备</option>';
    
    // 检查是否有错误
    if (data.error) {
        showStatus(data.error, 'error');
        return;
    }
    
    // 确保devices是数组
    const devices = data.devices || [];
    
    devices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.id;
        option.textContent = `${device.name} (${device.brand} - Android ${device.version})`;
        deviceSelect.appendChild(option);
    });
    
    if (devices.length > 0) {
        showStatus(`发现 ${devices.length} 个Android设备`, 'success');
    } else {
        showStatus('未发现Android设备，请检查设备连接和ADB状态', 'error');
    }
});

socket.on('apps_list', function(data) {
    const packageSelect = document.getElementById('packageSelect');
    const appSearch = document.getElementById('appSearch');
    
    // 检查是否有错误
    if (data.error) {
        showStatus(data.error, 'error');
        packageSelect.innerHTML = '<option value="">获取应用列表失败</option>';
        allApps = [];
        return;
    }
    
    // 确保 apps是数组
    const apps = data.apps || [];
    
    // 保存完整应用列表用于搜索
    allApps = apps;
    
    // 清空搜索框
    if (appSearch) {
        appSearch.value = '';
    }
    
    // 显示所有应用
    packageSelect.innerHTML = '';
    
    if (apps.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '未发现应用';
        packageSelect.appendChild(option);
        showStatus('未发现应用，请检查设备状态', 'error');
    } else {
        apps.forEach(app => {
            const option = document.createElement('option');
            option.value = app.package_name;
            // 🔒 显示格式：应用名称(包名)
            option.textContent = `${app.app_name} (${app.package_name})`;
            packageSelect.appendChild(option);
        });
        showStatus(`发现 ${apps.length} 个应用，可使用搜索框过滤`, 'success');
    }
});

socket.on('status', function(data) {
    showStatus(data.message, data.type);
    
    if (data.type === 'success' && data.message.includes('开始监控')) {
        isMonitoring = true;
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
    } else if (data.type === 'info' && data.message.includes('已停止')) {
        isMonitoring = false;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
    }
});

socket.on('performance_data', function(data) {
    if (!isMonitoring) return;
    
    // 计算CPU占用信息
    const cpuCores = data.cpu_cores || 8; // CPU核心数
    const appCpuRaw = data.cpu; // 应用CPU（相对单核，可能超过100%）
    const systemCpu = data.system_cpu; // 整机CPU使用率
    
    // 计算应用占整机的百分比：appCpuRaw / cpuCores
    const appCpuPercent = (appCpuRaw / cpuCores).toFixed(1);
    
    // 立即更新当前值显示
    document.getElementById('currentCpu').textContent = `${appCpuRaw.toFixed(1)}%`;
    document.getElementById('cpuPercentOfTotal').textContent = `${appCpuPercent}%`;
    document.getElementById('cpuCores').textContent = `${cpuCores}核`;
    document.getElementById('currentSystemCpu').textContent = `${systemCpu.toFixed(1)}%`;
    document.getElementById('cpuCoreInfo').textContent = `${cpuCores}核心`;
    document.getElementById('currentMemory').textContent = `${data.memory.toFixed(1)}MB`;
    document.getElementById('systemMemInfo').textContent = `系统: ${data.system_memory_used.toFixed(0)}/${data.system_memory_total.toFixed(0)}MB`;
    document.getElementById('currentThreads').textContent = data.threads;
    document.getElementById('currentFps').textContent = `${data.fps}FPS`;
    
    // 更新磁盘读写当前值显示
    if (data.disk_reads !== undefined && typeof data.disk_reads === 'number') {
        document.getElementById('currentDiskReads').textContent = `${data.disk_reads.toFixed(1)}MB`;
    }
    if (data.disk_writes !== undefined && typeof data.disk_writes === 'number') {
        document.getElementById('currentDiskWrites').textContent = `${data.disk_writes.toFixed(1)}MB`;
    }
    
    // 添加数据到图表
    addDataToChart(cpuChart, data.time, data.cpu);
    addDataToChart(memoryChart, data.time, data.memory);
    addDataToChart(threadsChart, data.time, data.threads);
    addDataToChart(fpsChart, data.time, data.fps);
    
    // 添加磁盘读写数据到图表
    if (data.disk_reads !== undefined && typeof data.disk_reads === 'number') {
        addDataToChart(diskReadsChart, data.time, data.disk_reads);
    }
    if (data.disk_writes !== undefined && typeof data.disk_writes === 'number') {
        addDataToChart(diskWritesChart, data.time, data.disk_writes);
    }
    
    // 更新统计数据
    if (!window.statsUpdatePending) {
        window.statsUpdatePending = true;
        setTimeout(() => {
            const diskReads = (typeof data.disk_reads === 'number') ? data.disk_reads : 0;
            const diskWrites = (typeof data.disk_writes === 'number') ? data.disk_writes : 0;
            updatePerformanceStats(data.cpu, data.memory, data.fps || 0, data.threads, diskReads, diskWrites);
            window.statsUpdatePending = false;
        }, 500);
    }
});

socket.on('connect', function() {
    console.log('已连接到服务器');
});

socket.on('disconnect', function() {
    console.log('与服务器断开连接');
    if (isMonitoring) {
        showStatus('与服务器连接断开', 'error');
    }
});

// 处理线程详情数据
socket.on('thread_details', function(data) {
    if (!isMonitoring) return;
    
    const threads = data.threads || [];
    updateThreadDistribution(threads);
});

// 更新线程分布显示
function updateThreadDistribution(threads) {
    // 统计线程状态
    const stats = {
        total: threads.length,
        running: 0,
        sleeping: 0,
        other: 0
    };
    
    // 按类型统计线程数量
    const typeStats = {};
    
    threads.forEach(thread => {
        // 统计状态
        switch (thread.state) {
            case 'R':
                stats.running++;
                break;
            case 'S':
                stats.sleeping++;
                break;
            default:
                stats.other++;
                break;
        }
        
        // 统计类型
        if (typeStats[thread.type]) {
            typeStats[thread.type]++;
        } else {
            typeStats[thread.type] = 1;
        }
    });
    
    // 更新状态统计显示
    document.getElementById('totalThreads').textContent = stats.total;
    document.getElementById('runningThreads').textContent = stats.running;
    document.getElementById('sleepingThreads').textContent = stats.sleeping;
    document.getElementById('otherThreads').textContent = stats.other;
    
    // 显示线程类型统计（可点击展开）
    createThreadTypeStats(typeStats, stats.total, threads);
    
    // 更新线程列表（默认显示所有线程）
    updateThreadList(threads);
}

// 创建线程类型统计
function createThreadTypeStats(typeStats, totalCount, allThreads) {
    const threadStatsContainer = document.querySelector('.thread-summary');
    
    // 获取或创建线程类型统计容器
    let typeStatsContainer = document.getElementById('threadTypeStats');
    if (!typeStatsContainer) {
        typeStatsContainer = document.createElement('div');
        typeStatsContainer.id = 'threadTypeStats';
        typeStatsContainer.style.cssText = `
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e5e5e7;
        `;
        
        const title = document.createElement('h4');
        title.textContent = '📊 线程类型统计 (点击展开)';
        title.style.cssText = `
            margin: 0 0 15px 0;
            font-size: 14px;
            color: #1d1d1f;
            font-weight: 600;
        `;
        typeStatsContainer.appendChild(title);
        
        // 插入到状态统计之后
        threadStatsContainer.insertAdjacentElement('afterend', typeStatsContainer);
    }
    
    // 清除之前的统计内容（保留标题）
    const existingStats = typeStatsContainer.querySelectorAll('.type-stat-item');
    existingStats.forEach(item => item.remove());
    
    // 按数量排序线程类型
    const sortedTypes = Object.entries(typeStats).sort((a, b) => b[1] - a[1]);
    
    // 创建类型统计网格
    const statsGrid = document.createElement('div');
    statsGrid.style.cssText = `
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 10px;
    `;
    
    sortedTypes.forEach(([type, count]) => {
        const percentage = ((count / totalCount) * 100).toFixed(1);
        
        const typeCard = document.createElement('div');
        typeCard.className = 'type-stat-item';
        typeCard.style.cssText = `
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            background: white;
            border: 1px solid #e5e5e7;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        `;
        
        typeCard.innerHTML = `
            <div style="font-size: 11px; color: #86868b; margin-bottom: 4px;">${type}</div>
            <div style="font-size: 16px; font-weight: 600; color: #007aff;">${count}个</div>
            <div style="font-size: 10px; color: #86868b;">(${percentage}%)</div>
        `;
        
        // 添加悬停效果
        typeCard.addEventListener('mouseenter', () => {
            typeCard.style.transform = 'translateY(-2px)';
            typeCard.style.boxShadow = '0 4px 12px rgba(0, 122, 255, 0.15)';
            typeCard.style.borderColor = '#007aff';
        });
        
        typeCard.addEventListener('mouseleave', () => {
            typeCard.style.transform = 'translateY(0)';
            typeCard.style.boxShadow = 'none';
            typeCard.style.borderColor = '#e5e5e7';
        });
        
        // 添加点击事件 - 过滤显示该类型的线程
        typeCard.addEventListener('click', () => {
            filterThreadsByType(allThreads, type, typeCard);
        });
        
        statsGrid.appendChild(typeCard);
    });
    
    typeStatsContainer.appendChild(statsGrid);
}

// 按类型过滤线程并高亮显示
function filterThreadsByType(allThreads, selectedType, clickedCard) {
    // 重置所有卡片样式
    document.querySelectorAll('.type-stat-item').forEach(card => {
        card.style.backgroundColor = 'white';
        card.style.color = '';
    });
    
    // 检查是否已经选中了这个类型（切换显示）
    const isCurrentlySelected = clickedCard.style.backgroundColor === 'rgb(0, 122, 255)';
    
    if (isCurrentlySelected) {
        // 如果已选中，则显示所有线程
        updateThreadList(allThreads);
        updateThreadListTitle('所有线程');
    } else {
        // 高亮选中的卡片
        clickedCard.style.backgroundColor = '#007aff';
        clickedCard.style.color = 'white';
        
        // 过滤显示选中类型的线程
        const filteredThreads = allThreads.filter(thread => thread.type === selectedType);
        updateThreadList(filteredThreads);
        updateThreadListTitle(`${selectedType} 类型线程 (${filteredThreads.length}个)`);
    }
}

// 更新线程列表标题
function updateThreadListTitle(title) {
    let titleElement = document.getElementById('threadListTitle');
    if (!titleElement) {
        titleElement = document.createElement('h4');
        titleElement.id = 'threadListTitle';
        titleElement.style.cssText = `
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #1d1d1f;
            font-weight: 600;
            padding: 0 15px;
        `;
        
        const threadList = document.querySelector('.thread-list');
        threadList.insertBefore(titleElement, threadList.firstChild);
    }
    titleElement.textContent = title;
}

// 更新线程列表显示
function updateThreadList(threads) {
    const threadListContent = document.getElementById('threadListContent');
    
    if (threads.length === 0) {
        threadListContent.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #86868b; font-style: italic;">
                暂无线程数据...
            </div>
        `;
        return;
    }
    
    // 按状态和类型对线程进行排序
    const sortedThreads = threads.sort((a, b) => {
        // 1. 首先按状态排序：R(运行中) > S(睡眠中) > 其他
        const stateOrder = { 'R': 0, 'S': 1 };
        const aStateOrder = stateOrder[a.state] !== undefined ? stateOrder[a.state] : 2;
        const bStateOrder = stateOrder[b.state] !== undefined ? stateOrder[b.state] : 2;
        
        if (aStateOrder !== bStateOrder) {
            return aStateOrder - bStateOrder;
        }
        
        // 2. 相同状态下按类型排序
        if (a.type !== b.type) {
            return a.type.localeCompare(b.type);
        }
        
        // 3. 相同类型下按TID排序
        return parseInt(a.tid) - parseInt(b.tid);
    });
    
    // 生成线程列表HTML
    let html = '';
    let currentState = null;
    let currentType = null;
    
    sortedThreads.forEach(thread => {
        // 如果是新状态，添加状态分组标题
        if (thread.state !== currentState) {
            currentState = thread.state;
            const stateText = getStateText(thread.state);
            const stateColor = thread.state === 'R' ? '#ff3b30' : thread.state === 'S' ? '#34c759' : '#ff9500';
            html += `<div style="padding: 8px 15px; background: ${stateColor}; color: white; font-size: 12px; font-weight: 600; position: sticky; top: 0; z-index: 10;">`;
            html += `🔴 ${stateText} (${sortedThreads.filter(t => t.state === thread.state).length}个)`;
            html += `</div>`;
            currentType = null; // 重置类型分组
        }
        
        // 如果是新类型，添加类型子分组
        if (thread.type !== currentType) {
            currentType = thread.type;
            const typeCount = sortedThreads.filter(t => t.state === thread.state && t.type === thread.type).length;
            html += `<div style="padding: 5px 15px; background: #f8f9fa; border-left: 3px solid #007aff; font-size: 11px; font-weight: 600; color: #666;">`;
            html += `📂 ${thread.type} (${typeCount}个)`;
            html += `</div>`;
        }
        
        html += `
            <div class="thread-item">
                <div class="thread-tid">${thread.tid}</div>
                <div class="thread-name" title="${thread.name}">${thread.name}</div>
                <div class="thread-state ${thread.state}">${getStateText(thread.state)}</div>
                <div>${thread.type}</div>
            </div>
        `;
    });
    
    threadListContent.innerHTML = html;
}

// 获取线程状态文本
function getStateText(state) {
    switch (state) {
        case 'R': return '运行中';
        case 'S': return '睡眠中';
        case 'D': return '不可中断';
        case 'T': return '停止';
        case 'Z': return '僵尸';
        default: return state || '未知';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('Android性能监控可视化界面已加载');
    
    setTimeout(() => {
        initCharts();
        initDragAndDrop();
        ensureStatisticsPanelPosition(); // 🔒 关键修改4：确保统计面板位置
        restorePanelOrder();
    }, 100);
    
    // 自动刷新设备列表
    refreshDevices();
});

// 🔒 确保统计面板在所有图表容器上方
function ensureStatisticsPanelPosition() {
    const container = document.querySelector('.container');
    const statisticsPanel = document.getElementById('statisticsPanel');
    const firstChartContainer = document.getElementById('cpuChart-container');
    
    if (container && statisticsPanel && firstChartContainer) {
        // 将统计面板移动到第一个图表容器之前
        container.insertBefore(statisticsPanel, firstChartContainer);
        console.log('✅ 统计面板已放置在图表上方');
    } else {
        console.warn('⚠️ 统计面板位置调整失败：', {
            container: !!container,
            statisticsPanel: !!statisticsPanel,
            firstChartContainer: !!firstChartContainer
        });
    }
}
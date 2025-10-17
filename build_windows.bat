@echo off
REM ============================================
REM Android性能监控工具 - Windows打包脚本
REM ============================================

echo ========================================
echo   Android性能监控工具 - 打包脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [1/5] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] PyInstaller未安装，正在安装...
    pip install pyinstaller
)

echo [2/5] 安装项目依赖...
pip install -r requirements_windows.txt

echo [3/5] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist android\__pycache__ rmdir /s /q android\__pycache__
if exist ios\__pycache__ rmdir /s /q ios\__pycache__

echo [4/5] 开始打包...
echo.
echo 选择打包方式:
echo   1. Android监控 (轻量版, 推荐)
echo   2. 统一监控 (完整版, 支持iOS和Android)
echo   3. 使用spec配置文件打包 (高级)
echo.
set /p choice=请输入选项 [1-3]: 

if "%choice%"=="1" goto build_android
if "%choice%"=="2" goto build_unified
if "%choice%"=="3" goto build_spec
echo [错误] 无效的选项
pause
exit /b 1

:build_android
echo.
echo [打包] Android性能监控 (单文件)...
pyinstaller --onefile ^
    --name "Android性能监控" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "android;android" ^
    --add-data "ios;ios" ^
    --hidden-import=flask ^
    --hidden-import=flask_socketio ^
    --hidden-import=psutil ^
    --hidden-import=engineio ^
    --hidden-import=socketio ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=pandas ^
    start_android_monitor.py
goto finish

:build_unified
echo.
echo [打包] 跨平台统一监控 (单文件)...
pyinstaller --onefile ^
    --name "跨平台性能监控" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "android;android" ^
    --add-data "ios;ios" ^
    --hidden-import=flask ^
    --hidden-import=flask_socketio ^
    --hidden-import=psutil ^
    --hidden-import=engineio ^
    --hidden-import=socketio ^
    --hidden-import=py_ios_device ^
    --hidden-import=pymobiledevice3 ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=pandas ^
    start_unified_monitor.py
goto finish

:build_spec
echo.
echo 可用的spec配置文件:
echo   1. build_android.spec  - Android监控
echo   2. build_unified.spec  - 统一监控
echo.
set /p spec_choice=请选择配置文件 [1-2]: 

if "%spec_choice%"=="1" (
    echo [打包] 使用 build_android.spec...
    pyinstaller build_android.spec
) else if "%spec_choice%"=="2" (
    echo [打包] 使用 build_unified.spec...
    pyinstaller build_unified.spec
) else (
    echo [错误] 无效的选项
    pause
    exit /b 1
)
goto finish

:finish
echo.
echo [5/5] 打包完成！
echo.
echo ========================================
echo   打包结果
echo ========================================
echo 可执行文件位置: dist\
echo.
if exist "dist\Android性能监控.exe" (
    echo ✓ Android性能监控.exe
)
if exist "dist\跨平台性能监控.exe" (
    echo ✓ 跨平台性能监控.exe
)
echo.
echo ========================================
echo   使用说明
echo ========================================
echo 1. Android监控需要安装 ADB (Android SDK Platform Tools)
echo 2. iOS监控需要安装 iTunes 或 Apple Device Support (实验性)
echo 3. 双击exe文件即可运行
echo 4. 首次运行可能被杀毒软件拦截，请添加信任
echo.
echo 按任意键退出...
pause >nul

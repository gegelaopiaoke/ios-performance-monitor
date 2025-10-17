"""
Windows 平台资源路径修复工具
用于确保打包后的exe能正确访问资源文件
"""

import sys
import os


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    适配开发环境和 PyInstaller 打包后的环境
    
    Args:
        relative_path: 相对路径，如 'templates' 或 'static/css/style.css'
    
    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller 创建临时文件夹并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境中使用当前工作目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_project_root():
    """
    获取项目根目录
    适配开发环境和打包后的环境
    """
    try:
        # PyInstaller 打包后的环境
        return sys._MEIPASS
    except AttributeError:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


def get_template_folder():
    """获取模板文件夹路径"""
    return get_resource_path('templates')


def get_static_folder():
    """获取静态文件夹路径"""
    return get_resource_path('static')


def get_logs_folder():
    """获取日志文件夹路径（使用用户目录，避免权限问题）"""
    # 使用用户目录存储日志，打包后也能正常工作
    user_home = os.path.expanduser('~')
    logs_dir = os.path.join(user_home, '.android_performance_monitor', 'logs')
    
    # 确保目录存在
    os.makedirs(logs_dir, exist_ok=True)
    
    return logs_dir


def get_data_folder():
    """获取数据文件夹路径（使用用户目录）"""
    user_home = os.path.expanduser('~')
    data_dir = os.path.join(user_home, '.android_performance_monitor', 'data')
    
    # 确保目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    return data_dir


# 使用示例：
if __name__ == '__main__':
    print("=" * 60)
    print("资源路径工具 - 路径测试")
    print("=" * 60)
    print(f"项目根目录: {get_project_root()}")
    print(f"模板文件夹: {get_template_folder()}")
    print(f"静态文件夹: {get_static_folder()}")
    print(f"日志文件夹: {get_logs_folder()}")
    print(f"数据文件夹: {get_data_folder()}")
    print("=" * 60)
    
    # 检查路径是否存在
    paths_to_check = [
        ('templates', get_template_folder()),
        ('static', get_static_folder()),
        ('logs', get_logs_folder()),
        ('data', get_data_folder()),
    ]
    
    print("\n路径存在性检查:")
    for name, path in paths_to_check:
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"  {exists} {name}: {path}")

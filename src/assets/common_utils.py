import os
import sys
import json
import subprocess
import shutil
import urllib.request
import tempfile
import webbrowser
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime

def print_header(title):
    """打印标题栏"""
    print("=" * 38)
    print(f"{title:^38}")
    print("=" * 38)

def ensure_directory(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_application_path():
    """获取应用程序路径，兼容打包环境"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    print(f"[调试] 应用程序路径: {application_path}")
    return application_path


def get_game_build_guid(game_path):
    """获取游戏的build-guid作为版本标识"""
    boot_config_path = os.path.join(game_path, "Sultan's Game_Data", "boot.config")
    
    if not os.path.exists(boot_config_path):
        print(f"[警告] 找不到boot.config文件: {boot_config_path}")
        return None
    
    try:
        with open(boot_config_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # 查找build-guid行
        for line in content.splitlines():
            if line.startswith('build-guid='):
                build_guid = line.split('=', 1)[1].strip()
                print(f"[信息] 找到游戏build-guid: {build_guid}")
                return build_guid
        
        print("[警告] boot.config中未找到build-guid属性")
        return None
    except Exception as e:
        print(f"[错误] 读取boot.config文件时出错: {e}")
        return None

def get_game_path():
    """获取游戏路径"""
    # 首先尝试从配置文件获取
    config_dir = os.path.join(get_application_path(), "config")
    config_file = os.path.join(config_dir, "config.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'game_path' in config and os.path.exists(config['game_path']):
                    return config['game_path']
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    
    # 尝试自动查找游戏路径
    # 常见的安装位置
    common_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Sultan's Game",
        r"C:\Program Files\Steam\steamapps\common\Sultan's Game",
        r"D:\Program Files (x86)\Steam\steamapps\common\Sultan's Game",
        r"D:\Program Files\Steam\steamapps\common\Sultan's Game",
        r"E:\Program Files (x86)\Steam\steamapps\common\Sultan's Game",
        r"E:\Program Files\Steam\steamapps\common\Sultan's Game",
        r"C:\Games\Steam\steamapps\common\Sultan's Game",
        r"D:\Games\Steam\steamapps\common\Sultan's Game",
        r"E:\Games\Steam\steamapps\common\Sultan's Game",
        r"C:\Game\Steam\steamapps\common\Sultan's Game",
        r"D:\Game\Steam\steamapps\common\Sultan's Game",
        r"E:\Game\Steam\steamapps\common\Sultan's Game"
    ]
    
    for path in common_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "Sultan's Game.exe")):
            return path
    
    # 如果找不到，返回None而不是请求用户输入
    return None    

def get_config_dir(game_path):
    """获取游戏配置目录"""
    return os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "config")

def check_git_installed():
    """检查Git是否已安装"""
    try:
        result = subprocess.run(
            ['git', '--version'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def show_confirm_dialog(title, message):
    """显示确认对话框，返回用户选择（True表示确认，False表示取消）"""
    # 创建一个隐藏的根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 将窗口放在屏幕前面
    root.attributes('-topmost', True)
    
    # 显示确认对话框
    result = messagebox.askyesno(title, message)
    
    # 销毁根窗口
    root.destroy()
    
    return result

def download_and_install_git():
    """下载并安装Git"""
    print("[信息] 正在准备下载Git安装程序...")
    git_url = "https://registry.npmmirror.com/-/binary/git-for-windows/v2.49.0.windows.1/Git-2.49.0-64-bit.exe"
    
    # 使用弹窗询问用户是否下载
    if not show_confirm_dialog("下载Git", "Git未安装，是否下载并安装Git？"):
        print("[信息] 用户取消下载Git，程序无法继续")
        sys.exit(0)  # 正常退出程序
        return False
    
    # 创建临时文件
    temp_file = os.path.join(tempfile.gettempdir(), "Git-2.49.0-64-bit.exe")
    
    try:
        print(f"[下载] 正在从 {git_url} 下载Git安装程序...")
        print("[下载] 这可能需要几分钟时间，请耐心等待...")
        
        # 下载文件，显示进度
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size))
            if percent % 10 == 0:  # 每10%显示一次进度
                print(f"[下载] 已完成: {percent}%")
        
        urllib.request.urlretrieve(git_url, temp_file, reporthook=report_progress)
        
        print("[下载] Git安装程序下载完成")
        
        # 使用弹窗询问用户是否安装
        if show_confirm_dialog("安装Git", "是否立即安装Git？"):
            print("[安装] 正在启动Git安装程序...")
            # 启动安装程序
            os.startfile(temp_file)
            print("[安装] 请完成Git安装后再继续")
            
            # 再次检查Git是否安装成功
            if check_git_installed():
                print("[成功] Git已成功安装")
                return True
            else:
                print("[警告] Git安装可能未完成，请手动完成安装后再运行程序")
                return False
        else:
            print(f"[信息] Git安装程序已下载到: {temp_file}")
            print("[信息] 请手动安装Git后再运行程序")
            return False
            
    except Exception as e:
        print(f"[错误] 下载或安装Git时出错: {e}")
        print("[信息] 请手动下载并安装Git: https://registry.npmmirror.com/-/binary/git-for-windows/v2.49.0.windows.1/Git-2.49.0-64-bit.exe")
        
        # 使用弹窗询问是否在浏览器中打开下载链接
        if show_confirm_dialog("打开浏览器", "是否在浏览器中打开下载链接？"):
            webbrowser.open(git_url)
            
        return False

def run_git_command(cmd, cwd=None, check=True):
    """运行Git命令并返回输出"""
    try:
        startupinfo = None
        creationflags = 0

        if os.name == "nt":  # 仅在 Windows 下设置
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        stdout, stderr = process.communicate()

        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, output=stdout, stderr=stderr)

        return stdout, stderr, process.returncode
    except Exception as e:
        if check:
            raise e
        return "", str(e), 1
        
def restore_old_version_mods(game_path, bak_dir, config_dir):
    """还原旧版本MOD管理器的备份文件"""
    # 统计计数器
    restored_count = 0
    
    # 遍历备份目录中的所有文件
    for root, _, files in os.walk(bak_dir):
        for file in files:
            if file.endswith('.bak'):
                bak_file = os.path.join(root, file)
                
                # 计算原始文件路径
                rel_path = os.path.relpath(bak_file, bak_dir)
                rel_path = rel_path[:-4]  # 移除.bak后缀
                
                # 修复：检查rel_path是否包含重复路径
                if rel_path.startswith("Sultan's Game_Data/StreamingAssets/config/") or \
                   rel_path.startswith("Sultan's Game_Data\\StreamingAssets\\config\\"):
                    parts = rel_path.split('config/', 1) if '/' in rel_path else rel_path.split('config\\', 1)
                    if len(parts) > 1:
                        rel_path = parts[1]
                
                target_file = os.path.join(config_dir, rel_path)
                
                # 检查备份文件大小
                if os.path.getsize(bak_file) <= 1:
                    # 这是空备份文件，表示原始文件不存在或是ADD模式的备份，删除目标文件
                    if os.path.exists(target_file):
                        os.remove(target_file)
                        print(f"  - 删除文件: {target_file}")
                        restored_count += 1
                else:
                    # 这是其他模式的备份，恢复文件
                    target_dir = os.path.dirname(target_file)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    
                    shutil.copy2(bak_file, target_file)
                    print(f"  - 恢复文件: {target_file}")
                    restored_count += 1
                
                # 删除备份文件
                os.remove(bak_file)
    
    # 删除空目录
    for root, dirs, files in os.walk(bak_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)
    
    # 尝试删除bak目录（如果为空）
    try:
        if os.path.exists(bak_dir) and not os.listdir(bak_dir):
            os.rmdir(bak_dir)
            print("[兼容] 已删除空的bak目录")
    except:
        pass
    
    print("=" * 38)
    print("旧版本MOD还原完成")
    print(f"  还原: {restored_count} 个文件")
    print("=" * 38)
    
    return True
    
def init_git_repo(config_dir):
    """初始化Git仓库"""
    if(not check_git_installed()):
        print("[Git] Git未安装，正在尝试下载并安装Git...")
        download_and_install_git()
    print("[Git] 正在初始化Git仓库...")
    
    # 检查是否已经是Git仓库
    stdout, stderr, code = run_git_command(['git', 'status'], cwd=config_dir, check=False)
    is_new_repo = code != 0
    
    # 如果是新仓库，尝试使用预先准备的.git.zip
    if is_new_repo:
        # 检查应用路径下是否存在.git.zip
        app_path = get_application_path()
        git_zip_path = os.path.join(app_path, ".git.zip")
        
        if os.path.exists(git_zip_path):
            print("[Git] 发现预先准备的Git仓库压缩包，正在解压...")
            try:
                import zipfile
                with zipfile.ZipFile(git_zip_path, 'r') as zip_ref:
                    # 解压到配置目录
                    zip_ref.extractall(config_dir)
                
                # 验证解压是否成功
                if os.path.exists(os.path.join(config_dir, ".git")):
                    print("[Git] 成功从压缩包恢复Git仓库")
                    
                    # 检查是否需要更新游戏版本标签
                    game_path = os.path.dirname(os.path.dirname(os.path.dirname(config_dir)))
                    build_guid = get_game_build_guid(game_path)
                    
                    if build_guid:
                        tag_name = f"game_version_{build_guid}"
                        # 检查标签是否存在
                        stdout, stderr, code = run_git_command(['git', 'tag', '-l', tag_name], cwd=config_dir, check=False)
                        if not stdout.strip():
                            print(f"[Git] 为当前游戏版本创建标签: {tag_name}")
                            # 创建标签
                            run_git_command(['git', 'tag', tag_name], cwd=config_dir, check=False)
                    
                    return True
                else:
                    print("[Git] 解压后未找到.git目录，将继续常规初始化")
            except Exception as e:
                print(f"[Git] 解压.git.zip时出错: {e}")
                print("[Git] 将继续常规初始化过程")
        else:
            print("[Git] 未找到预先准备的Git仓库压缩包，将进行常规初始化")
        
        print("\n" + "=" * 60)
        print("[重要提示] 初始化仓库需要一个干净的游戏环境，请确保：")
        print("  1. 游戏没有安装任何MOD")
        print("  2. 游戏处于原始状态，没有任何自定义修改")
        print("=" * 60)
        
        # 使用弹窗询问用户确认游戏环境干净
        if not show_confirm_dialog("确认游戏环境", "请确认游戏环境干净，没有安装其他MOD"):
            print("[信息] 用户取消初始化，请在确保游戏环境干净后再试")
            return False
        
        print("[信息] 用户已确认游戏环境干净，继续初始化仓库...\n")
    
    print("[提示] 整个过程可能需要几分钟时间，请耐心等待...")
    
    # 显示进度动画
    import threading
    import time
    
    stop_animation = False
    
    def progress_animation():
        animation = "|/-\\"
        idx = 0
        while not stop_animation:
            print(f"\r[进行中] 正在初始化Git仓库... {animation[idx % len(animation)]}", end="")
            idx += 1
            time.sleep(0.1)
    
    # 启动进度动画线程
    animation_thread = threading.Thread(target=progress_animation)
    animation_thread.daemon = True
    animation_thread.start()
    
    try:
        # 检查是否存在旧版本的bak目录，如果存在则先还原
        game_path = os.path.dirname(os.path.dirname(os.path.dirname(config_dir)))
        bak_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "bak")
        
        if os.path.exists(bak_dir) and os.listdir(bak_dir):
            print("\r[兼容] 检测到旧版本MOD管理器的备份文件，正在还原...      ")
            restore_old_version_mods(game_path, bak_dir, config_dir)
        
        # 检查是否已经是Git仓库
        print("\r[Git] 检查是否已经是Git仓库...                           ", end="")
        if not is_new_repo:
            print("\r[Git] 已存在Git仓库                                  ")
            
            # 检查是否存在游戏版本标签
            print("\r[Git] 检查是否存在游戏版本标签...                     ", end="")
            tag_stdout, tag_stderr, tag_code = run_git_command(
                ['git', 'tag', '-l', 'game_version_*'], 
                cwd=config_dir, 
                check=False
            )
            
            # 检查是否存在游戏版本更新或初始化提交
            print("\r[Git] 检查是否存在游戏版本更新或初始化提交...          ", end="")
            log_stdout, log_stderr, log_code = run_git_command(
                ['git', 'log', '--grep=游戏版本更新|初始游戏版本', '--extended-regexp', '--format=%H', '-n', '1'], 
                cwd=config_dir, 
                check=False
            )
            
            # 如果没有游戏版本标签或相关提交，则创建一个初始化提交
            if not tag_stdout.strip() or not log_stdout.strip():
                print("\r[Git] 已存在仓库但未找到游戏版本标签或初始化提交，将创建初始化提交...")
                
                # 配置用户信息（确保存在）
                print("\r[Git] 配置用户信息...                             ", end="")
                run_git_command(['git', 'config', 'user.name', 'Sultan Mod Manager'], cwd=config_dir)
                run_git_command(['git', 'config', 'user.email', 'mod@example.com'], cwd=config_dir)
                
                # 创建一个空提交作为初始化
                print("\r[Git] 创建初始化提交...                           ", end="")
                empty_commit_stdout, empty_commit_stderr, empty_commit_code = run_git_command(
                    ['git', 'commit', '--allow-empty', '-m', f'初始游戏版本 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
                    cwd=config_dir,
                    check=False
                )
                
                if empty_commit_code != 0:
                    print(f"\r[警告] 无法创建初始化提交: {empty_commit_stderr}")
                else:
                    # 创建主分支标签
                    # 获取build-guid作为版本标识
                    print("\r[Git] 获取游戏版本标识...                      ", end="")
                    build_guid = get_game_build_guid(game_path)
                    
                    if build_guid:
                        tag_name = f"game_version_{build_guid}"
                    else:
                        # 兼容旧版本，使用时间戳
                        game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
                        if os.path.exists(game_exe_path):
                            mod_time = os.path.getmtime(game_exe_path)
                            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
                            tag_name = f"game_version_{mod_time_str}"
                        else:
                            # 如果找不到游戏可执行文件，使用当前时间
                            tag_name = f"game_version_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    print(f"\r[Git] 创建游戏版本标签: {tag_name}...           ", end="")
                    stdout, stderr, code = run_git_command(
                        ['git', 'tag', tag_name],
                        cwd=config_dir
                    )
                    if code != 0:
                        print(f"\r[警告] 无法创建标签: {stderr}")
                    else:
                        print(f"\r[Git] 已在现有仓库上创建游戏版本标签: {tag_name}")
            
            return True
        
        # 初始化仓库
        print("\r[Git] 初始化新的Git仓库...                            ", end="")
        stdout, stderr, code = run_git_command(['git', 'init'], cwd=config_dir)
        if code != 0:
            print(f"\r[错误] 无法初始化Git仓库: {stderr}")
            return False
        
        # 配置用户信息
        print("\r[Git] 配置用户信息...                                 ", end="")
        run_git_command(['git', 'config', 'user.name', 'Sultan Mod Manager'], cwd=config_dir)
        run_git_command(['git', 'config', 'user.email', 'mod@example.com'], cwd=config_dir)
        
        # 添加所有文件
        print("\r[Git] 添加所有文件到仓库...                           ", end="")
        run_git_command(['git', 'add', '.'], cwd=config_dir)
        
        # 提交初始版本
        print("\r[Git] 提交初始版本...                                ", end="")
        stdout, stderr, code = run_git_command(
            ['git', 'commit', '-m', f'初始游戏版本 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
            cwd=config_dir
        )
        if code != 0:
            print(f"\r[错误] 无法提交初始版本: {stderr}")
            return False
        
        # 创建主分支标签
        # 获取build-guid作为版本标识
        print("\r[Git] 获取游戏版本标识...                            ", end="")
        build_guid = get_game_build_guid(game_path)
        
        if build_guid:
            tag_name = f"game_version_{build_guid}"
        else:
            # 兼容旧版本，使用时间戳
            game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
            if os.path.exists(game_exe_path):
                mod_time = os.path.getmtime(game_exe_path)
                mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
                tag_name = f"game_version_{mod_time_str}"
            else:
                # 如果找不到游戏可执行文件，使用当前时间
                tag_name = f"game_version_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        print(f"\r[Git] 创建游戏版本标签: {tag_name}...                 ", end="")
        stdout, stderr, code = run_git_command(
            ['git', 'tag', tag_name],
            cwd=config_dir
        )
        if code != 0:
            print(f"\r[警告] 无法创建标签: {stderr}")
        
        print("\r[Git] Git仓库初始化完成                              ")
        return True
    finally:
        # 停止进度动画
        stop_animation = True
        animation_thread.join(0.5)  # 等待动画线程结束，最多等待0.5秒
        print("\r" + " " * 60 + "\r", end="")  # 清除动画行

def reset_to_game_version(config_dir, game_path):
    """重置Git仓库到游戏当前版本"""
    print("[Git] 正在重置仓库到游戏当前版本...")
    
    # 获取build-guid作为版本标识
    build_guid = get_game_build_guid(game_path)
    
    if build_guid:
        tag_name = f"game_version_{build_guid}"
        print(f"[Git] 使用build-guid作为版本标识: {build_guid}")
    else:
        # 兼容旧版本，使用时间戳
        game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
        if not os.path.exists(game_exe_path):
            print("[错误] 找不到游戏可执行文件")
            return False
        
        mod_time = os.path.getmtime(game_exe_path)
        mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
        tag_name = f"game_version_{mod_time_str}"
        print(f"[Git] 使用文件修改时间作为版本标识: {mod_time_str}")
    
    # 检查是否存在对应标签
    stdout, stderr, code = run_git_command(['git', 'tag', '-l', tag_name], cwd=config_dir)
    is_version_updated = stdout.strip() == ""
    
    # 如果通过build-guid没找到标签，尝试通过exe文件更新时间查找
    if is_version_updated and build_guid:
        print("[Git] 通过build-guid未找到标签，尝试通过exe文件更新时间查找...")
        game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
        if os.path.exists(game_exe_path):
            mod_time = os.path.getmtime(game_exe_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
            old_tag_name = f"game_version_{mod_time_str}"
            
            # 检查是否存在基于时间的标签
            stdout, stderr, code = run_git_command(['git', 'tag', '-l', old_tag_name], cwd=config_dir)
            if stdout.strip() != "":
                print(f"[Git] 找到基于时间的标签: {old_tag_name}，认为游戏版本未更新")
                
                # 获取该标签对应的提交
                commit_stdout, commit_stderr, commit_code = run_git_command(
                    ['git', 'rev-parse', old_tag_name], 
                    cwd=config_dir
                )
                if commit_code == 0:
                    commit_hash = commit_stdout.strip()
                    
                    # 给该提交添加新的build-guid标签
                    tag_stdout, tag_stderr, tag_code = run_git_command(
                        ['git', 'tag', tag_name, commit_hash],
                        cwd=config_dir
                    )
                    if tag_code == 0:
                        print(f"[Git] 已将build-guid标签 {tag_name} 添加到原有提交 {commit_hash[:8]}")
                        is_version_updated = False
                    else:
                        print(f"[警告] 无法添加build-guid标签: {tag_stderr}")
                else:
                    print(f"[警告] 无法获取标签对应的提交: {commit_stderr}")
    
    # 如果版本没有更新，直接丢弃未提交的更改
    if not is_version_updated:
        print(f"[Git] 找到游戏版本标签 {tag_name}，游戏版本未更新")
        # 丢弃所有未提交的更改
        run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
    else:
        print(f"[Git] 未找到游戏版本标签 {tag_name}，检测到游戏版本更新")

        # 获取上次游戏版本更新的提交
        stdout, stderr, code = run_git_command(
            ['git', 'log', '--grep=游戏版本更新|初始游戏版本', '--extended-regexp', '--format=%H', '-n', '1'], 
            cwd=config_dir, 
            check=False
        )
        last_update_commit = stdout.strip()
        
        # 如果找到了上次游戏版本更新的提交，删除之前添加的文件
        mod_added_files = []
        if last_update_commit:
            print(f"[Git] 找到上次游戏版本更新提交: {last_update_commit[:8]}")
            # 获取从上次更新到现在添加的文件列表
            stdout, stderr, code = run_git_command(
                ['git', 'diff', '--name-only', '--diff-filter=A', last_update_commit], 
                cwd=config_dir, 
                check=False
            )
            mod_added_files = stdout.strip().split('\n') if stdout.strip() else []
            print(f"[Git] 找到 {len(mod_added_files)} 个MOD添加的文件")
        
        # 创建临时目录用于存储当前游戏文件
        temp_dir = os.path.join(os.path.dirname(config_dir), "temp_game_files")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # 复制当前游戏配置文件到临时目录，但排除MOD添加的文件
        for item in os.listdir(config_dir):
            if item != '.git':  # 排除.git目录
                src_path = os.path.join(config_dir, item)
                rel_path = item
                
                # 检查是否是MOD添加的文件
                if rel_path in mod_added_files:
                    print(f"[Git] 排除MOD添加的文件: {rel_path}")
                    continue
                
                # 如果是目录，需要递归检查
                if os.path.isdir(src_path):
                    for root, dirs, files in os.walk(src_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_file_path = os.path.relpath(file_path, config_dir).replace('\\', '/')
                            if rel_file_path in mod_added_files:
                                print(f"[Git] 排除MOD添加的文件: {rel_file_path}")
                                # 不复制这个文件
                                continue
                    
                    # 复制目录（不包含MOD添加的文件）
                    dst_path = os.path.join(temp_dir, item)
                    if not os.path.exists(dst_path):
                        os.makedirs(dst_path)
                    
                    for root, dirs, files in os.walk(src_path):
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            rel_dir_path = os.path.relpath(dir_path, src_path)
                            dst_dir_path = os.path.join(dst_path, rel_dir_path)
                            if not os.path.exists(dst_dir_path):
                                os.makedirs(dst_dir_path)
                        
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_file_path = os.path.relpath(file_path, config_dir).replace('\\', '/')
                            if rel_file_path not in mod_added_files:
                                rel_path_in_dir = os.path.relpath(file_path, src_path)
                                dst_file_path = os.path.join(dst_path, rel_path_in_dir)
                                dst_dir = os.path.dirname(dst_file_path)
                                if not os.path.exists(dst_dir):
                                    os.makedirs(dst_dir)
                                shutil.copy2(file_path, dst_file_path)
                else:
                    # 复制文件
                    dst_path = os.path.join(temp_dir, item)
                    shutil.copy2(src_path, dst_path)
    
    # 获取当前分支
    current_branch_stdout, _, _ = run_git_command(['git', 'branch', '--show-current'], cwd=config_dir, check=False)
    current_branch = current_branch_stdout.strip()
    
    # 获取所有分支
    all_branches_stdout, _, _ = run_git_command(['git', 'branch'], cwd=config_dir, check=False)
    all_branches = [b.strip().replace('* ', '') for b in all_branches_stdout.split('\n') if b.strip()]
    
    # 确定主分支
    main_branch = None
    for branch_name in ['master', 'main']:
        if branch_name in all_branches:
            main_branch = branch_name
            break
    
    # 如果没有找到master或main分支，但有其他分支，使用第一个非当前分支
    if main_branch is None and all_branches:
        for branch in all_branches:
            if branch != current_branch and branch != f"* {current_branch}":
                main_branch = branch
                break
    
    # 如果仍然没有找到主分支，但有当前分支，使用当前分支
    if main_branch is None and current_branch:
        main_branch = current_branch
        print(f"[Git] 使用当前分支作为主分支: {main_branch}")
    
    # 如果没有任何分支，创建一个master分支
    if main_branch is None:
        print("[Git] 没有找到任何分支，创建master分支")
        stdout, stderr, code = run_git_command(['git', 'checkout', '-b', 'master'], cwd=config_dir, check=False)
        if code != 0:
            print(f"[错误] 无法创建master分支: {stderr}")
            return False
        main_branch = 'master'
    
    # 切换到主分支
    if current_branch != main_branch:
        print(f"[Git] 切换到主分支: {main_branch}")
        # 强制切换分支，丢弃所有未提交的更改
        stdout, stderr, code = run_git_command(['git', 'checkout', '-f', main_branch], cwd=config_dir, check=False)
        if code != 0:
            print(f"[错误] 无法切换到主分支 {main_branch}: {stderr}")
            return False
    
    # 不再删除所有其他分支，保留所有MOD分支
    
    # 如果游戏版本已更新，处理文件更新
    if is_version_updated and 'temp_dir' in locals() and os.path.exists(temp_dir):
        # 清空仓库中的所有文件（除了.git目录）
        for item in os.listdir(config_dir):
            if item != '.git':
                item_path = os.path.join(config_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        # 将临时目录中的文件复制回仓库
        for item in os.listdir(temp_dir):
            src_path = os.path.join(temp_dir, item)
            dst_path = os.path.join(config_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        
        # 删除临时目录
        shutil.rmtree(temp_dir)
        
        # 添加所有文件并提交（包括删除的文件）
        run_git_command(['git', 'add', '--all'], cwd=config_dir)
        stdout, stderr, code = run_git_command(
            ['git', 'commit', '-m', f'游戏版本更新 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
            cwd=config_dir,
            check=False
        )
        
        if code != 0 and "nothing to commit" not in stderr:
            print(f"[警告] 提交游戏版本更新时出现问题: {stderr}")
        
        # 创建标签
        stdout, stderr, code = run_git_command(['git', 'tag', tag_name], cwd=config_dir)
        if code != 0:
            print(f"[错误] 无法创建标签: {stderr}")
            return False
    
    # 硬重置到标签
    stdout, stderr, code = run_git_command(['git', 'reset', '--hard', tag_name], cwd=config_dir)
    if code != 0:
        print(f"[错误] 无法重置到标签 {tag_name}: {stderr}")
        return False
    

     # 清除所有未进行版本控制的文件
    print("[Git] 清除所有未进行版本控制的文件...")
    stdout, stderr, code = run_git_command(['git', 'clean', '-fdx'], cwd=config_dir, check=False)
    if code != 0:
        print(f"[警告] 清除未版本控制文件时出现问题: {stderr}")
    else:
        print("[Git] 已清除所有未版本控制的文件")


    print(f"[Git] 已重置到游戏版本 {tag_name}")
    return True

def prepare_git_environment(game_path):
    """准备Git环境"""
    config_dir = get_config_dir(game_path)
    
    # 确保配置目录存在
    ensure_directory(config_dir)
    
    # 初始化Git仓库
    if not init_git_repo(config_dir):
        return False
    
    # 重置到游戏当前版本
    if not reset_to_game_version(config_dir, game_path):
        return False
    
    return True

# 添加彩色输出支持
class Colors:
    """终端颜色代码"""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

def colored_print(message, color=Colors.RESET, end="\n"):
    """打印彩色文本"""
    print(f"{color}{message}{Colors.RESET}", end=end)

def generate_safe_branch_name(name):
    """生成安全的分支名称，移除不允许的字符"""
    # 移除不允许的字符，只保留字母、数字、下划线和连字符
    safe_name = ''.join(c if c.isalnum() or c in '_-' else '_' for c in name)
    
    # 确保不以连字符或点开头
    if safe_name.startswith('-') or safe_name.startswith('.'):
        safe_name = 'mod' + safe_name
    
    # 确保不为空
    if not safe_name:
        safe_name = 'mod'
    
    # 转为小写并限制长度
    safe_name = safe_name.lower()[:50]
    
    return safe_name

if __name__ == "__main__":
    download_and_install_git()

import os
import sys
import json
import subprocess
import shutil
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

def get_game_path():
    """获取游戏路径"""
    possible_paths = [
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
    now_application_path = get_application_path()
    if "Sultan's Game" in now_application_path:
        possible_paths.append(now_application_path)  # 添加应用程序路径

    # 检查缓存的游戏路径
    config_file = 'game_path_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            cached_path = json.load(f).get('game_path')
            if cached_path and os.path.exists(cached_path):
                print(f"[信息] 使用缓存的游戏路径: {cached_path}")
                return cached_path

    # 检查可能的路径
    for path in possible_paths:
        if os.path.exists(path):
            print(f"[信息] 找到游戏路径: {path}")
            return path

    # 提示用户输入路径
    while True:
        user_input = input("未找到游戏路径，请输入游戏根目录（应包含'Sultan's Game'文件夹）: ").strip()
        if "Sultan's Game" in user_input:
            game_path = user_input.split("Sultan's Game")[0] + "Sultan's Game"
            if os.path.exists(game_path):
                # 缓存路径
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'game_path': game_path}, f, ensure_ascii=False, indent=2)
                print(f"[信息] 使用用户输入的游戏路径: {game_path}")
                return game_path
            else:
                print("[警告] 输入的路径不存在，请确认后重试。")
        else:
            confirm = input("输入的路径可能不是游戏路径，输入 '我确定这就是游戏路径' 以强制使用该路径: ").strip()
            if confirm == "我确定这就是游戏路径":
                # 缓存路径
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'game_path': user_input}, f, ensure_ascii=False, indent=2)
                print(f"[信息] 强制使用用户输入的游戏路径: {user_input}")
                return user_input

def get_config_dir(game_path):
    """获取游戏配置目录"""
    return os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "config")

def run_git_command(command, cwd=None, check=True):
    """运行Git命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            cwd=cwd, 
            check=check, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        print(f"[错误] Git命令执行失败: {e}")
        print(f"命令: {' '.join(command)}")
        print(f"错误输出: {e.stderr}")
        return "", e.stderr, e.returncode

def init_git_repo(config_dir):
    """初始化Git仓库"""
    print("[Git] 正在初始化Git仓库...")
    
    # 检查是否已经是Git仓库
    stdout, stderr, code = run_git_command(['git', 'status'], cwd=config_dir, check=False)
    if code == 0:
        print("[Git] 已存在Git仓库")
        return True
    
    # 初始化仓库
    stdout, stderr, code = run_git_command(['git', 'init'], cwd=config_dir)
    if code != 0:
        print(f"[错误] 无法初始化Git仓库: {stderr}")
        return False
    
    # 配置用户信息
    run_git_command(['git', 'config', 'user.name', 'Sultan Mod Manager'], cwd=config_dir)
    run_git_command(['git', 'config', 'user.email', 'mod@example.com'], cwd=config_dir)
    
    # 添加所有文件
    run_git_command(['git', 'add', '.'], cwd=config_dir)
    
    # 提交初始版本
    stdout, stderr, code = run_git_command(
        ['git', 'commit', '-m', f'初始游戏版本 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
        cwd=config_dir
    )
    if code != 0:
        print(f"[错误] 无法提交初始版本: {stderr}")
        return False
    
    # 创建主分支标签
    game_exe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(config_dir))), "Sultan's Game.exe")
    if os.path.exists(game_exe_path):
        mod_time = os.path.getmtime(game_exe_path)
        mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
        tag_name = f"game_version_{mod_time_str}"
        
        stdout, stderr, code = run_git_command(
            ['git', 'tag', tag_name],
            cwd=config_dir
        )
        if code != 0:
            print(f"[警告] 无法创建标签: {stderr}")
    
    print("[Git] Git仓库初始化完成")
    return True

def reset_to_game_version(config_dir, game_path):
    """重置Git仓库到游戏当前版本"""
    print("[Git] 正在重置仓库到游戏当前版本...")
    
    # 先切换到master分支
    stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir, check=False)
    if code != 0:
        # 如果master分支不存在，使用main分支
        stdout, stderr, code = run_git_command(['git', 'checkout', 'main'], cwd=config_dir, check=False)
        if code != 0:
            # 如果main分支也不存在，检查当前分支
            stdout, stderr, code = run_git_command(['git', 'branch', '--show-current'], cwd=config_dir)
            if stdout.strip() == "":
                print("[错误] 无法确定主分支")
                return False
    
    # 删除所有其他分支
    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
    branches = [b.strip() for b in stdout.split('\n') if b.strip() and not b.strip().startswith('*')]
    
    for branch in branches:
        run_git_command(['git', 'branch', '-D', branch], cwd=config_dir, check=False)
    
    # 获取游戏可执行文件的修改时间
    game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
    if not os.path.exists(game_exe_path):
        print("[错误] 找不到游戏可执行文件")
        return False
    
    mod_time = os.path.getmtime(game_exe_path)
    mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
    tag_name = f"game_version_{mod_time_str}"
    
    # 检查是否存在对应标签
    stdout, stderr, code = run_git_command(['git', 'tag', '-l', tag_name], cwd=config_dir)
    if stdout.strip() == "":
        # 标签不存在，创建新标签 - 游戏版本已更新
        print(f"[Git] 未找到游戏版本标签 {tag_name}，检测到游戏版本更新")
        
        # 创建临时目录用于存储当前游戏文件
        temp_dir = os.path.join(os.path.dirname(config_dir), "temp_game_files")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # 复制当前游戏配置文件到临时目录
        for item in os.listdir(config_dir):
            if item != '.git':  # 排除.git目录
                src_path = os.path.join(config_dir, item)
                dst_path = os.path.join(temp_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
        
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
    else:
        print(f"[Git] 找到游戏版本标签 {tag_name}")
    
    # 硬重置到标签
    stdout, stderr, code = run_git_command(['git', 'reset', '--hard', tag_name], cwd=config_dir)
    if code != 0:
        print(f"[错误] 无法重置到标签 {tag_name}: {stderr}")
        return False
    
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
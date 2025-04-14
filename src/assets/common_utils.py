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
        
        # 检查是否存在游戏版本标签
        tag_stdout, tag_stderr, tag_code = run_git_command(
            ['git', 'tag', '-l', 'game_version_*'], 
            cwd=config_dir, 
            check=False
        )
        
        # 检查是否存在游戏版本更新或初始化提交
        log_stdout, log_stderr, log_code = run_git_command(
            ['git', 'log', '--grep=游戏版本更新|初始游戏版本', '--extended-regexp', '--format=%H', '-n', '1'], 
            cwd=config_dir, 
            check=False
        )
        
        # 如果没有游戏版本标签或相关提交，则创建一个初始化提交
        if not tag_stdout.strip() or not log_stdout.strip():
            print("[Git] 已存在仓库但未找到游戏版本标签或初始化提交，将创建初始化提交...")
            
            # 配置用户信息（确保存在）
            run_git_command(['git', 'config', 'user.name', 'Sultan Mod Manager'], cwd=config_dir)
            run_git_command(['git', 'config', 'user.email', 'mod@example.com'], cwd=config_dir)
            
            # 创建一个空提交作为初始化
            empty_commit_stdout, empty_commit_stderr, empty_commit_code = run_git_command(
                ['git', 'commit', '--allow-empty', '-m', f'初始游戏版本 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
                cwd=config_dir,
                check=False
            )
            
            if empty_commit_code != 0:
                print(f"[警告] 无法创建初始化提交: {empty_commit_stderr}")
            else:
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
                    else:
                        print(f"[Git] 已在现有仓库上创建游戏版本标签: {tag_name}")
        
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
    is_version_updated = stdout.strip() == ""
    
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
    
    # 删除所有其他分支
    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
    branches = [b.strip() for b in stdout.split('\n') if b.strip() and not b.strip().startswith('*')]
    
    for branch in branches:
        if branch != main_branch:
            run_git_command(['git', 'branch', '-D', branch], cwd=config_dir, check=False)
    
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
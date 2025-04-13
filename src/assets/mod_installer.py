import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime  # 添加这一行

# 导入公共工具
from common_utils import (
    print_header, ensure_directory, get_application_path, get_game_path,
    get_config_dir, prepare_git_environment, run_git_command
)

def apply_patch(patch_file, config_dir, mod_name):
    """应用补丁文件"""
    print(f"[应用] MOD: {mod_name}")
    
    if not os.path.exists(patch_file):
        print(f"[错误] 补丁文件不存在: {patch_file}")
        return False
    
    # 首先尝试使用git am命令应用补丁
    print(f"[尝试] 使用git am应用补丁...")
    stdout, stderr, code = run_git_command(['git', 'am', '--ignore-space-change','--keep-cr', patch_file], cwd=config_dir, check=False)
    if code == 0:
        print(f"[成功] 使用git am应用补丁成功")
        return True
    
    # git am失败，中止补丁应用
    print(f"[警告] git am应用补丁失败: {stderr}")
    run_git_command(['git', 'am', '--abort'], cwd=config_dir, check=False)
    
    # 尝试使用git apply命令（方法1）
    print(f"[尝试] 使用git apply方法1应用补丁...")
    stdout, stderr, code = run_git_command(['git', 'apply', '--ignore-space-change',  patch_file], cwd=config_dir, check=False)
    if code == 0:
        # 应用成功，添加并提交更改
        print(f"[成功] 使用git apply方法1应用补丁成功")
        run_git_command(['git', 'add', '--all'], cwd=config_dir)
        commit_msg = f"应用MOD: {mod_name}"
        stdout, stderr, code = run_git_command(['git', 'commit', '-m', commit_msg], cwd=config_dir, check=False)
        if code == 0:
            return True
        else:
            print(f"[错误] 提交更改失败: {stderr}")
            return False
    
    # 方法1失败，尝试方法2
    print(f"[警告] git apply方法1应用补丁失败: {stderr}")
    
    # 尝试使用git apply命令（方法2）
    print(f"[尝试] 使用git apply方法2应用补丁...")
    stdout, stderr, code = run_git_command(['git', 'apply', '--reject', '--whitespace=fix', patch_file], cwd=config_dir, check=False)
    
    # 检查是否有.rej文件（冲突文件）
    has_reject_files = False
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith('.rej'):
                has_reject_files = True
                reject_path = os.path.join(root, file)
                print(f"[警告] 发现冲突文件: {os.path.relpath(reject_path, config_dir)}")
    
    if has_reject_files:
        print(f"[错误] 补丁应用存在冲突，无法自动解决")
        # 清理工作目录
        run_git_command(['git', 'reset', '--hard'], cwd=config_dir)
        return False
    
    # 没有冲突，添加并提交更改
    run_git_command(['git', 'add', '--all'], cwd=config_dir)
    commit_msg = f"应用MOD: {mod_name}"
    stdout, stderr, code = run_git_command(['git', 'commit', '-m', commit_msg], cwd=config_dir, check=False)
    if code == 0:
        print(f"[成功] 使用git apply方法2应用补丁成功")
        return True
    else:
        print(f"[错误] 提交更改失败: {stderr}")
        # 清理工作目录
        run_git_command(['git', 'reset', '--hard'], cwd=config_dir)
        return False

def install_mods():
    """安装MOD主函数"""
    try:
        # 获取应用程序路径
        app_path = get_application_path()
        
        # 获取游戏路径
        game_path = get_game_path()
        if not game_path:
            print("无法确定游戏路径，安装中止")
            return False
        
        # 获取配置目录
        config_dir = get_config_dir(game_path)
        
        # 准备Git环境
        if not prepare_git_environment(game_path):
            print("准备Git环境失败，安装中止")
            return False
        
        # 获取游戏版本日期
        game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
        if not os.path.exists(game_exe_path):
            print("[错误] 找不到游戏可执行文件")
            return False
        
        game_mod_time = os.path.getmtime(game_exe_path)
        game_version_date = datetime.fromtimestamp(game_mod_time).strftime("%Y%m%d")
        print(f"[信息] 当前游戏版本日期: {game_version_date}")
        
        # 创建MOD分支
        mod_branch = "mods_applied"
        stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir)
        if code != 0:
            print(f"[错误] 无法切换到主分支: {stderr}")
            return False
        
        # 检查是否已存在MOD分支，如果存在则删除
        stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
        if mod_branch in stdout:
            run_git_command(['git', 'branch', '-D', mod_branch], cwd=config_dir, check=False)
        
        # 创建新的MOD分支
        stdout, stderr, code = run_git_command(['git', 'checkout', '-b', mod_branch], cwd=config_dir)
        if code != 0:
            print(f"[错误] 无法创建MOD分支: {stderr}")
            return False
        
        # 获取Mods目录
        mods_dir = os.path.join(app_path, "Mods")
        if not os.path.exists(mods_dir):
            print("[错误] Mods目录不存在")
            return False
        
        # 遍历Mods目录
        total_count = 0
        success_count = 0
        skipped_count = 0
        
        # 按照优先级排序MOD
        mod_list = []
        for mod_name in os.listdir(mods_dir):
            mod_dir = os.path.join(mods_dir, mod_name)
            if not os.path.isdir(mod_dir):
                continue
            
            # 查找modConfig.json文件
            mod_config_file = os.path.join(mod_dir, "modConfig.json")
            if not os.path.exists(mod_config_file):
                print(f"[跳过] {mod_name} 没有modConfig.json文件")
                continue
            
            # 读取配置文件
            try:
                with open(mod_config_file, 'r', encoding='utf-8') as f:
                    mod_config = json.load(f)
            except Exception as e:
                print(f"[错误] 无法读取配置文件 {mod_config_file}: {e}")
                # 发生错误，执行还原操作
                prepare_git_environment(game_path)
                return False
            
            # 检查是否有补丁文件
            if "patchFile" not in mod_config:
                print(f"[跳过] {mod_name} 没有补丁文件")
                continue
            
            # 检查updateTo属性
            if "updateTo" in mod_config:
                update_to_date = mod_config["updateTo"]
                # 尝试将updateTo转换为标准格式（如果不是标准格式）
                if isinstance(update_to_date, str):
                    # 移除所有非数字字符
                    update_to_date = ''.join(filter(str.isdigit, update_to_date))
                    # 确保至少有8位数字（YYYYMMDD）
                    if len(update_to_date) >= 8:
                        update_to_date = update_to_date[:8]  # 只取前8位
                        # 比较日期
                        if update_to_date < game_version_date:
                            print(f"[跳过] {mod_name} 的补丁版本({update_to_date})低于当前游戏版本({game_version_date})")
                            skipped_count += 1
                            continue
            
            # 获取优先级
            priority = mod_config.get("priority", 100)  # 默认优先级为100
            
            mod_list.append({
                "name": mod_name,
                "dir": mod_dir,
                "config": mod_config,
                "priority": priority
            })
        
        # 按优先级排序（数字越小优先级越高）
        mod_list.sort(key=lambda x: x["priority"])
        
        # 应用所有MOD补丁
        for mod_info in mod_list:
            mod_name = mod_info["name"]
            mod_dir = mod_info["dir"]
            mod_config = mod_info["config"]
            
            total_count += 1
            
            # 获取补丁文件路径
            patch_file = os.path.join(mod_dir, mod_config["patchFile"])
            
            # 应用补丁
            if apply_patch(patch_file, config_dir, mod_name):
                success_count += 1
            else:
                # 补丁应用失败，执行还原操作
                print(f"[错误] 应用MOD {mod_name} 失败，安装停止")
                # prepare_git_environment(game_path)
                return False
        
        print(f"\n[完成] 共处理 {total_count} 个MOD，成功 {success_count} 个，跳过 {skipped_count} 个")
        
        if success_count > 0:
            print("\n[成功] 所有MOD已成功安装")
            return True
        else:
            print("\n[警告] 没有成功安装任何MOD")
            prepare_git_environment(game_path)
            return False
    
    except Exception as e:
        print(f"[错误] 安装过程中发生异常: {e}")
        # 发生任何异常，执行还原操作
        try:
            game_path = get_game_path()
            if game_path:
                prepare_git_environment(game_path)
        except:
            print("[错误] 还原操作失败")
        return False

def main():
    """主函数"""
    print_header("MOD安装管理工具")
    
    try:
        # 获取游戏路径
        game_path = get_game_path()
        if not game_path:
            print("无法确定游戏路径，安装中止")
            input("按任意键继续...")
            return
        
        # 安装MOD
        print("[安装阶段] 开始处理MOD文件...\n")
        if install_mods():
            print("\n[完成] MOD安装成功")
        else:
            print("\n[警告] MOD安装过程中出现问题，已执行还原操作")
    
    except Exception as e:
        print(f"\n[错误] 发生异常: {e}")
        print("[警告] 执行还原操作")
        try:
            game_path = get_game_path()
            if game_path:
                prepare_git_environment(game_path)
        except:
            print("[错误] 还原操作失败")
    
    input("按任意键继续...")

if __name__ == "__main__":
    main()
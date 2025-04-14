import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 导入公共工具
from common_utils import (
    print_header, ensure_directory, get_application_path, get_game_path,
    get_config_dir, prepare_git_environment, run_git_command
)

# 导入MOD配置检查工具
from check_mod_configs import check_mod_configs

def apply_patch(patch_file, config_dir, mod_name, mod_config):
    """应用补丁文件"""
    print(f"[应用] MOD: {mod_name}")
    
    if not os.path.exists(patch_file):
        print(f"[错误] 补丁文件不存在: {patch_file}")
        return False
    
    # 尝试修复补丁文件编码
    try:
        # 读取补丁文件内容
        with open(patch_file, 'rb') as f:
            patch_content = f.read()
        
        # 尝试检测编码并修复
        try:
            # 尝试用UTF-8解码
            patch_text = patch_content.decode('utf-8')
        except UnicodeDecodeError:
            # UTF-8解码失败，尝试用GBK或其他编码
            try:
                patch_text = patch_content.decode('gbk')
                # 转换为UTF-8
                patch_content = patch_text.encode('utf-8')
                # 创建临时补丁文件
                temp_patch_file = patch_file + ".utf8"
                with open(temp_patch_file, 'wb') as f:
                    f.write(patch_content)
                patch_file = temp_patch_file
                print(f"[信息] 已修复补丁文件编码")
            except UnicodeDecodeError:
                # 如果GBK也失败，尝试latin-1（这个编码可以解码任何字节序列）
                patch_text = patch_content.decode('latin-1')
                patch_content = patch_text.encode('utf-8')
                temp_patch_file = patch_file + ".utf8"
                with open(temp_patch_file, 'wb') as f:
                    f.write(patch_content)
                patch_file = temp_patch_file
                print(f"[信息] 已使用通用编码修复补丁文件")
    except Exception as e:
        print(f"[警告] 修复补丁文件编码时出错: {e}")
    
    # 准备提交信息
    author = mod_config.get("author", "未知作者")
    source = mod_config.get("source", "")
    version = mod_config.get("version", "")
    
    commit_msg = f"应用MOD: {mod_name}"
    if author:
        commit_msg += f"\n作者: {author}"
    if source:
        commit_msg += f"\n来源: {source}"
    if version:
        commit_msg += f"\n版本: {version}"
    
    # 首先尝试使用git am命令应用补丁
    print(f"[尝试] 使用git am应用补丁...")
    stdout, stderr, code = run_git_command(['git', 'am', '--ignore-whitespace', '--keep-cr', patch_file], cwd=config_dir, check=False)
    if code == 0:
        print(f"[成功] 使用git am应用补丁成功")
        # 修改最后一次提交的信息
        run_git_command(['git', 'commit', '--amend', '-m', commit_msg], cwd=config_dir, check=False)
        return True
    
    # git am失败，中止补丁应用
    print(f"[警告] git am应用补丁失败: {stderr}")
    run_git_command(['git', 'am', '--abort'], cwd=config_dir, check=False)
    
    # 尝试使用git apply命令（方法1）
    print(f"[尝试] 使用git apply方法1应用补丁...")
    stdout, stderr, code = run_git_command(['git', 'apply', '--ignore-whitespace', patch_file], cwd=config_dir, check=False)
    if code == 0:
        # 应用成功，添加并提交更改
        print(f"[成功] 使用git apply方法1应用补丁成功")
        run_git_command(['git', 'add', '--all'], cwd=config_dir)
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
    try:
        # 使用更宽松的选项
        stdout, stderr, code = run_git_command(['git', 'apply', '--reject', '--whitespace=fix', '--ignore-whitespace', patch_file], cwd=config_dir, check=False)
        # 确保stdout和stderr不为None
        stdout = stdout or ""
        stderr = stderr or ""
    except Exception as e:
        print(f"[警告] git apply方法2执行异常: {e}")
        stdout = ""
        stderr = str(e)
        code = 1  # 设置错误码
    
    # 检查是否有.rej文件（冲突文件）
    has_reject_files = False
    conflict_files = []
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith('.rej'):
                has_reject_files = True
                reject_path = os.path.join(root, file)
                original_file = reject_path[:-4]  # 移除.rej后缀
                rel_path = os.path.relpath(original_file, config_dir)
                conflict_files.append(rel_path)
                print(f"[警告] 发现冲突文件: {rel_path}")
    
    if has_reject_files:
        print(f"[错误] 补丁应用存在冲突，无法自动解决")
        
        # 分析冲突文件，查找可能导致冲突的MOD
        for conflict_file in conflict_files:
            print(f"\n[分析] 分析冲突文件: {conflict_file}")
            
            # 查找修改过该文件的提交
            stdout, stderr, code = run_git_command(
                ['git', 'log', '--format=%H:%s', '--', conflict_file], 
                cwd=config_dir, 
                check=False
            )
            
            if stdout and code == 0:
                commits = stdout.strip().split('\n')
                conflict_mods = []
                
                for commit in commits:
                    if ':' in commit:
                        commit_hash, commit_msg = commit.split(':', 1)
                        if commit_msg.startswith("应用MOD:"):
                            conflict_mod_name = commit_msg[5:].strip().split('\n')[0]  # 获取MOD名称，去除可能的作者信息
                            if conflict_mod_name not in conflict_mods:
                                conflict_mods.append(conflict_mod_name)
                
                if conflict_mods:
                    print(f"[提示] 以下MOD可能与当前MOD({mod_name})在文件 {conflict_file} 上存在冲突:")
                    for i, conflict_mod in enumerate(conflict_mods, 1):
                        print(f"  {i}. {conflict_mod}")
                    print("[建议] 请检查这些MOD的兼容性，或调整它们的安装顺序")
                else:
                    print(f"[信息] 未找到修改过文件 {conflict_file} 的MOD记录")
            else:
                print(f"[信息] 无法获取文件 {conflict_file} 的修改历史")
        
        # 清理工作目录
        run_git_command(['git', 'reset', '--hard'], cwd=config_dir)
        return False
    
    # 没有冲突，添加并提交更改
    run_git_command(['git', 'add', '--all'], cwd=config_dir)
    stdout, stderr, code = run_git_command(['git', 'commit', '-m', commit_msg], cwd=config_dir, check=False)
    if code == 0:
        print(f"[成功] 使用git apply方法2应用补丁成功")
        return True
    else:
        print(f"[错误] 提交更改失败: {stderr or '未知错误'}")
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
        
        # 不再调用prepare_git_environment，因为已经在check_mod_configs中完成
        # 这里可以添加一个简单的检查，确保Git环境已经准备好
        stdout, stderr, code = run_git_command(['git', 'status'], cwd=config_dir, check=False)
        if code != 0:
            print("Git环境未准备好，安装中止")
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
            if apply_patch(patch_file, config_dir, mod_name, mod_config):
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
        
        # 先检查并准备MOD配置
        print("[准备阶段] 检查MOD配置和补丁文件...")
        check_mod_configs()
        
        # 安装MOD
        print("\n[安装阶段] 开始处理MOD文件...\n")
        if install_mods():
            print("\n[完成] MOD安装成功")
        else:
            print("\n[警告] MOD安装过程中出现问题，执行还原操作")
            if game_path:
                prepare_git_environment(game_path)
    
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
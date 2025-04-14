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
    stdout, stderr, code = run_git_command(['git', 'am', '--reject', '--ignore-whitespace', '--keep-cr', patch_file], cwd=config_dir, check=False)
    if code == 0:
        print(f"[成功] 使用git am应用补丁成功")
        # 修改最后一次提交的信息
        run_git_command(['git', 'commit', '--amend', '-m', commit_msg], cwd=config_dir, check=False)
        return True
    
    # git am失败，中止补丁应用
    print(f"[警告] git am应用补丁失败: {mod_name}")
    run_git_command(['git', 'am', '--abort'], cwd=config_dir, check=False)
    
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
                conflict_files.append((rel_path, reject_path))
                
                print(f"[警告] 发现冲突文件: {rel_path}")
    
    if has_reject_files:
        print(f"[错误] 补丁应用存在冲突，无法自动解决")
        
        # 分析冲突文件，查找可能导致冲突的MOD
        conflict_analysis = {}  # 用于存储分析结果
        for rel_path, reject_path in conflict_files:
            print(f"\n[分析] 分析冲突文件: {rel_path}")
            
            # 查找修改过该文件的提交
            stdout, stderr, code = run_git_command(
                ['git', 'log', '--format=%H:%s', '--', rel_path], 
                cwd=config_dir, 
                check=False
            )
            
            conflict_mods = []
            if stdout and code == 0:
                commits = stdout.strip().split('\n')
                
                for commit in commits:
                    if ':' in commit:
                        commit_hash, commit_msg = commit.split(':', 1)
                        if commit_msg.startswith("应用MOD:"):
                            conflict_mod_name = commit_msg[5:].strip().split('\n')[0]  # 获取MOD名称，去除可能的作者信息
                            if conflict_mod_name not in conflict_mods:
                                conflict_mods.append(conflict_mod_name)
                
                if conflict_mods:
                    print(f"[提示] 以下MOD可能与当前MOD({mod_name})在文件 {rel_path} 上存在冲突:")
                    for i, conflict_mod in enumerate(conflict_mods, 1):
                        print(f"  {i}. {conflict_mod}")
                    print("[建议] 请检查这些MOD的兼容性，或调整它们的安装顺序")
                else:
                    print(f"[信息] 未找到修改过文件 {rel_path} 的MOD记录")
            else:
                print(f"[信息] 无法获取文件 {rel_path} 的修改历史")
            
            # 保存分析结果
            conflict_analysis[rel_path] = {
                'reject_path': reject_path,
                'conflict_mods': conflict_mods
            }
        
        # 完成分析后，创建冲突文件夹并复制文件
        conflict_dir = os.path.join(os.path.dirname(config_dir), "conflict_files", mod_name)
        if os.path.exists(conflict_dir):
            shutil.rmtree(conflict_dir)
        os.makedirs(conflict_dir, exist_ok=True)
        
        # 创建分析结果文件
        analysis_file = os.path.join(conflict_dir, "conflict_analysis.txt")
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write(f"MOD: {mod_name} 冲突分析\n")
            f.write("=" * 50 + "\n\n")
            
            for rel_path, info in conflict_analysis.items():
                f.write(f"文件: {rel_path}\n")
                if info['conflict_mods']:
                    f.write("可能冲突的MOD:\n")
                    for i, conflict_mod in enumerate(info['conflict_mods'], 1):
                        f.write(f"  {i}. {conflict_mod}\n")
                else:
                    f.write("未找到可能冲突的MOD\n")
                f.write("\n" + "-" * 40 + "\n\n")
        
        print(f"\n[信息] 冲突分析已保存到: {analysis_file}")
        
        # 复制冲突文件到冲突文件夹
        for rel_path, info in conflict_analysis.items():
            reject_path = info['reject_path']
            
            # 创建目标目录结构
            target_dir = os.path.join(conflict_dir, os.path.dirname(rel_path))
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制.rej文件
            target_rej = os.path.join(conflict_dir, rel_path + '.rej')
            shutil.copy2(reject_path, target_rej)
            
            # 复制原始文件
            original_file = reject_path[:-4]
            if os.path.exists(original_file):
                target_orig = os.path.join(conflict_dir, rel_path)
                shutil.copy2(original_file, target_orig)
            
            print(f"[信息] 已将冲突文件保存到: {os.path.join(conflict_dir, rel_path + '.rej')}")
        
        # 清理工作目录
        run_git_command(['git', 'reset', '--hard'], cwd=config_dir)
        # 确保移除所有未跟踪的文件，特别是.rej文件
        run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
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
        failed_count = 0
        
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
        current_branch = mod_branch
        failed_branches = []  # 用于记录失败MOD的分支
        
        for i, mod_info in enumerate(mod_list):
            mod_name = mod_info["name"]
            mod_dir = mod_info["dir"]
            mod_config = mod_info["config"]
            
            total_count += 1
            
            # 获取补丁文件路径
            patch_file = os.path.join(mod_dir, mod_config["patchFile"])
            
            # 应用补丁
            print(f"\n[应用] MOD ({i+1}/{len(mod_list)}): {mod_name}")
            
            # 在当前MOD分支上尝试应用补丁
            if apply_patch(patch_file, config_dir, mod_name, mod_config):
                success_count += 1
                print(f"[成功] MOD {mod_name} 应用成功")
            else:
                failed_count += 1
                print(f"[失败] MOD {mod_name} 应用失败，尝试在新分支上安装")
                
                # 舍弃所有未提交的更改
                run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
                
                # 从主分支切出新分支尝试安装失败的MOD
                stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir)
                if code != 0:
                    print(f"[错误] 无法切换到主分支: {stderr}")
                    # 尝试切回原MOD分支
                    run_git_command(['git', 'checkout', current_branch], cwd=config_dir, check=False)
                    continue
                
                # 创建失败MOD的专用分支，确保分支名称有效
                safe_mod_name = ''.join(c if c.isalnum() or c in '_-' else '_' for c in mod_name)
                failed_branch = f"failed_mod_{safe_mod_name}_{i}"
                
                # 检查分支是否已存在，如果存在则删除
                stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
                if failed_branch in stdout:
                    run_git_command(['git', 'branch', '-D', failed_branch], cwd=config_dir, check=False)
                
                # 创建新分支
                stdout, stderr, code = run_git_command(['git', 'checkout', '-b', failed_branch], cwd=config_dir)
                if code != 0:
                    print(f"[错误] 无法创建失败MOD分支 {failed_branch}: {stderr}")
                    # 尝试切回原MOD分支
                    run_git_command(['git', 'checkout', current_branch], cwd=config_dir, check=False)
                    continue
                
                # 在新分支上尝试应用补丁
                print(f"[尝试] 在新分支 {failed_branch} 上安装MOD: {mod_name}")
                if apply_patch(patch_file, config_dir, mod_name, mod_config):
                    print(f"[信息] MOD {mod_name} 在独立分支上安装成功")
                    print(f"[信息] 您可以稍后手动解决冲突并合并此分支")
                    failed_branches.append(failed_branch)
                else:
                    print(f"[信息] MOD {mod_name} 在独立分支上也安装失败")
                
                # 确保工作目录干净，移除所有未跟踪的文件
                print(f"[清理] 移除所有未跟踪的文件...")
                run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
                
                # 切回原MOD分支继续安装其他MOD
                stdout, stderr, code = run_git_command(['git', 'checkout', current_branch], cwd=config_dir)
                if code != 0:
                    print(f"[错误] 无法切回MOD分支 {current_branch}: {stderr}")
                    # 再次尝试清理并切换
                    run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
                    run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
                    
                    stdout, stderr, code = run_git_command(['git', 'checkout', current_branch], cwd=config_dir)
                    if code != 0:
                        # 这是一个严重错误，但我们尝试恢复
                        print(f"[错误] 再次尝试切回失败，尝试从主分支重新创建MOD分支")
                        stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir)
                        if code == 0:
                            # 重新创建MOD分支
                            if mod_branch in run_git_command(['git', 'branch'], cwd=config_dir)[0]:
                                run_git_command(['git', 'branch', '-D', mod_branch], cwd=config_dir, check=False)
                            run_git_command(['git', 'checkout', '-b', mod_branch], cwd=config_dir, check=False)
                            current_branch = mod_branch
                        else:
                            return False
        
        # 如果至少有一个MOD成功应用，确保我们在主MOD分支上
        if success_count > 0:
            # 确保我们在主MOD分支上
            stdout, stderr, code = run_git_command(['git', 'checkout', mod_branch], cwd=config_dir)
            if code != 0:
                print(f"[错误] 无法切换到主MOD分支: {stderr}")
                return False
            
            print(f"\n[完成] 共处理 {total_count} 个MOD，成功 {success_count} 个，失败 {failed_count} 个，跳过 {skipped_count} 个")
            
            # 显示失败MOD的分支信息
            if failed_count > 0:
                print("\n[信息] 以下MOD在独立分支上安装，您可以稍后手动解决冲突:")
                
                # 获取当前存在的分支列表
                stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
                existing_branches = []
                if code == 0:
                    all_branches = stdout.strip().split('\n')
                    existing_branches = [b.strip().replace('* ', '') for b in all_branches]
                
                # 检查记录的失败分支是否仍然存在
                existing_failed_branches = []
                for branch in failed_branches:
                    if branch in existing_branches:
                        existing_failed_branches.append(branch)
                    else:
                        print(f"[警告] 分支 {branch} 已不存在，可能在处理过程中被删除")
                
                # 如果没有找到任何失败分支，再次尝试从所有分支中查找
                if not existing_failed_branches:
                    existing_failed_branches = [b for b in existing_branches if b.startswith('failed_mod_')]
                    if existing_failed_branches:
                        print("[信息] 从现有分支中找到以下失败MOD分支:")
                
                # 显示失败分支
                if existing_failed_branches:
                    for i, branch in enumerate(existing_failed_branches, 1):
                        print(f"  {i}. {branch}")
                    
                    print("\n[提示] 您可以使用以下命令查看和合并这些分支:")
                    print("  git checkout <分支名>  # 切换到分支")
                    print("  git checkout mods_applied  # 切回MOD主分支")
                    print("  git merge <分支名>  # 合并分支")

                    print("[检查] 验证失败MOD分支是否存在...")
                    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
                    if code == 0:
                        existing_branches = stdout.strip().split('\n')
                        existing_branches = [b.strip().replace('* ', '') for b in existing_branches]
                        
                        for branch in failed_branches:
                            if branch not in existing_branches:
                                print(f"[警告] 失败MOD分支 {branch} 不存在，尝试恢复...")
                                # 这里可以添加恢复分支的逻辑，如果需要的话
                else:
                    print("[警告] 未找到任何失败MOD的分支，可能在处理过程中被删除")
            
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
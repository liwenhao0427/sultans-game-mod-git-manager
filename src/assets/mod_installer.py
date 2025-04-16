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
    get_config_dir, prepare_git_environment, run_git_command,
    Colors, colored_print, generate_safe_branch_name
)

# 导入MOD配置检查工具
from check_mod_configs import check_mod_configs


def apply_patch(patch_file, config_dir, mod_name, mod_config):
    """应用补丁文件"""
    colored_print(f"[应用] MOD: {mod_name}", Colors.CYAN)
    
    if not os.path.exists(patch_file):
        colored_print(f"[错误] 补丁文件不存在: {patch_file}", Colors.RED)
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
                colored_print(f"[信息] 已修复补丁文件编码", Colors.BLUE)
            except UnicodeDecodeError:
                # 如果GBK也失败，尝试latin-1（这个编码可以解码任何字节序列）
                patch_text = patch_content.decode('latin-1')
                patch_content = patch_text.encode('utf-8')
                temp_patch_file = patch_file + ".utf8"
                with open(temp_patch_file, 'wb') as f:
                    f.write(patch_content)
                patch_file = temp_patch_file
                colored_print(f"[信息] 已使用通用编码修复补丁文件", Colors.BLUE)
    except Exception as e:
        colored_print(f"[警告] 修复补丁文件编码时出错: {e}", Colors.YELLOW)
    
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
    colored_print(f"[尝试] 使用git am应用补丁...", Colors.CYAN)
    
    # 修改：添加错误处理，确保即使命令输出包含非UTF-8字符也能正常处理
    try:
        stdout, stderr, code = run_git_command(['git', 'am', '--reject', '--ignore-whitespace', '--keep-cr', patch_file], cwd=config_dir, check=False)
        if code == 0:
            colored_print(f"[成功] 使用git am应用补丁成功", Colors.GREEN)
            # 修改最后一次提交的信息
            run_git_command(['git', 'commit', '--amend', '-m', commit_msg], cwd=config_dir, check=False)
            return True
    except Exception as e:
        colored_print(f"[警告] 执行git am命令时出错: {e}", Colors.YELLOW)
        # 尝试中止可能处于中间状态的补丁应用
        run_git_command(['git', 'am', '--abort'], cwd=config_dir, check=False)
        code = 1  # 设置错误代码，表示失败
    
    # git am失败，中止补丁应用
    colored_print(f"[警告] git am应用补丁失败: {mod_name}", Colors.YELLOW)
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
                
                colored_print(f"[警告] 发现冲突文件: {rel_path}", Colors.YELLOW)
    
    if has_reject_files:
        colored_print(f"[错误] 补丁应用存在冲突，无法自动解决", Colors.RED)
        
        # 分析冲突文件，查找可能导致冲突的MOD
        conflict_analysis = {}  # 用于存储分析结果
        for rel_path, reject_path in conflict_files:
            colored_print(f"\n[分析] 分析冲突文件: {rel_path}", Colors.MAGENTA)
            
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
                    colored_print(f"[提示] 以下MOD可能与当前MOD({mod_name})在文件 {rel_path} 上存在冲突:", Colors.YELLOW)
                    for i, conflict_mod in enumerate(conflict_mods, 1):
                        colored_print(f"  {i}. {conflict_mod}", Colors.YELLOW)
                    colored_print("[建议] 请检查这些MOD的兼容性，或调整它们的安装顺序", Colors.YELLOW)
                else:
                    colored_print(f"[信息] 未找到修改过文件 {rel_path} 的MOD记录", Colors.BLUE)
            else:
                colored_print(f"[信息] 无法获取文件 {rel_path} 的修改历史", Colors.BLUE)
            
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
        
        colored_print(f"\n[信息] 冲突分析已保存到: {analysis_file}", Colors.BLUE)
        
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
            colored_print("无法确定游戏路径，安装中止", Colors.RED)
            return False
        
        # 获取配置目录
        config_dir = get_config_dir(game_path)
        
        # 不再调用prepare_git_environment，因为已经在check_mod_configs中完成
        # 这里可以添加一个简单的检查，确保Git环境已经准备好
        stdout, stderr, code = run_git_command(['git', 'status'], cwd=config_dir, check=False)
        if code != 0:
            colored_print("Git环境未准备好，安装中止", Colors.RED)
            return False
        
        # 获取游戏版本日期
        game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
        if not os.path.exists(game_exe_path):
            colored_print("[错误] 找不到游戏可执行文件", Colors.RED)
            return False
        
        game_mod_time = os.path.getmtime(game_exe_path)
        game_version_date = datetime.fromtimestamp(game_mod_time).strftime("%Y%m%d")
        colored_print(f"[信息] 当前游戏版本日期: {game_version_date}", Colors.BLUE)
        
        # 切换到master分支
        stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir)
        if code != 0:
            colored_print(f"[错误] 无法切换到主分支: {stderr}", Colors.RED)
            return False
        
        # 获取所有分支
        stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
        if code != 0:
            colored_print(f"[错误] 无法获取分支列表: {stderr}", Colors.RED)
            return False
        
        all_branches = stdout.strip().split('\n')
        existing_branches = [b.strip().replace('* ', '') for b in all_branches if b.strip()]
        
        # 删除所有failed_mod分支
        colored_print("[清理] 删除所有失败MOD分支...", Colors.BLUE)
        failed_branches_count = 0
        for branch in existing_branches:
            if branch.startswith('failed_mod_'):
                run_git_command(['git', 'branch', '-D', branch], cwd=config_dir, check=False)
                failed_branches_count += 1
        
        if failed_branches_count > 0:
            colored_print(f"[信息] 已删除 {failed_branches_count} 个失败MOD分支", Colors.BLUE)
        
        # 创建MOD分支
        mod_branch = "mods_applied"
        
        # 检查是否已存在MOD分支，如果存在则删除
        if mod_branch in existing_branches:
            run_git_command(['git', 'branch', '-D', mod_branch], cwd=config_dir, check=False)
        
        # 创建新的MOD分支
        stdout, stderr, code = run_git_command(['git', 'checkout', '-b', mod_branch], cwd=config_dir)
        if code != 0:
            colored_print(f"[错误] 无法创建MOD分支: {stderr}", Colors.RED)
            return False
        
        # 获取Mods目录
        mods_dir = os.path.join(app_path, "Mods")
        if not os.path.exists(mods_dir):
            colored_print("[错误] Mods目录不存在", Colors.RED)
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
                colored_print(f"[跳过] {mod_name} 没有modConfig.json文件", Colors.YELLOW)
                continue
            
            # 读取配置文件
            try:
                with open(mod_config_file, 'r', encoding='utf-8') as f:
                    mod_config = json.load(f)
            except Exception as e:
                colored_print(f"[错误] 无法读取配置文件 {mod_config_file}: {e}", Colors.RED)
                # 发生错误，执行还原操作
                prepare_git_environment(game_path)
                return False
            
            # 检查是否有补丁文件
            if "patchFile" not in mod_config:
                colored_print(f"[跳过] {mod_name} 没有补丁文件", Colors.YELLOW)
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
                            colored_print(f"[跳过] {mod_name} 的补丁版本({update_to_date})低于当前游戏版本({game_version_date})", Colors.YELLOW)
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
        failed_mod_sources = {}  # 用于记录失败MOD分支的来源，是否从mod分支签出
        
        # 重新获取所有分支（可能在前面的操作中有变化）
        stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
        if code == 0:
            all_branches = stdout.strip().split('\n')
            existing_branches = [b.strip().replace('* ', '') for b in all_branches if b.strip()]
        
        # 创建MOD名称到分支名称的映射
        mod_branch_map = {}
        for branch in existing_branches:
            # 查找所有以mod_开头的分支
            if branch.startswith('mod_'):
                # 尝试从分支名中提取MOD名称
                mod_branch_map[branch] = branch[4:]  # 移除'mod_'前缀
        
        for i, mod_info in enumerate(mod_list):
            mod_name = mod_info["name"]
            mod_dir = mod_info["dir"]
            mod_config = mod_info["config"]
            
            total_count += 1
            
            # 获取补丁文件路径
            patch_file = os.path.join(mod_dir, mod_config["patchFile"])
            
            # 应用补丁
            colored_print(f"\n[应用] MOD ({i+1}/{len(mod_list)}): {mod_name}", Colors.CYAN + Colors.BOLD)
            
            # 确保我们在主MOD分支上开始安装
            stdout, stderr, code = run_git_command(['git', 'checkout', current_branch], cwd=config_dir, check=False)
            if code != 0:
                colored_print(f"[警告] 无法切换到主MOD分支 {current_branch}，尝试恢复...", Colors.YELLOW)
                # 尝试切换到master分支并重新创建MOD分支
                run_git_command(['git', 'checkout', 'master'], cwd=config_dir, check=False)
                if mod_branch in run_git_command(['git', 'branch'], cwd=config_dir)[0]:
                    run_git_command(['git', 'branch', '-D', mod_branch], cwd=config_dir, check=False)
                run_git_command(['git', 'checkout', '-b', mod_branch], cwd=config_dir, check=False)
                current_branch = mod_branch
            
            # 在当前MOD分支上尝试应用补丁
            if apply_patch(patch_file, config_dir, mod_name, mod_config):
                success_count += 1
                colored_print(f"[成功] MOD {mod_name} 应用成功", Colors.GREEN)
            else:
                failed_count += 1
                colored_print(f"[失败] MOD {mod_name} 应用失败，尝试在新分支上安装", Colors.RED)
                
                # 舍弃所有未提交的更改
                run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
                
                # 从主分支切出新分支尝试安装失败的MOD
                stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir)
                if code != 0:
                    colored_print(f"[错误] 无法切换到主分支: {stderr}", Colors.RED)
                    # 尝试切回原MOD分支
                    run_git_command(['git', 'checkout', current_branch], cwd=config_dir, check=False)
                    continue
                
                # 创建失败MOD的专用分支，确保分支名称有效
                safe_mod_name = generate_safe_branch_name(mod_name)
                failed_branch = f"failed_mod_{safe_mod_name}"
                
                # 查找是否有对应的mod分支
                mod_branch_found = None
                for branch, branch_mod_name in mod_branch_map.items():
                    if safe_mod_name == branch_mod_name or safe_mod_name in branch_mod_name or branch_mod_name in safe_mod_name:
                        mod_branch_found = branch
                        break
                
                # 记录失败MOD的来源
                from_mod_branch = False
                
                if mod_branch_found:
                    colored_print(f"[信息] 找到对应的MOD分支: {mod_branch_found}", Colors.BLUE)
                    # 从mod分支签出作为新的failed_mod分支
                    stdout, stderr, code = run_git_command(['git', 'checkout', mod_branch_found], cwd=config_dir)
                    if code == 0:
                        # 创建新的失败分支
                        stdout, stderr, code = run_git_command(['git', 'checkout', '-b', failed_branch], cwd=config_dir)
                        if code == 0:
                            colored_print(f"[信息] 从MOD分支 {mod_branch_found} 创建失败分支 {failed_branch}", Colors.BLUE)
                            from_mod_branch = True
                            
                            # 检查该分支是否已经应用了该MOD
                            stdout, stderr, code = run_git_command(['git', 'log', '--grep', f"应用MOD: {mod_name}"], cwd=config_dir, check=False)
                            if stdout and "应用MOD:" in stdout:
                                colored_print(f"[信息] 分支已经应用了MOD {mod_name}，尝试从master合并代码", Colors.BLUE)
                                
                                # 从master合并代码
                                stdout, stderr, code = run_git_command(['git', 'merge', 'master', '--no-commit'], cwd=config_dir, check=False)
                                if code == 0:
                                    colored_print(f"[信息] 成功从master合并代码到 {failed_branch}", Colors.GREEN)
                                    failed_branches.append(failed_branch)
                                    failed_mod_sources[failed_branch] = from_mod_branch
                                    continue
                                else:
                                    colored_print(f"[警告] 从master合并代码失败: {stderr}", Colors.YELLOW)
                                    # 中止合并
                                    run_git_command(['git', 'merge', '--abort'], cwd=config_dir, check=False)
                        else:
                            colored_print(f"[错误] 无法创建失败分支 {failed_branch}: {stderr}", Colors.RED)
                            # 切回master
                            run_git_command(['git', 'checkout', 'master'], cwd=config_dir, check=False)
                    else:
                        colored_print(f"[错误] 无法切换到MOD分支 {mod_branch_found}: {stderr}", Colors.RED)
                
                # 如果没有找到对应的mod分支或者上述操作失败，则从master创建新分支
                stdout, stderr, code = run_git_command(['git', 'checkout', 'master'], cwd=config_dir)
                if code != 0:
                    colored_print(f"[错误] 无法切换到主分支: {stderr}", Colors.RED)
                    # 尝试切回原MOD分支
                    run_git_command(['git', 'checkout', current_branch], cwd=config_dir, check=False)
                    continue
                
                # 创建新分支
                stdout, stderr, code = run_git_command(['git', 'checkout', '-b', failed_branch], cwd=config_dir)
                if code != 0:
                    colored_print(f"[错误] 无法创建失败MOD分支 {failed_branch}: {stderr}", Colors.RED)
                    # 尝试切回原MOD分支
                    run_git_command(['git', 'checkout', current_branch], cwd=config_dir, check=False)
                    continue
                
                # 在新分支上尝试应用补丁
                colored_print(f"[尝试] 在新分支 {failed_branch} 上安装MOD: {mod_name}", Colors.CYAN)
                if apply_patch(patch_file, config_dir, mod_name, mod_config):
                    colored_print(f"[信息] MOD {mod_name} 在独立分支上安装成功", Colors.GREEN)
                    colored_print(f"[信息] 您可以稍后手动解决冲突并合并此分支", Colors.BLUE)
                    failed_branches.append(failed_branch)
                    failed_mod_sources[failed_branch] = from_mod_branch
                else:
                    colored_print(f"[信息] MOD {mod_name} 在独立分支上也安装失败", Colors.RED)
                
                # 确保工作目录干净，移除所有未跟踪的文件
                colored_print(f"[清理] 移除所有未跟踪的文件...", Colors.BLUE)
                run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
                
                # 切回原MOD分支继续安装其他MOD
                stdout, stderr, code = run_git_command(['git', 'checkout', current_branch], cwd=config_dir)
                if code != 0:
                    colored_print(f"[错误] 无法切回MOD分支 {current_branch}: {stderr}", Colors.RED)
                    # 再次尝试清理并切换
                    run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
                    run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
                    
                    stdout, stderr, code = run_git_command(['git', 'checkout', current_branch], cwd=config_dir)
                    if code != 0:
                        # 这是一个严重错误，但我们尝试恢复
                        colored_print(f"[错误] 再次尝试切回失败，尝试从主分支重新创建MOD分支", Colors.RED)
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
                colored_print(f"[错误] 无法切换到主MOD分支: {stderr}", Colors.RED)
                return False
            
            colored_print(f"\n[完成] 共处理 {total_count} 个MOD，成功 {success_count} 个，失败 {failed_count} 个，跳过 {skipped_count} 个", Colors.GREEN + Colors.BOLD)
            
            # 显示失败MOD的分支信息
            if failed_count > 0:
                colored_print("\n[信息] 以下MOD在独立分支上安装，您可以稍后手动解决冲突:", Colors.YELLOW)
                
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
                        colored_print(f"[警告] 分支 {branch} 已不存在，可能在处理过程中被删除", Colors.YELLOW)
                
                # 如果没有找到任何失败分支，再次尝试从所有分支中查找
                if not existing_failed_branches:
                    existing_failed_branches = [b for b in existing_branches if b.startswith('failed_mod_')]
                    if existing_failed_branches:
                        colored_print("[信息] 从现有分支中找到以下失败MOD分支:", Colors.BLUE)
                
                # 显示失败分支
                if existing_failed_branches:
                    for i, branch in enumerate(existing_failed_branches, 1):
                        colored_print(f"  {i}. {branch}", Colors.MAGENTA)
                    
                    # 为不是从mod分支签出的failed_mod分支创建对应的mod分支
                    colored_print("\n[处理] 为失败MOD创建对应的mod分支...", Colors.BLUE)
                    for branch in existing_failed_branches:
                        # 检查是否是从mod分支签出的
                        if branch in failed_mod_sources and not failed_mod_sources[branch]:
                            # 提取MOD名称
                            mod_name = branch.replace('failed_mod_', '', 1)
                            mod_branch_name = f"mod_{mod_name}"
                            
                            # 检查mod分支是否已存在
                            if mod_branch_name in existing_branches:
                                colored_print(f"[跳过] MOD分支 {mod_branch_name} 已存在", Colors.BLUE)
                                continue
                            
                            # 切换到失败分支
                            stdout, stderr, code = run_git_command(['git', 'checkout', branch], cwd=config_dir)
                            if code == 0:
                                # 创建mod分支
                                stdout, stderr, code = run_git_command(['git', 'checkout', '-b', mod_branch_name], cwd=config_dir)
                                if code == 0:
                                    colored_print(f"[成功] 从失败分支 {branch} 创建MOD分支 {mod_branch_name}", Colors.GREEN)
                                else:
                                    colored_print(f"[错误] 无法创建MOD分支 {mod_branch_name}: {stderr}", Colors.RED)
                            else:
                                colored_print(f"[错误] 无法切换到失败分支 {branch}: {stderr}", Colors.RED)
                    
                    # 切回主MOD分支
                    run_git_command(['git', 'checkout', mod_branch], cwd=config_dir, check=False)
                    
                    colored_print("\n[提示] 您可以使用以下命令查看和合并这些分支:", Colors.CYAN)
                    colored_print("  git checkout <分支名>  # 切换到分支", Colors.CYAN)
                    colored_print("  git checkout mods_applied  # 切回MOD主分支", Colors.CYAN)
                    colored_print("  git merge <分支名>  # 合并分支", Colors.CYAN)

                    colored_print("[检查] 验证失败MOD分支是否存在...", Colors.BLUE)
                    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
                    if code == 0:
                        existing_branches = stdout.strip().split('\n')
                        existing_branches = [b.strip().replace('* ', '') for b in existing_branches]
                        
                        for branch in failed_branches:
                            if branch not in existing_branches:
                                colored_print(f"[警告] 失败MOD分支 {branch} 不存在，尝试恢复...", Colors.YELLOW)
                else:
                    colored_print("[警告] 未找到任何失败MOD的分支，可能在处理过程中被删除", Colors.YELLOW)
            
            
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_branch = f"history_{current_date}"
            
            # 清理未提交的更改
            run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
            
            # 创建历史版本分支
            colored_print(f"\n[历史版本] 正在创建历史版本分支: {history_branch}", Colors.BLUE)
            stdout, stderr, code = run_git_command(['git', 'checkout', '-b', history_branch], cwd=config_dir)
            if code == 0:
                # 添加说明注释
                commit_msg = f"历史版本 {current_date}\n\n"
                commit_msg += f"成功安装MOD数量: {success_count}\n"
                commit_msg += f"跳过MOD数量: {skipped_count}\n"
                commit_msg += f"失败MOD数量: {failed_count}\n"
                
                # 如果有失败的MOD，添加到注释中
                if failed_count > 0 and existing_failed_branches:
                    commit_msg += "\n失败MOD分支:\n"
                    for branch in existing_failed_branches:
                        commit_msg += f"- {branch}\n"
                
                # 创建空提交，添加说明信息
                stdout, stderr, code = run_git_command(['git', 'commit', '--allow-empty', '-m', commit_msg], cwd=config_dir)
                if code == 0:
                    colored_print(f"[成功] 已创建历史版本分支: {history_branch}", Colors.GREEN)
                else:
                    colored_print(f"[警告] 创建历史版本提交失败: {stderr}", Colors.YELLOW)
                
                # 切回MOD分支
                run_git_command(['git', 'checkout', mod_branch], cwd=config_dir, check=False)
            else:
                colored_print(f"[警告] 创建历史版本分支失败: {stderr}", Colors.YELLOW)
            
            return True
        else:
            colored_print("\n[警告] 没有成功安装任何MOD", Colors.YELLOW)
            prepare_git_environment(game_path)
            return False
            
    except Exception as e:
        colored_print(f"[错误] 安装过程中发生异常: {e}", Colors.RED)
        # 发生任何异常，执行还原操作
        try:
            game_path = get_game_path()
            if game_path:
                prepare_git_environment(game_path)
        except:
            colored_print("[错误] 还原操作失败", Colors.RED)
        return False

def main():
    """主函数"""
    print_header("MOD安装管理工具")
    
    # 初始化安装状态变量
    install_success = True

    try:
        # 获取游戏路径
        game_path = get_game_path()
        if not game_path:
            colored_print("无法确定游戏路径，安装中止", Colors.RED)
            input("按任意键继续...")
            return
        
        # 先检查并准备MOD配置
        colored_print("[准备阶段] 检查MOD配置和补丁文件...", Colors.CYAN)
        check_mod_configs()
        
        # 安装MOD
        colored_print("\n[安装阶段] 开始处理MOD文件...\n", Colors.CYAN)
        if install_mods():
            colored_print("\n[完成] MOD安装成功", Colors.GREEN + Colors.BOLD)
        else:
            colored_print("\n[警告] MOD安装过程中出现问题，执行还原操作", Colors.YELLOW)
            if game_path:
                prepare_git_environment(game_path)
    
    except Exception as e:
        colored_print(f"\n[错误] 发生异常: {e}", Colors.RED)
        colored_print("[警告] 执行还原操作", Colors.YELLOW)
        try:
            game_path = get_game_path()
            if game_path:
                prepare_git_environment(game_path)
        except:
            colored_print("[错误] 还原操作失败", Colors.RED)
        install_success = False
    
    # 询问用户是否要启动Git工具
    if install_success:
        colored_print("\n[提示] MOD安装已完成，是否要启动Git操作工具？", Colors.CYAN)
        choice = input("请输入选择 (y/n): ").strip().lower()
        if choice == 'y':
            colored_print("\n[启动] 正在启动Git操作工具...", Colors.BLUE)
            # 导入git_tools模块
            try:
                import git_tools
                git_tools.main()
            except ImportError:
                colored_print("[错误] 无法导入Git工具模块", Colors.RED)
            except Exception as e:
                colored_print(f"[错误] 启动Git工具时发生错误: {e}", Colors.RED)

if __name__ == "__main__":
    main()

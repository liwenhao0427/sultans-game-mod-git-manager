import os
import sys
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

# 导入公共工具
from common_utils import (
    get_application_path, get_game_path, get_config_dir, 
    run_git_command, prepare_git_environment, 
    Colors, colored_print, print_header, show_confirm_dialog
)

def open_directory(path):
    """打开指定目录"""
    if os.path.exists(path):
        colored_print(f"[打开] 正在打开目录: {path}", Colors.BLUE)
        # 使用系统默认文件管理器打开目录
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])
        return True
    else:
        colored_print(f"[错误] 目录不存在: {path}", Colors.RED)
        return False

def get_save_data_dir():
    """获取游戏存档目录"""
    # 获取用户主目录
    user_profile = os.environ.get('USERPROFILE')
    if not user_profile:
        colored_print("[错误] 无法获取用户主目录", Colors.RED)
        return None
    
    # 构建存档目录路径
    save_data_dir = os.path.join(user_profile, "AppData", "LocalLow", "DoubleCross", "SultansGame", "SAVEDATA")
    
    if not os.path.exists(save_data_dir):
        colored_print(f"[警告] 存档目录不存在: {save_data_dir}", Colors.YELLOW)
        # 尝试创建目录
        try:
            os.makedirs(save_data_dir, exist_ok=True)
            colored_print(f"[信息] 已创建存档目录: {save_data_dir}", Colors.GREEN)
        except Exception as e:
            colored_print(f"[错误] 无法创建存档目录: {e}", Colors.RED)
            return None
    
    return save_data_dir

def get_conflict_dir(game_path):
    """获取冲突文件目录"""
    conflict_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "conflict_files")
    if not os.path.exists(conflict_dir):
        colored_print(f"[信息] 冲突目录不存在，将创建: {conflict_dir}", Colors.BLUE)
        try:
            os.makedirs(conflict_dir, exist_ok=True)
        except Exception as e:
            colored_print(f"[错误] 无法创建冲突目录: {e}", Colors.RED)
            return None
    return conflict_dir

def switch_to_branch(config_dir, branch_name):
    """切换到指定分支"""
    # 检查分支是否存在
    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法获取分支列表: {stderr}", Colors.RED)
        return False
    
    existing_branches = [b.strip().replace('* ', '') for b in stdout.strip().split('\n') if b.strip()]
    
    if branch_name not in existing_branches:
        colored_print(f"[错误] 分支 {branch_name} 不存在", Colors.RED)
        return False
    
    # 清理工作区
    run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
    run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
    
    # 切换分支
    stdout, stderr, code = run_git_command(['git', 'checkout', branch_name], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法切换到分支 {branch_name}: {stderr}", Colors.RED)
        return False
    
    colored_print(f"[成功] 已切换到分支: {branch_name}", Colors.GREEN)
    return True

def list_history_branches(config_dir):
    """列出所有历史版本分支"""
    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法获取分支列表: {stderr}", Colors.RED)
        return []
    
    all_branches = stdout.strip().split('\n')
    history_branches = []
    
    for branch in all_branches:
        branch = branch.strip().replace('* ', '')
        if branch.startswith('history_'):
            # 获取分支的提交信息
            stdout, stderr, code = run_git_command(['git', 'log', '-1', '--pretty=format:%s', branch], cwd=config_dir)
            commit_msg = stdout.strip() if code == 0 else "未知"
            
            # 从分支名中提取日期
            date_str = branch.replace('history_', '')
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_date = date_str
            
            history_branches.append({
                'name': branch,
                'date': formatted_date,
                'message': commit_msg
            })
    
    # 按日期排序，最新的在前
    history_branches.sort(key=lambda x: x['name'], reverse=True)
    return history_branches

def list_failed_mod_branches(config_dir):
    """列出所有失败MOD分支"""
    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法获取分支列表: {stderr}", Colors.RED)
        return []
    
    all_branches = stdout.strip().split('\n')
    failed_branches = []
    
    for branch in all_branches:
        branch = branch.strip().replace('* ', '')
        if branch.startswith('failed_mod_'):
            # 获取分支的提交信息
            stdout, stderr, code = run_git_command(['git', 'log', '-1', '--pretty=format:%s', branch], cwd=config_dir)
            commit_msg = stdout.strip() if code == 0 else "未知"
            
            # 从分支名中提取MOD名称
            mod_name = branch.replace('failed_mod_', '')
            
            failed_branches.append({
                'name': branch,
                'mod_name': mod_name,
                'message': commit_msg
            })
    
    # 按MOD名称排序
    failed_branches.sort(key=lambda x: x['mod_name'])
    return failed_branches

def try_merge_failed_mod(config_dir, failed_branch):
    """尝试合并失败的MOD分支"""
    # 获取当前分支
    stdout, stderr, code = run_git_command(['git', 'branch', '--show-current'], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法获取当前分支: {stderr}", Colors.RED)
        return False
    
    current_branch = stdout.strip()
    
    # 检查失败分支是否存在
    stdout, stderr, code = run_git_command(['git', 'branch'], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法获取分支列表: {stderr}", Colors.RED)
        return False
    
    existing_branches = [b.strip().replace('* ', '') for b in stdout.strip().split('\n') if b.strip()]
    
    if failed_branch not in existing_branches:
        colored_print(f"[错误] 分支 {failed_branch} 不存在", Colors.RED)
        return False
    
    # 清理工作区
    run_git_command(['git', 'reset', '--hard'], cwd=config_dir, check=False)
    run_git_command(['git', 'clean', '-fd'], cwd=config_dir, check=False)
    
    # 尝试合并
    colored_print(f"[合并] 正在尝试将 {failed_branch} 合并到 {current_branch}", Colors.BLUE)
    stdout, stderr, code = run_git_command(['git', 'merge', failed_branch], cwd=config_dir, check=False)
    
    if code == 0:
        colored_print(f"[成功] 已成功合并分支 {failed_branch}", Colors.GREEN)
        return True
    else:
        colored_print(f"[冲突] 合并分支 {failed_branch} 时发生冲突: {stderr}", Colors.YELLOW)
        colored_print("[提示] 您需要手动解决冲突，然后执行以下命令:", Colors.CYAN)
        colored_print("  git add .", Colors.CYAN)
        colored_print("  git commit -m \"解决冲突并合并分支\"", Colors.CYAN)
        
        # 询问是否中止合并
        if show_confirm_dialog("中止合并", "是否中止合并操作？"):
            run_git_command(['git', 'merge', '--abort'], cwd=config_dir, check=False)
            colored_print("[信息] 已中止合并操作", Colors.BLUE)
            return False
        else:
            colored_print("[信息] 请手动解决冲突后继续", Colors.BLUE)
            return False

def create_backup_branch(config_dir):
    """创建当前状态的备份分支"""
    # 获取当前分支
    stdout, stderr, code = run_git_command(['git', 'branch', '--show-current'], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法获取当前分支: {stderr}", Colors.RED)
        return False
    
    current_branch = stdout.strip()
    
    # 创建备份分支
    backup_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_branch = f"backup_{current_branch}_{backup_date}"
    
    stdout, stderr, code = run_git_command(['git', 'checkout', '-b', backup_branch], cwd=config_dir)
    if code != 0:
        colored_print(f"[错误] 无法创建备份分支: {stderr}", Colors.RED)
        return False
    
    colored_print(f"[成功] 已创建备份分支: {backup_branch}", Colors.GREEN)
    
    # 切回原分支
    stdout, stderr, code = run_git_command(['git', 'checkout', current_branch], cwd=config_dir)
    if code != 0:
        colored_print(f"[警告] 无法切回原分支 {current_branch}: {stderr}", Colors.YELLOW)
    
    return backup_branch

def run_game(game_path):
    """运行游戏"""
    game_exe = os.path.join(game_path, "Sultan's Game.exe")
    if os.path.exists(game_exe):
        colored_print(f"[启动] 正在启动游戏: {game_exe}", Colors.BLUE)
        try:
            # 使用subprocess启动游戏，不等待游戏结束
            subprocess.Popen(game_exe, cwd=game_path)
            return True
        except Exception as e:
            colored_print(f"[错误] 启动游戏失败: {e}", Colors.RED)
            return False
    else:
        colored_print(f"[错误] 游戏可执行文件不存在: {game_exe}", Colors.RED)
        return False

def restore_from_gitee_repo(config_dir, game_path):
    """从Gitee仓库恢复游戏配置"""
    import shutil
    from datetime import datetime
    
    colored_print("[警告] 此操作将使用Gitee仓库中的配置文件替换您当前的游戏配置", Colors.YELLOW)
    colored_print("[警告] 您当前的所有MOD和自定义配置将被备份，但不会应用到新配置", Colors.YELLOW)
    colored_print("[提示] 该选项可用于修复之前初始化有问题的配置，类似Steam验证游戏完整性", Colors.CYAN)
    colored_print("[提示] 其原理是使用作者的开源仓库配置替代本地配置，因此可能不是最新", Colors.CYAN)
    colored_print("[提示] 如果遇到问题，请使用 14.从备份还原游戏配置选项", Colors.CYAN)
    
    if not show_confirm_dialog("确认操作", "确定要继续吗？"):
        colored_print("[信息] 操作已取消", Colors.BLUE)
        return False
    
    # 在配置目录的父目录中创建工作目录，而不是使用系统临时目录
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    parent_dir = os.path.dirname(config_dir)
    work_dir = os.path.join(parent_dir, f"gitee_work_{backup_time}")
    
    colored_print(f"[信息] 创建工作目录: {work_dir}", Colors.BLUE)
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # 备份当前配置
        backup_dir = os.path.join(parent_dir, f"config_backup_{backup_time}")
        
        colored_print(f"[备份] 正在备份当前配置到: {backup_dir}", Colors.BLUE)
        shutil.copytree(config_dir, backup_dir)
        colored_print("[备份] 备份完成", Colors.GREEN)
        
        # 克隆Gitee仓库
        colored_print("[下载] 正在从Gitee克隆仓库...", Colors.BLUE)
        gitee_url = "https://gitee.com/notnow/sultans-game-config.git"
        
        result = subprocess.run(
            ['git', 'clone', gitee_url, work_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            colored_print(f"[错误] 克隆仓库失败: {result.stderr}", Colors.RED)
            return False
        
        colored_print("[下载] 仓库克隆成功", Colors.GREEN)
        
        # 重命名当前配置目录
        old_config_dir = os.path.join(parent_dir, f"config_old_{backup_time}")
        colored_print(f"[信息] 重命名当前配置目录: {config_dir} -> {old_config_dir}", Colors.BLUE)
        os.rename(config_dir, old_config_dir)
        
        # 复制仓库内容到配置目录
        repo_config_dir = os.path.join(work_dir, "config")
        if not os.path.exists(repo_config_dir):
            repo_config_dir = work_dir  # 如果仓库根目录就是配置目录
        
        colored_print(f"[信息] 复制仓库配置到游戏目录: {repo_config_dir} -> {config_dir}", Colors.BLUE)
        shutil.copytree(repo_config_dir, config_dir)
        
        colored_print("[成功] 游戏配置已替换为Gitee仓库中的配置", Colors.GREEN)
        colored_print(f"[信息] 原配置已备份到: {backup_dir}", Colors.BLUE)
        colored_print(f"[信息] 原配置目录已重命名为: {old_config_dir}", Colors.BLUE)
        
        # 初始化新的Git仓库
        colored_print("[Git] 正在初始化新的Git仓库...", Colors.BLUE)
        from common_utils import init_git_repo
        if init_git_repo(config_dir):
            colored_print("[Git] 新的Git仓库初始化成功", Colors.GREEN)
            return True
        else:
            colored_print("[警告] 新的Git仓库初始化失败，但配置文件已替换", Colors.YELLOW)
            return False
            
    except Exception as e:
        colored_print(f"[错误] 恢复过程中出错: {e}", Colors.RED)
        return False
    finally:
        # 清理工作目录
        try:
            # 先尝试删除.git目录，这通常是导致权限问题的原因
            git_dir = os.path.join(work_dir, ".git")
            if os.path.exists(git_dir):
                for root, dirs, files in os.walk(git_dir, topdown=False):
                    for name in files:
                        try:
                            os.chmod(os.path.join(root, name), 0o777)  # 修改文件权限
                            os.remove(os.path.join(root, name))
                        except:
                            pass
                    for name in dirs:
                        try:
                            os.chmod(os.path.join(root, name), 0o777)  # 修改目录权限
                            os.rmdir(os.path.join(root, name))
                        except:
                            pass
            
            # 然后尝试删除整个工作目录
            shutil.rmtree(work_dir, ignore_errors=True)
            colored_print("[清理] 工作目录已删除", Colors.BLUE)
        except Exception as e:
            colored_print(f"[警告] 无法完全删除工作目录: {e}", Colors.YELLOW)
            colored_print(f"[提示] 您可以稍后手动删除此目录: {work_dir}", Colors.CYAN)

            
def restore_from_backup_config(config_dir, game_path):
    """从备份恢复游戏配置"""
    import os
    import shutil
    from datetime import datetime
    
    # 查找备份目录
    parent_dir = os.path.dirname(config_dir)
    backup_dirs = []
    old_dirs = []
    
    for item in os.listdir(parent_dir):
        full_path = os.path.join(parent_dir, item)
        if os.path.isdir(full_path):
            if item.startswith("config_backup_"):
                backup_time = item.replace("config_backup_", "")
                backup_dirs.append({"path": full_path, "time": backup_time, "type": "backup"})
            elif item.startswith("config_old_"):
                old_time = item.replace("config_old_", "")
                old_dirs.append({"path": full_path, "time": old_time, "type": "old"})
    
    # 合并并按时间排序
    all_dirs = backup_dirs + old_dirs
    all_dirs.sort(key=lambda x: x["time"], reverse=True)
    
    if not all_dirs:
        colored_print("[错误] 未找到任何备份或旧配置目录", Colors.RED)
        return False
    
    # 显示可用的备份
    colored_print("\n可用的备份配置:", Colors.BLUE)
    colored_print("=" * 80, Colors.CYAN)
    colored_print("  序号  |     类型     |     创建时间     |     备份路径", Colors.CYAN)
    colored_print("=" * 80, Colors.CYAN)
    
    for i, dir_info in enumerate(all_dirs, 1):
        try:
            time_str = datetime.strptime(dir_info["time"], "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = dir_info["time"]
        
        # 根据类型提供更详细的描述
        if dir_info["type"] == "backup":
            type_desc = "自动备份"
            if "before_restore" in dir_info["path"]:
                type_desc = "还原前备份"
        else:
            type_desc = "旧配置(替换前)"
        
        # 格式化显示，对齐列
        colored_print(f"  {i:2d}    | {type_desc:12s} | {time_str:16s} | {dir_info['path']}", 
                     Colors.CYAN if i % 2 == 0 else Colors.BLUE)
    
    colored_print("=" * 80, Colors.CYAN)
    colored_print("[说明] 自动备份: 系统自动创建的备份", Colors.GREEN)
    colored_print("[说明] 还原前备份: 在执行还原操作前创建的备份", Colors.GREEN)
    colored_print("[说明] 旧配置(替换前): 在替换配置前，原始配置的备份", Colors.GREEN)
    
    # 用户选择
    choice = input("\n请选择要还原的备份编号 (0取消): ")
    if choice == "0" or not choice.strip():
        colored_print("[信息] 操作已取消", Colors.BLUE)
        return False
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(all_dirs):
            selected_dir = all_dirs[index]
        else:
            colored_print("[错误] 无效的选项", Colors.RED)
            return False
    except ValueError:
        colored_print("[错误] 请输入有效的数字", Colors.RED)
        return False
    
    # 确认还原
    colored_print(f"[警告] 您将使用 {selected_dir['path']} 替换当前配置", Colors.YELLOW)
    colored_print("[警告] 当前的所有配置将被备份，但可能会丢失最近的更改", Colors.YELLOW)
    
    if not show_confirm_dialog("确认还原", "确定要继续吗？"):
        colored_print("[信息] 操作已取消", Colors.BLUE)
        return False
    
    try:
        # 备份当前配置
        backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(parent_dir, f"config_backup_before_restore_{backup_time}")
        
        colored_print(f"[备份] 正在备份当前配置到: {backup_dir}", Colors.BLUE)
        shutil.copytree(config_dir, backup_dir)
        colored_print("[备份] 备份完成", Colors.GREEN)
        
        # 重命名当前配置目录
        old_config_dir = os.path.join(parent_dir, f"config_to_remove_{backup_time}")
        colored_print(f"[信息] 重命名当前配置目录: {config_dir} -> {old_config_dir}", Colors.BLUE)
        os.rename(config_dir, old_config_dir)
        
        # 复制备份内容到配置目录
        colored_print(f"[信息] 复制备份配置到游戏目录: {selected_dir['path']} -> {config_dir}", Colors.BLUE)
        shutil.copytree(selected_dir['path'], config_dir)
        
        colored_print("[成功] 游戏配置已从备份还原", Colors.GREEN)
        colored_print(f"[信息] 当前配置已备份到: {backup_dir}", Colors.BLUE)
        
        # 询问是否删除临时目录
        if show_confirm_dialog("删除临时目录", "是否删除临时目录以节省空间？"):
            try:
                shutil.rmtree(old_config_dir)
                colored_print(f"[清理] 已删除临时目录: {old_config_dir}", Colors.BLUE)
            except Exception as e:
                colored_print(f"[警告] 无法删除临时目录: {e}", Colors.YELLOW)
        
        # 初始化Git仓库
        colored_print("[Git] 正在检查Git仓库状态...", Colors.BLUE)
        stdout, stderr, code = run_git_command(['git', 'status'], cwd=config_dir, check=False)
        if code != 0:
            colored_print("[Git] 需要初始化Git仓库...", Colors.YELLOW)
            from common_utils import init_git_repo
            if init_git_repo(config_dir):
                colored_print("[Git] Git仓库初始化成功", Colors.GREEN)
            else:
                colored_print("[警告] Git仓库初始化失败，但配置文件已还原", Colors.YELLOW)
        else:
            colored_print("[Git] Git仓库状态正常", Colors.GREEN)
        
        return True
            
    except Exception as e:
        colored_print(f"[错误] 还原过程中出错: {e}", Colors.RED)
        return False

def main():
    """主函数"""
    print_header("Git操作快捷工具")
    
    # 获取游戏路径
    game_path = get_game_path()
    if not game_path:
        colored_print("无法确定游戏路径，操作中止", Colors.RED)
        input("按任意键继续...")
        return
    
    # 获取配置目录
    config_dir = get_config_dir(game_path)
    
    # 检查Git环境
    stdout, stderr, code = run_git_command(['git', 'status'], cwd=config_dir, check=False)
    if code != 0:
        colored_print("Git环境未准备好，尝试初始化...", Colors.YELLOW)
        if not prepare_git_environment(game_path):
            colored_print("准备Git环境失败，操作中止", Colors.RED)
            input("按任意键继续...")
            return
    
    while True:
        print("\n" + "=" * 50)
        print("Git操作快捷工具 - 请选择操作:")
        print("=" * 50)
        print("1. 切换到纯净的游戏分支 (master)")
        print("2. 切换到MOD安装分支 (mods_applied)")
        print("3. 查看并切换到历史版本")
        print("4. 启动游戏")  
        print("5. 创建当前状态的备份分支")
        print("6. 打开游戏目录")
        print("7. 打开游戏配置目录")
        print("8. 打开游戏冲突目录")
        print("9. 打开游戏存档目录")
        print("10. 查看当前分支状态")
        print("11. 重置游戏到纯净状态")
        print("12. 查看并尝试合并失败的MOD")
        print("13. 使用Gitee仓库配置替换游戏配置")
        print("14. 从备份还原游戏配置")
        print("0. 退出")
        print("=" * 50)
        
        choice = input("请输入选项编号: ")
        
        if choice == '1':
            # 切换到纯净的游戏分支
            switch_to_branch(config_dir, 'master')
        
        elif choice == '2':
            # 切换到MOD安装分支
            switch_to_branch(config_dir, 'mods_applied')
        
        elif choice == '3':
            # 查看并切换到历史版本
            history_branches = list_history_branches(config_dir)
            if not history_branches:
                colored_print("[信息] 没有找到历史版本分支", Colors.BLUE)
                continue
            
            print("\n历史版本列表:")
            for i, branch in enumerate(history_branches, 1):
                print(f"{i}. {branch['name']} - {branch['date']} - {branch['message']}")
            
            sub_choice = input("\n请选择要切换的历史版本编号 (0返回): ")
            if sub_choice == '0':
                continue
            
            try:
                index = int(sub_choice) - 1
                if 0 <= index < len(history_branches):
                    switch_to_branch(config_dir, history_branches[index]['name'])
                else:
                    colored_print("[错误] 无效的选项", Colors.RED)
            except ValueError:
                colored_print("[错误] 请输入有效的数字", Colors.RED)
        
        elif choice == '12':
            # 查看并尝试合并失败的MOD
            failed_branches = list_failed_mod_branches(config_dir)
            if not failed_branches:
                colored_print("[信息] 没有找到失败的MOD分支", Colors.BLUE)
                continue
            
            print("\n失败MOD分支列表:")
            for i, branch in enumerate(failed_branches, 1):
                print(f"{i}. {branch['name']} - {branch['mod_name']} - {branch['message']}")
            
            sub_choice = input("\n请选择要合并的失败MOD分支编号 (0返回): ")
            if sub_choice == '0':
                continue
            
            try:
                index = int(sub_choice) - 1
                if 0 <= index < len(failed_branches):
                    try_merge_failed_mod(config_dir, failed_branches[index]['name'])
                else:
                    colored_print("[错误] 无效的选项", Colors.RED)
            except ValueError:
                colored_print("[错误] 请输入有效的数字", Colors.RED)
        
        elif choice == '5':
            # 创建当前状态的备份分支
            backup_branch = create_backup_branch(config_dir)
            if backup_branch:
                colored_print(f"[信息] 您可以使用 'git checkout {backup_branch}' 命令切换到备份分支", Colors.BLUE)
        
        elif choice == '6':
            # 打开游戏目录
            open_directory(game_path)
        
        elif choice == '7':
            # 打开游戏配置目录
            open_directory(config_dir)
        
        elif choice == '8':
            # 打开游戏冲突目录
            conflict_dir = get_conflict_dir(game_path)
            if conflict_dir:
                open_directory(conflict_dir)
        
        elif choice == '9':
            # 打开游戏存档目录
            save_data_dir = get_save_data_dir()
            if save_data_dir:
                open_directory(save_data_dir)
        
        elif choice == '10':
            # 查看当前分支状态
            stdout, stderr, code = run_git_command(['git', 'branch', '--show-current'], cwd=config_dir)
            if code == 0:
                current_branch = stdout.strip()
                colored_print(f"[信息] 当前分支: {current_branch}", Colors.BLUE)
                
                # 获取分支的提交信息
                stdout, stderr, code = run_git_command(['git', 'log', '-1', '--pretty=format:%s%n%b', current_branch], cwd=config_dir)
                if code == 0:
                    commit_msg = stdout.strip()
                    colored_print(f"[信息] 分支描述:\n{commit_msg}", Colors.CYAN)
                
                # 检查是否有未提交的更改
                stdout, stderr, code = run_git_command(['git', 'status', '--porcelain'], cwd=config_dir)
                if stdout.strip():
                    colored_print("[警告] 当前分支有未提交的更改", Colors.YELLOW)
                else:
                    colored_print("[信息] 当前分支没有未提交的更改", Colors.GREEN)
            else:
                colored_print(f"[错误] 无法获取当前分支: {stderr}", Colors.RED)
        
        elif choice == '11':
            # 重置游戏到纯净状态
            colored_print("[警告] 此操作将重置游戏到纯净状态，所有MOD更改将丢失", Colors.YELLOW)
            if show_confirm_dialog("重置游戏", "确定要继续吗？"):
                if prepare_git_environment(game_path):
                    colored_print("[成功] 已重置游戏到纯净状态", Colors.GREEN)
                else:
                    colored_print("[错误] 重置游戏失败", Colors.RED)
        
        elif choice == '4':
            # 启动游戏
            run_game(game_path)

        elif choice == '13':
            # 使用Gitee仓库配置替换游戏配置
            restore_from_gitee_repo(config_dir, game_path)

        elif choice == '14':
            # 从备份还原游戏配置
            restore_from_backup_config(config_dir, game_path)

        elif choice == '0':
            # 退出
            break
        
        else:
            colored_print("[错误] 无效的选项，请重新输入", Colors.RED)
            
    print("感谢使用Git操作快捷工具！")

if __name__ == "__main__":
    main()
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
    Colors, colored_print, print_header
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
        choice = input("是否中止合并操作？(y/n): ")
        if choice.lower() == 'y':
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
        print("4. 查看并尝试合并失败的MOD")
        print("5. 创建当前状态的备份分支")
        print("6. 打开游戏目录")
        print("7. 打开游戏配置目录")
        print("8. 打开游戏冲突目录")
        print("9. 打开游戏存档目录")
        print("10. 查看当前分支状态")
        print("11. 重置游戏到纯净状态")
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
        
        elif choice == '4':
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
            confirm = input("确定要继续吗？(y/n): ")
            if confirm.lower() == 'y':
                if prepare_git_environment(game_path):
                    colored_print("[成功] 已重置游戏到纯净状态", Colors.GREEN)
                else:
                    colored_print("[错误] 重置游戏失败", Colors.RED)
        
        elif choice == '0':
            # 退出
            break
        
        else:
            colored_print("[错误] 无效的选项，请重新输入", Colors.RED)
            
    print("感谢使用Git操作快捷工具！")

if __name__ == "__main__":
    main()
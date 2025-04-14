import os
import sys
import json
import datetime
import shutil
from pathlib import Path

# 导入公共工具
from common_utils import (
    get_application_path, ensure_directory, get_game_path, 
    get_config_dir, prepare_git_environment, run_git_command
)

def generate_default_config(mod_dir, mod_name, patch_file=None):
    """为指定的MOD目录生成默认的modConfig.json文件"""
    # 获取当前日期
    current_date = datetime.datetime.now().strftime("%Y.%m.%d")
    
    # 创建默认配置
    default_config = {
        "name": mod_name,
        "author": "未知",
        "version": "1.0.0",
        "gameVersion": "未知",
        "updateDate": current_date,
        "tag": ["自动导入"],
        "source": {
            "name": "自动生成",
            "url": "https://github.com/liwenhao0427/sultans-game-mod-git-manager"
        },
        "files": []
    }
    
    # 如果有补丁文件，添加到配置中
    if patch_file:
        default_config["patchFile"] = patch_file
    
    # 查找并读取txt文件作为remark
    txt_files = []
    for root, _, files in os.walk(mod_dir):
        for file in files:
            if file.lower().endswith('.txt'):
                txt_path = os.path.join(root, file)
                txt_files.append(txt_path)
    
    # 如果找到txt文件，读取第一个作为remark
    if txt_files:
        try:
            with open(txt_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                txt_content = f.read().strip()
                if txt_content:
                    # 限制remark长度，避免过长
                    if len(txt_content) > 500:
                        txt_content = txt_content[:497] + "..."
                    default_config["remark"] = txt_content
                    print(f"已从 {os.path.basename(txt_files[0])} 读取说明信息")
        except Exception as e:
            print(f"读取txt文件时出错: {e}")
    
    # 写入modConfig.json文件
    config_path = os.path.join(mod_dir, "modConfig.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    print(f"已为 {mod_name} 生成默认配置文件")
    return config_path

def process_mod_files(mod_dir, config_dir, mod_name):
    """处理MOD文件，复制到游戏目录并生成补丁"""
    print(f"[处理] MOD: {mod_name}")
    
    # 创建补丁目录
    patches_dir = os.path.join(mod_dir, "patches")
    ensure_directory(patches_dir)
    
    # 查找所有json文件
    json_files = []
    for root, _, files in os.walk(mod_dir):
        for file in files:
            if file.lower().endswith('.json') and file != "modConfig.json":
                json_path = os.path.join(root, file)
                json_files.append(json_path)
    
    if not json_files:
        print(f"[警告] {mod_name} 中没有找到json文件")
        return None
    
    # 创建新分支，处理分支名称，去除非法字符
    safe_mod_name = mod_name.replace(' ', '_').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
    safe_mod_name = ''.join(c for c in safe_mod_name if c.isalnum() or c in '_-.')
    branch_name = f"mod_{safe_mod_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 确保分支名不超过Git允许的最大长度（通常为255个字符）
    if len(branch_name) > 250:
        branch_name = branch_name[:250]
    
    stdout, stderr, code = run_git_command(['git', 'checkout', '-b', branch_name], cwd=config_dir)
    if code != 0:
        print(f"[错误] 无法创建分支 {branch_name}: {stderr}")
        return None
    
    # 复制文件到游戏目录
    copied_files = []
    for json_file in json_files:
        # 计算相对路径
        rel_path = os.path.relpath(json_file, mod_dir)
        target_file = os.path.join(config_dir, rel_path)
        
        # 确保目标目录存在
        ensure_directory(os.path.dirname(target_file))
        
        # 复制文件
        shutil.copy2(json_file, target_file)
        copied_files.append(rel_path)
        print(f"  - 复制: {rel_path}")
    
    # 添加并提交更改
    run_git_command(['git', 'add', '.'], cwd=config_dir)
    commit_msg = f"应用MOD: {mod_name}"
    stdout, stderr, code = run_git_command(['git', 'commit', '-m', commit_msg], cwd=config_dir)
    if code != 0:
        print(f"[错误] 无法提交更改: {stderr}")
        # 重置更改
        run_git_command(['git', 'reset', '--hard', 'HEAD'], cwd=config_dir)
        run_git_command(['git', 'checkout', 'master'], cwd=config_dir, check=False)
        return None
    
    # 生成补丁
    patch_file = os.path.join(patches_dir, f"{mod_name}.patch")
    stdout, stderr, code = run_git_command(['git', 'format-patch', '-1', 'HEAD', '-o', patches_dir], cwd=config_dir)
    if code != 0:
        print(f"[错误] 无法生成补丁: {stderr}")
        # 重置更改
        run_git_command(['git', 'reset', '--hard', 'HEAD~1'], cwd=config_dir)
        run_git_command(['git', 'checkout', 'master'], cwd=config_dir, check=False)
        return None
    
    # 获取生成的补丁文件名
    patch_files = [f for f in os.listdir(patches_dir) if f.endswith('.patch')]
    if not patch_files:
        print(f"[错误] 未找到生成的补丁文件")
        return None
    
    # 使用最新的补丁文件
    latest_patch = sorted(patch_files)[-1]
    patch_path = os.path.join(patches_dir, latest_patch)
    
    # 重置到主分支
    run_git_command(['git', 'checkout', 'master'], cwd=config_dir, check=False)
    run_git_command(['git', 'branch', '-D', branch_name], cwd=config_dir, check=False)
    
    print(f"[完成] 已为 {mod_name} 生成补丁文件: {latest_patch}")
    return os.path.join("patches", latest_patch)

def check_mod_configs():
    """检查所有MOD目录并生成补丁和配置文件"""
    
    # 获取应用程序路径
    app_path = get_application_path()
    
    # 获取游戏路径
    game_path = get_game_path()
    if not game_path:
        print("无法确定游戏路径，操作中止")
        input("按任意键继续...")
        return
    
    # 获取配置目录
    config_dir = get_config_dir(game_path)
    
    # 准备Git环境
    if not prepare_git_environment(game_path):
        print("准备Git环境失败，操作中止")
        input("按任意键继续...")
        return
    
    # 获取Mods目录
    mods_dir = os.path.join(app_path, "Mods")
    if not os.path.exists(mods_dir):
        print(f"错误: Mods目录不存在 ({mods_dir})")
        input("按任意键继续...")
        return
    
    print(f"开始处理 {mods_dir} 目录下的MOD...")
    
    # 统计信息
    total_mods = 0
    processed_mods = 0
    
    # 遍历Mods目录下的所有文件夹
    for mod_name in os.listdir(mods_dir):
        mod_dir = os.path.join(mods_dir, mod_name)
        
        # 只处理目录
        if not os.path.isdir(mod_dir):
            continue
            
        total_mods += 1
        
        # 检查是否存在modConfig.json
        config_file = os.path.join(mod_dir, "modConfig.json")
        
        # 检查是否需要更新补丁
        need_update = False
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 检查是否设置了更新标记或者没有补丁文件
                if config.get("updatePatches", False) or "patchFile" not in config:
                    need_update = True
                    if config.get("updatePatches", False):
                        print(f"[更新] {mod_name} 设置了更新标记，将重新生成补丁")
                    else:
                        print(f"[更新] {mod_name} 没有补丁文件，将生成补丁")
                else:
                    # 检查补丁文件是否存在
                    patch_path = os.path.join(mod_dir, config["patchFile"])
                    if not os.path.exists(patch_path):
                        need_update = True
                        print(f"[更新] {mod_name} 的补丁文件不存在，将重新生成")
                    else:
                        print(f"[跳过] {mod_name} 已有配置文件和补丁文件")
                        continue
            except Exception as e:
                print(f"[错误] 读取配置文件时出错: {e}")
                need_update = True  # 如果配置文件有问题，重新生成
        else:
            need_update = True
            print(f"[新建] {mod_name} 没有配置文件，将生成配置和补丁")
        
        # 处理MOD文件
        if need_update:
            patch_file = process_mod_files(mod_dir, config_dir, mod_name)
            
            if not os.path.exists(config_file):
                print(f"为 {mod_name} 生成配置文件")
                generate_default_config(mod_dir, mod_name, patch_file)
            else:
                # 更新现有配置文件，保留原有属性
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 更新补丁文件路径
                    if patch_file:
                        config["patchFile"] = patch_file
                    
                    # 移除更新标记
                    if "updatePatches" in config:
                        del config["updatePatches"]
                    
                    # 写回配置文件
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    
                    print(f"已更新 {mod_name} 的配置文件")
                except Exception as e:
                    print(f"更新配置文件时出错: {e}")
            
            if patch_file:
                processed_mods += 1
    
    # 打印统计信息
    print("\n处理完成!")
    print(f"总计 {total_mods} 个MOD目录")
    print(f"成功处理 {processed_mods} 个MOD")

if __name__ == "__main__":
    check_mod_configs()
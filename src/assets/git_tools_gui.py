import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue

# 导入公共工具
from common_utils import (
    Colors, colored_print, get_application_path
)

# 直接导入git_tools模块中的所有函数
from git_tools import (
    open_directory, get_save_data_dir, get_conflict_dir,
    switch_to_branch, list_history_branches, list_failed_mod_branches,
    try_merge_failed_mod, create_backup_branch, run_game,
    restore_from_gitee_repo, restore_from_backup_config,
    get_game_path, get_config_dir, prepare_git_environment, run_git_command
)

# 创建一个自定义的输出重定向类，用于捕获控制台输出并显示在GUI中
class TextRedirector:
    def __init__(self, text_widget, queue, tag=""):
        self.text_widget = text_widget
        self.tag = tag
        self.queue = queue

    def write(self, string):
        self.queue.put((string, self.tag))

    def flush(self):
        pass
        
    def input(self, prompt=""):
        """处理输入请求，避免打包后的stdin错误"""
        if prompt:
            self.write(prompt)
        return ""  # 返回空字符串作为默认输入
        
    def readline(self):
        """处理输入请求，避免打包后的stdin错误"""
        return "\n"  # 返回换行符作为默认输入
        
    def read(self, size=-1):
        """处理输入请求，避免打包后的stdin错误"""
        return ""  # 返回空字符串作为默认输入

class GitToolsGUI:
    def __init__(self, root, parent_frame=None, msg_queue=None):
        self.root = root
        self.parent_frame = parent_frame
        
        # 保存原始的标准输入输出
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        
        # 如果提供了父框架，则使用它，否则创建新的
        if parent_frame:
            self.main_frame = parent_frame
        else:
            self.main_frame = ttk.Frame(root, padding="10")
            self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 如果提供了消息队列，则使用它，否则创建新的
        if msg_queue:
            self.msg_queue = msg_queue
        else:
            self.msg_queue = queue.Queue()
            
        # 创建标题标签
        title_label = ttk.Label(
            self.main_frame, 
            text="Git操作工具", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 创建游戏路径框架
        path_frame = ttk.LabelFrame(self.main_frame, text="游戏路径", padding="5")
        path_frame.pack(fill=tk.X, pady=5)
        
        self.game_path_var = tk.StringVar()
        game_path_entry = ttk.Entry(path_frame, textvariable=self.game_path_var, width=70)
        game_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        refresh_btn = ttk.Button(path_frame, text="刷新", command=self.refresh_game_path)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建分支信息框架
        branch_frame = ttk.LabelFrame(self.main_frame, text="分支信息", padding="5")
        branch_frame.pack(fill=tk.X, pady=5)
        
        self.current_branch_var = tk.StringVar(value="加载中...")
        current_branch_label = ttk.Label(branch_frame, text="当前分支:")
        current_branch_label.pack(side=tk.LEFT, padx=5)
        
        current_branch_value = ttk.Label(branch_frame, textvariable=self.current_branch_var, font=("Arial", 10, "bold"))
        current_branch_value.pack(side=tk.LEFT, padx=5)
        
        refresh_branch_btn = ttk.Button(branch_frame, text="刷新", command=self.refresh_branch_info)
        refresh_branch_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建操作按钮框架
        actions_frame = ttk.LabelFrame(self.main_frame, text="Git操作", padding="10")
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建按钮网格
        button_frame = ttk.Frame(actions_frame)
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # 定义按钮和它们的操作
        buttons = [
            {"text": "切换到纯净的游戏分支 (master)", "command": self.switch_to_master, "row": 0, "col": 0},
            {"text": "切换到MOD安装分支 (mods_applied)", "command": self.switch_to_mods_applied, "row": 0, "col": 1},
            {"text": "查看并切换到历史版本", "command": self.view_history_branches, "row": 1, "col": 0},
            {"text": "启动游戏", "command": self.start_game, "row": 1, "col": 1},
            {"text": "创建当前状态的备份分支", "command": self.create_backup, "row": 2, "col": 0},
            {"text": "打开游戏目录", "command": self.open_game_dir, "row": 2, "col": 1},
            {"text": "打开游戏配置目录", "command": self.open_config_dir, "row": 3, "col": 0},
            {"text": "打开游戏冲突目录", "command": self.open_conflict_dir, "row": 3, "col": 1},
            {"text": "打开游戏存档目录", "command": self.open_save_dir, "row": 4, "col": 0},
            # {"text": "查看当前分支状态", "command": self.view_branch_status, "row": 4, "col": 1},
            {"text": "重置游戏到纯净状态", "command": self.reset_to_clean, "row": 5, "col": 0},
            {"text": "查看并尝试合并失败的MOD", "command": self.view_failed_mods, "row": 5, "col": 1},
            {"text": "使用Gitee仓库配置替换游戏配置", "command": self.restore_from_gitee, "row": 6, "col": 0},
            {"text": "从备份还原游戏配置", "command": self.restore_from_backup, "row": 6, "col": 1}
        ]
        
        # 创建按钮
        for btn in buttons:
            button = ttk.Button(
                button_frame, 
                text=btn["text"], 
                command=btn["command"],
                width=30
            )
            button.grid(row=btn["row"], column=btn["col"], padx=10, pady=5, sticky="ew")
        
        # 设置网格列权重
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # 创建输出日志框架
        log_frame = ttk.LabelFrame(self.main_frame, text="操作日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本标签颜色
        self.log_text.tag_configure("red", foreground="red")
        self.log_text.tag_configure("green", foreground="green")
        self.log_text.tag_configure("yellow", foreground="orange")
        self.log_text.tag_configure("blue", foreground="blue")
        self.log_text.tag_configure("magenta", foreground="purple")
        self.log_text.tag_configure("cyan", foreground="teal")
        self.log_text.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=2)
        
        # 重定向标准输出
        redirector = TextRedirector(self.log_text, self.msg_queue)
        sys.stdout = redirector
        sys.stdin = redirector  # 确保标准输入也被重定向
        
        # 设置周期性检查消息队列的任务
        self.check_queue()
        
        # 初始化数据
        self.game_path = None
        self.config_dir = None
        
        # 如果是独立运行，则设置重定向和队列检查
        if not parent_frame:
            # 设置周期性检查消息队列的任务
            self.check_queue()
        
        # 加载初始数据
        self.refresh_game_path()
        self.refresh_branch_info()
    
    def check_queue(self):
        """检查消息队列，更新日志文本框"""
        try:
            while True:
                message, tag = self.msg_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
                self.msg_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # 每100毫秒检查一次队列
            self.root.after(100, self.check_queue)
    
    def refresh_game_path(self):
        """刷新游戏路径"""
        self.game_path = get_game_path()
        if self.game_path:
            self.game_path_var.set(self.game_path)
            self.config_dir = get_config_dir(self.game_path)
            self.status_var.set(f"游戏路径: {self.game_path}")
        else:
            self.game_path_var.set("未找到游戏路径")
            self.config_dir = None
            self.status_var.set("错误: 未找到游戏路径")
            messagebox.showerror("错误", "无法找到游戏路径，请确保游戏已安装。")
    
    def refresh_branch_info(self):
        """刷新分支信息"""
        if not self.config_dir:
            self.current_branch_var.set("未知")
            return
        
        # 在新线程中执行Git命令
        threading.Thread(target=self._refresh_branch_thread, daemon=True).start()
    
    def _refresh_branch_thread(self):
        """在新线程中刷新分支信息"""
        try:
            stdout, stderr, code = run_git_command(['git', 'branch', '--show-current'], cwd=self.config_dir)
            if code == 0:
                branch_name = stdout.strip()
                # 在主线程中更新UI
                self.root.after(0, lambda: self.current_branch_var.set(branch_name))
                self.root.after(0, lambda: self.status_var.set(f"当前分支: {branch_name}"))
            else:
                self.root.after(0, lambda: self.current_branch_var.set("未知"))
                self.root.after(0, lambda: self.status_var.set("无法获取分支信息"))
        except Exception as e:
            self.root.after(0, lambda: self.current_branch_var.set("错误"))
            self.root.after(0, lambda: self.status_var.set(f"获取分支信息时出错: {e}"))
    
    def switch_to_master(self):
        """切换到master分支"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行
        threading.Thread(target=self._switch_branch_thread, args=("master",), daemon=True).start()
    
    def switch_to_mods_applied(self):
        """切换到mods_applied分支"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行
        threading.Thread(target=self._switch_branch_thread, args=("mods_applied",), daemon=True).start()
    
    def _switch_branch_thread(self, branch_name):
        """在新线程中切换分支"""
        try:
            self.root.after(0, lambda: self.status_var.set(f"正在切换到分支: {branch_name}..."))
            
            colored_print(f"[切换] 正在切换到分支: {branch_name}", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            result = switch_to_branch(self.config_dir, branch_name)
            
            if result:
                colored_print(f"[成功] 已切换到分支: {branch_name}", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set(f"已切换到分支: {branch_name}"))
                self.root.after(0, lambda: self.current_branch_var.set(branch_name))
            else:
                colored_print(f"[错误] 无法切换到分支: {branch_name}", Colors.RED)
                self.root.after(0, lambda: self.status_var.set(f"切换分支失败: {branch_name}"))
        
        except Exception as e:
            colored_print(f"[错误] 切换分支时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("切换分支时出错"))
    
    def view_history_branches(self):
        """查看并切换到历史版本"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中获取历史分支
        threading.Thread(target=self._view_history_thread, daemon=True).start()
    
    def _view_history_thread(self):
        """在新线程中获取历史分支"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在获取历史分支..."))
            
            colored_print("[查询] 正在获取历史分支列表...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            history_branches = list_history_branches(self.config_dir)
            
            if not history_branches:
                colored_print("[信息] 没有找到历史分支", Colors.YELLOW)
                self.root.after(0, lambda: self.status_var.set("没有找到历史分支"))
                return
            
            # 在主线程中显示历史分支对话框
            self.root.after(0, lambda: self._show_history_dialog(history_branches))
            
        except Exception as e:
            colored_print(f"[错误] 获取历史分支时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("获取历史分支时出错"))
    
    def _show_history_dialog(self, history_branches):
        """显示历史分支对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("历史版本分支")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 创建说明标签
        ttk.Label(dialog, text="选择要切换到的历史版本分支:", font=("Arial", 10, "bold")).pack(pady=10)
        
        # 创建分支列表框架
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建分支列表
        columns = ("name", "date", "message")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        tree.heading("name", text="分支名称")
        tree.heading("date", text="创建日期")
        tree.heading("message", text="提交信息")
        
        tree.column("name", width=150)
        tree.column("date", width=150)
        tree.column("message", width=250)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充数据
        for branch in history_branches:
            tree.insert("", tk.END, values=(branch["name"], branch["date"], branch["message"]))
        
        # 创建按钮框架
        btn_frame = ttk.Frame(dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        # 创建按钮
        switch_btn = ttk.Button(
            btn_frame, 
            text="切换到选中分支", 
            command=lambda: self._switch_to_selected_branch(tree, dialog)
        )
        switch_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(
            btn_frame, 
            text="取消", 
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def _switch_to_selected_branch(self, tree, dialog):
        """切换到选中的历史分支"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个分支")
            return
        
        # 获取选中的分支名称
        branch_name = tree.item(selected_items[0], "values")[0]
        
        # 关闭对话框
        dialog.destroy()
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中切换分支
        threading.Thread(target=self._switch_branch_thread, args=(branch_name,), daemon=True).start()
    
    def start_game(self):
        """启动游戏"""
        if not self.game_path:
            messagebox.showerror("错误", "未找到游戏路径")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中启动游戏
        threading.Thread(target=self._start_game_thread, daemon=True).start()
    
    def _start_game_thread(self):
        """在新线程中启动游戏"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在启动游戏..."))
            
            colored_print("[启动] 正在启动游戏...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            result = run_game(self.game_path)
            
            if result:
                colored_print("[成功] 游戏已启动", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set("游戏已启动"))
            else:
                colored_print("[错误] 启动游戏失败", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("启动游戏失败"))
        
        except Exception as e:
            colored_print(f"[错误] 启动游戏时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("启动游戏时出错"))
    
    def create_backup(self):
        """创建当前状态的备份分支"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中创建备份
        threading.Thread(target=self._create_backup_thread, daemon=True).start()
    
    def _create_backup_thread(self):
        """在新线程中创建备份"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在创建备份..."))
            
            colored_print("[备份] 正在创建当前状态的备份分支...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            backup_branch = create_backup_branch(self.config_dir)
            
            if backup_branch:
                colored_print(f"[成功] 已创建备份分支: {backup_branch}", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set(f"已创建备份分支: {backup_branch}"))
                
                # 显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("备份成功", f"已创建备份分支: {backup_branch}"))
            else:
                colored_print("[错误] 创建备份分支失败", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("创建备份分支失败"))
        
        except Exception as e:
            colored_print(f"[错误] 创建备份时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("创建备份时出错"))
    
    def open_game_dir(self):
        """打开游戏目录"""
        if not self.game_path:
            messagebox.showerror("错误", "未找到游戏路径")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中打开目录
        threading.Thread(target=lambda: self._open_directory_thread(self.game_path), daemon=True).start()
    
    def _open_directory_thread(self, path):
        """在新线程中打开目录"""
        try:
            self.root.after(0, lambda: self.status_var.set(f"正在打开目录: {path}"))
            
            # 直接调用git_tools.py中的函数
            result = open_directory(path)
            
            if result:
                colored_print(f"[成功] 已打开目录: {path}", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set("已打开目录"))
            else:
                colored_print("[错误] 打开目录失败", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("打开目录失败"))
        
        except Exception as e:
            colored_print(f"[错误] 打开目录时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("打开目录时出错"))
    
    def open_config_dir(self):
        """打开游戏配置目录"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中打开目录
        threading.Thread(target=lambda: self._open_directory_thread(self.config_dir), daemon=True).start()
    
    def open_conflict_dir(self):
        """打开游戏冲突目录"""
        if not self.game_path:
            messagebox.showerror("错误", "未找到游戏路径")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中打开目录
        threading.Thread(target=self._open_conflict_dir_thread, daemon=True).start()
    
    def _open_conflict_dir_thread(self):
        """在新线程中打开冲突目录"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在打开冲突目录..."))
            
            colored_print("[打开] 正在获取冲突目录...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            conflict_dir = get_conflict_dir(self.game_path)
            
            if conflict_dir:
                result = open_directory(conflict_dir)
                if result:
                    colored_print(f"[成功] 已打开冲突目录: {conflict_dir}", Colors.GREEN)
                    self.root.after(0, lambda: self.status_var.set(f"已打开冲突目录"))
                else:
                    colored_print("[错误] 打开冲突目录失败", Colors.RED)
                    self.root.after(0, lambda: self.status_var.set("打开冲突目录失败"))
            else:
                colored_print("[错误] 无法获取冲突目录", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("无法获取冲突目录"))
        
        except Exception as e:
            colored_print(f"[错误] 打开冲突目录时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("打开冲突目录时出错"))
    
    def open_save_dir(self):
        """打开游戏存档目录"""
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中打开目录
        threading.Thread(target=self._open_save_dir_thread, daemon=True).start()
    
    def _open_save_dir_thread(self):
        """在新线程中打开存档目录"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在打开存档目录..."))
            
            colored_print("[打开] 正在获取存档目录...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            save_dir = get_save_data_dir()
            
            if save_dir:
                result = open_directory(save_dir)
                if result:
                    colored_print(f"[成功] 已打开存档目录: {save_dir}", Colors.GREEN)
                    self.root.after(0, lambda: self.status_var.set(f"已打开存档目录"))
                else:
                    colored_print("[错误] 打开存档目录失败", Colors.RED)
                    self.root.after(0, lambda: self.status_var.set("打开存档目录失败"))
            else:
                colored_print("[错误] 无法获取存档目录", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("无法获取存档目录"))
        
        except Exception as e:
            colored_print(f"[错误] 打开存档目录时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("打开存档目录时出错"))
    
    def view_branch_status(self):
        """查看当前分支状态"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行Git命令
        threading.Thread(target=self._view_status_thread, daemon=True).start()
    
    def _view_status_thread(self):
        """在新线程中查看分支状态"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在获取分支状态..."))
            
            colored_print("[查询] 正在获取当前分支状态...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            stdout, stderr, code = run_git_command(['git', 'status'], cwd=self.config_dir)
            
            if code == 0:
                colored_print(f"[状态]\n{stdout}", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set("已获取分支状态"))
            else:
                colored_print(f"[错误] 无法获取分支状态: {stderr}", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("无法获取分支状态"))
        
        except Exception as e:
            colored_print(f"[错误] 获取分支状态时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("获取分支状态时出错"))
    
    def reset_to_clean(self):
        """重置游戏到纯净状态"""
        if not self.game_path:
            messagebox.showerror("错误", "未找到游戏路径")
            return
        
        # 确认重置
        confirm = messagebox.askyesno(
            "确认重置", 
            "确定要重置游戏到纯净状态吗？这将删除所有已安装的MOD。"
        )
        
        if not confirm:
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行重置
        threading.Thread(target=self._reset_to_clean_thread, daemon=True).start()
    
    def _reset_to_clean_thread(self):
        """在新线程中重置游戏到纯净状态"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在重置游戏到纯净状态..."))
            
            colored_print("[重置] 正在重置游戏到纯净状态...", Colors.BLUE)
            # 直接调用函数准备Git环境，这会重置游戏到纯净状态
            prepare_git_environment(self.game_path)
            
            colored_print("[成功] 游戏已重置到纯净状态", Colors.GREEN)
            self.root.after(0, lambda: self.status_var.set("游戏已重置到纯净状态"))
            
            # 刷新分支信息
            self.refresh_branch_info()
            
            # 显示成功消息
            self.root.after(0, lambda: messagebox.showinfo("重置成功", "游戏已重置到纯净状态"))
        
        except Exception as e:
            colored_print(f"[错误] 重置游戏时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("重置游戏时出错"))
    
    def view_failed_mods(self):
        """查看并尝试合并失败的MOD"""
        if not self.config_dir:
            messagebox.showerror("错误", "未找到游戏配置目录")
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中获取失败的MOD分支
        threading.Thread(target=self._view_failed_mods_thread, daemon=True).start()
    
    def _view_failed_mods_thread(self):
        """在新线程中获取失败的MOD分支"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在获取失败的MOD分支..."))
            
            colored_print("[查询] 正在获取失败的MOD分支列表...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            failed_branches = list_failed_mod_branches(self.config_dir)
            
            if not failed_branches:
                colored_print("[信息] 没有找到失败的MOD分支", Colors.YELLOW)
                self.root.after(0, lambda: self.status_var.set("没有找到失败的MOD分支"))
                
                # 显示信息
                self.root.after(0, lambda: messagebox.showinfo("查询结果", "没有找到失败的MOD分支"))
                return
            
            # 在主线程中显示失败的MOD分支对话框
            self.root.after(0, lambda: self._show_failed_mods_dialog(failed_branches))
            
        except Exception as e:
            colored_print(f"[错误] 获取失败的MOD分支时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("获取失败的MOD分支时出错"))
    
    def _show_failed_mods_dialog(self, failed_branches):
        """显示失败的MOD分支对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("失败的MOD分支")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 创建说明标签
        ttk.Label(dialog, text="选择要尝试合并的失败MOD分支:", font=("Arial", 10, "bold")).pack(pady=10)
        
        # 创建分支列表框架
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建分支列表
        columns = ("name", "date", "message")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        tree.heading("name", text="分支名称")
        tree.heading("date", text="创建日期")
        tree.heading("message", text="提交信息")
        
        tree.column("name", width=150)
        tree.column("date", width=150)
        tree.column("message", width=250)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充数据
        for branch in failed_branches:
            tree.insert("", tk.END, values=(branch["name"], branch["date"], branch["message"]))
        
        # 创建按钮框架
        btn_frame = ttk.Frame(dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        # 创建按钮
        merge_btn = ttk.Button(
            btn_frame, 
            text="尝试合并选中分支", 
            command=lambda: self._try_merge_failed_mod(tree, dialog)
        )
        merge_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(
            btn_frame, 
            text="取消", 
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def _try_merge_failed_mod(self, tree, dialog):
        """尝试合并选中的失败MOD分支"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个分支")
            return
        
        # 获取选中的分支名称
        branch_name = tree.item(selected_items[0], "values")[0]
        
        # 关闭对话框
        dialog.destroy()
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中尝试合并
        threading.Thread(target=self._try_merge_thread, args=(branch_name,), daemon=True).start()
    
    def _try_merge_thread(self, branch_name):
        """在新线程中尝试合并失败的MOD分支"""
        try:
            self.root.after(0, lambda: self.status_var.set(f"正在尝试合并分支: {branch_name}..."))
            
            colored_print(f"[合并] 正在尝试合并分支: {branch_name}", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            result = try_merge_failed_mod(self.config_dir, branch_name)
            
            if result:
                colored_print(f"[成功] 已成功合并分支: {branch_name}", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set(f"已成功合并分支: {branch_name}"))
                
                # 刷新分支信息
                self.refresh_branch_info()
                
                # 显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("合并成功", f"已成功合并分支: {branch_name}"))
            else:
                colored_print(f"[错误] 无法合并分支: {branch_name}", Colors.RED)
                self.root.after(0, lambda: self.status_var.set(f"合并分支失败: {branch_name}"))
                
                # 显示失败消息
                self.root.after(0, lambda: messagebox.showwarning("合并失败", f"无法合并分支: {branch_name}"))
        
        except Exception as e:
            colored_print(f"[错误] 合并分支时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("合并分支时出错"))
    
    def restore_from_gitee(self):
        """使用Gitee仓库配置替换游戏配置"""
        if not self.game_path:
            messagebox.showerror("错误", "未找到游戏路径")
            return
        
        # 确认还原
        confirm = messagebox.askyesno(
            "确认还原", 
            "确定要使用Gitee仓库配置替换当前游戏配置吗？这将覆盖当前的游戏配置。"
        )
        
        if not confirm:
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行还原
        threading.Thread(target=self._restore_from_gitee_thread, daemon=True).start()
    
    def _restore_from_gitee_thread(self):
        """在新线程中从Gitee仓库还原游戏配置"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在从Gitee仓库还原游戏配置..."))
            
            colored_print("[还原] 正在从Gitee仓库还原游戏配置...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            result = restore_from_gitee_repo(self.game_path)
            
            if result:
                colored_print("[成功] 已从Gitee仓库还原游戏配置", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set("已从Gitee仓库还原游戏配置"))
                
                # 刷新分支信息
                self.refresh_branch_info()
                
                # 显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("还原成功", "已从Gitee仓库还原游戏配置"))
            else:
                colored_print("[错误] 从Gitee仓库还原游戏配置失败", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("从Gitee仓库还原游戏配置失败"))
                
                # 显示失败消息
                self.root.after(0, lambda: messagebox.showwarning("还原失败", "从Gitee仓库还原游戏配置失败"))
        
        except Exception as e:
            colored_print(f"[错误] 还原游戏配置时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("还原游戏配置时出错"))
    
    def restore_from_backup(self):
        """从备份还原游戏配置"""
        if not self.game_path:
            messagebox.showerror("错误", "未找到游戏路径")
            return
        
        # 确认还原
        confirm = messagebox.askyesno(
            "确认还原", 
            "确定要从备份还原游戏配置吗？这将覆盖当前的游戏配置。"
        )
        
        if not confirm:
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行还原
        threading.Thread(target=self._restore_from_backup_thread, daemon=True).start()
    
    def _restore_from_backup_thread(self):
        """在新线程中从备份还原游戏配置"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在从备份还原游戏配置..."))
            
            colored_print("[还原] 正在从备份还原游戏配置...", Colors.BLUE)
            # 直接调用git_tools.py中的函数
            result = restore_from_backup_config(self.game_path)
            
            if result:
                colored_print("[成功] 已从备份还原游戏配置", Colors.GREEN)
                self.root.after(0, lambda: self.status_var.set("已从备份还原游戏配置"))
                
                # 刷新分支信息
                self.refresh_branch_info()
                
                # 显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("还原成功", "已从备份还原游戏配置"))
            else:
                colored_print("[错误] 从备份还原游戏配置失败", Colors.RED)
                self.root.after(0, lambda: self.status_var.set("从备份还原游戏配置失败"))
                
                # 显示失败消息
                self.root.after(0, lambda: messagebox.showwarning("还原失败", "从备份还原游戏配置失败"))
        
        except Exception as e:
            colored_print(f"[错误] 还原游戏配置时出错: {e}", Colors.RED)
            self.root.after(0, lambda: self.status_var.set("还原游戏配置时出错"))

    # 如果直接运行此文件，则创建独立窗口
    def on_closing(self):
        """窗口关闭时的处理"""
        # 恢复标准输入输出
        sys.stdout = self.old_stdout
        if hasattr(self, 'old_stdin'):
            sys.stdin = self.old_stdin
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = GitToolsGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # 添加关闭窗口处理
    root.mainloop()

if __name__ == "__main__":
    main()
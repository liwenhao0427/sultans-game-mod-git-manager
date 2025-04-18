import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import queue

# 导入原有的MOD安装器模块
from mod_installer import (
    apply_patch, install_mods, get_game_path, get_config_dir,
    prepare_git_environment, run_git_command, check_mod_configs
)

# 导入公共工具
from common_utils import (
    Colors, colored_print, get_application_path
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
        
    def readline(self):
        """处理输入请求，避免打包后的stdin错误"""
        return "\n"  # 返回换行符作为默认输入
        
    def read(self, size=-1):
        """处理输入请求，避免打包后的stdin错误"""
        return ""  # 返回空字符串作为默认输入

# 颜色映射，将原来的控制台颜色映射到Tkinter标签
COLOR_TAGS = {
    Colors.RED: "red",
    Colors.GREEN: "green",
    Colors.YELLOW: "yellow",
    Colors.BLUE: "blue",
    Colors.MAGENTA: "magenta",
    Colors.CYAN: "cyan",
    Colors.BOLD: "bold",
    Colors.RED + Colors.BOLD: "red_bold",
    Colors.GREEN + Colors.BOLD: "green_bold",
    Colors.YELLOW + Colors.BOLD: "yellow_bold",
    Colors.BLUE + Colors.BOLD: "blue_bold",
    Colors.MAGENTA + Colors.BOLD: "magenta_bold",
    Colors.CYAN + Colors.BOLD: "cyan_bold",
}

# 在导入部分添加
from tkinter import filedialog

class ModInstallerGUI:

    # 添加新方法
    def browse_game_path(self):
        """浏览并选择游戏路径"""
        path = filedialog.askdirectory(
            title="选择游戏目录",
            initialdir=self.game_path_var.get() or "C:/"
        )
        if path:
            # 检查是否是有效的游戏目录（包含游戏主程序）
            game_exe = os.path.join(path, "Sultan's Game.exe")
            if not os.path.exists(game_exe):
                messagebox.showerror("警告", "所选目录未找到游戏主程序，请确保路径正确")

            self.game_path_var.set(path)
            self.status_var.set(f"游戏路径: {path}")
            
            # 保存路径到配置文件
            try:
                config_dir = os.path.join(get_application_path(), "config")
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, "config.json")
                
                config = {}
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                
                config['game_path'] = path
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                colored_print(f"[配置] 已保存游戏路径: {path}", Colors.BLUE)
            except Exception as e:
                colored_print(f"[错误] 保存配置文件失败: {e}", Colors.RED)
                
    def __init__(self, root):
        self.root = root
        # 添加排序状态跟踪
        self.sort_reverse = {}  # 用于跟踪每列的排序状态
        self.root.title("苏丹的游戏 MOD 安装器")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # 保存原始的标准输入输出
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        
        # 设置应用图标
        try:
            icon_path = os.path.join(get_application_path(), "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法设置图标: {e}")
        
        # 创建消息队列，用于线程间通信
        self.msg_queue = queue.Queue()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题标签
        title_label = ttk.Label(
            self.main_frame, 
            text="苏丹的游戏 MOD 安装器", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(10,2))
        
        # 添加提示标签
        hint_label = ttk.Label(
            self.main_frame,
            text="提示：双击可以编辑MOD的属性",
            font=("Arial", 9)
        )
        hint_label.pack(pady=(0,8))
        
        # 创建游戏路径框架
        path_frame = ttk.LabelFrame(self.main_frame, text="游戏路径", padding="5")
        path_frame.pack(fill=tk.X, pady=5)
        
        self.game_path_var = tk.StringVar()
        game_path_entry = ttk.Entry(path_frame, textvariable=self.game_path_var, width=70)
        game_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_game_path)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        refresh_btn = ttk.Button(path_frame, text="刷新", command=self.refresh_game_path)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建MOD列表框架
        mods_frame = ttk.LabelFrame(self.main_frame, text="可用MOD", padding="5")
        mods_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建MOD列表视图 - 修改为支持编辑
        self.mod_tree = ttk.Treeview(
            mods_frame, 
            columns=("name", "author", "version", "priority", "recommend"),
            show="tree headings",  # 修改为显示树形结构和表头
            selectmode="extended"
        )
        
        # 定义列
        self.mod_tree.heading("#0", text="选择")  # 添加勾选列
        self.mod_tree.heading("name", text="MOD名称")
        self.mod_tree.heading("author", text="作者")
        self.mod_tree.heading("version", text="版本")
        self.mod_tree.heading("priority", text="安装顺序")
        self.mod_tree.heading("recommend", text="推荐度")
        
        self.mod_tree.column("#0", width=50, stretch=False)  # 设置勾选列宽度
        self.mod_tree.column("name", width=250)
        self.mod_tree.column("author", width=120)
        self.mod_tree.column("version", width=80)
        self.mod_tree.column("priority", width=70)
        self.mod_tree.column("recommend", width=70)

        # 在创建树形视图后添加列排序功能
        for col in ("name", "author", "version", "priority", "recommend"):
            self.mod_tree.heading(col, text=self.mod_tree.heading(col)["text"],
                                command=lambda c=col: self.sort_treeview(c))
        
        # 添加滚动条
        mod_scrollbar = ttk.Scrollbar(mods_frame, orient=tk.VERTICAL, command=self.mod_tree.yview)
        self.mod_tree.configure(yscrollcommand=mod_scrollbar.set)
        
        self.mod_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mod_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建控制按钮框架
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.select_all_var = tk.BooleanVar()
        select_all_check = ttk.Checkbutton(
            control_frame, 
            text="全选", 
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        select_all_check.pack(side=tk.LEFT, padx=5)
        
        install_btn = ttk.Button(
            control_frame, 
            text="安装选中的MOD", 
            command=self.install_selected_mods
        )
        install_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_mods_btn = ttk.Button(
            control_frame, 
            text="刷新MOD列表", 
            command=self.load_mods
        )
        refresh_mods_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = ttk.Button(
            control_frame, 
            text="重置游戏配置", 
            command=self.reset_game_config
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        git_tools_btn = ttk.Button(
            control_frame, 
            text="打开Git工具", 
            command=self.open_git_tools
        )
        git_tools_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建输出日志框架
        log_frame = ttk.LabelFrame(self.main_frame, text="安装日志", padding="5")
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
        
        # 配置组合颜色标签
        for color in [Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE, Colors.MAGENTA, Colors.CYAN]:
            self.log_text.tag_configure(
                f"{COLOR_TAGS[color]}_bold", 
                foreground=COLOR_TAGS[color], 
                font=("TkDefaultFont", 10, "bold")
            )
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=2)
        
        # 初始化数据
        self.mods = []
        self.selected_mods = set()
        
        # 重定向标准输出
        self.old_stdout = sys.stdout
        sys.stdout = TextRedirector(self.log_text, self.msg_queue)
        
        # 设置周期性检查消息队列的任务
        self.check_queue()
        
        # 加载初始数据
        self.refresh_game_path()
        self.load_mods()
    
    def check_queue(self):
        """检查消息队列，更新日志文本框"""
        try:
            while True:
                message, tag = self.msg_queue.get_nowait()
                
                # 处理颜色标签
                current_tag = ""
                for color, tag_name in COLOR_TAGS.items():
                    if color in tag:
                        current_tag = tag_name
                        break
                
                self.log_text.insert(tk.END, message, current_tag)
                self.log_text.see(tk.END)
                self.msg_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # 每100毫秒检查一次队列
            self.root.after(100, self.check_queue)
    
    def refresh_game_path(self):
        """刷新游戏路径"""
        game_path = get_game_path()
        if game_path:
            self.game_path_var.set(game_path)
            self.status_var.set(f"游戏路径: {game_path}")
        else:
            self.game_path_var.set("未找到游戏路径")
            self.status_var.set("错误: 未找到游戏路径")
            messagebox.showerror("错误", "无法找到游戏路径，请确保游戏已安装。")
    
    def load_mods(self):
        """加载可用的MOD列表"""
        try:
            # 清空现有列表
            for item in self.mod_tree.get_children():
                self.mod_tree.delete(item)
            
            self.mods = []
            self.selected_mods = set()
            
            # 获取应用程序路径
            app_path = get_application_path()
            mods_dir = os.path.join(app_path, "Mods")
            
            if not os.path.exists(mods_dir):
                self.log_text.insert(tk.END, "[错误] Mods目录不存在\n", "red")
                return
            
            # 遍历Mods目录
            for mod_name in os.listdir(mods_dir):
                mod_dir = os.path.join(mods_dir, mod_name)
                if not os.path.isdir(mod_dir):
                    continue
                
                # 查找modConfig.json文件
                mod_config_file = os.path.join(mod_dir, "modConfig.json")
                if not os.path.exists(mod_config_file):
                    continue
                
                # 读取配置文件
                try:
                    with open(mod_config_file, 'r', encoding='utf-8') as f:
                        mod_config = json.load(f)
                    
                    # 检查是否有补丁文件
                    if "patchFile" not in mod_config:
                        continue
                    
                    # 获取MOD信息
                    author = mod_config.get("author", "未知")
                    version = mod_config.get("version", "")
                    priority = mod_config.get("priority", 100)
                    recommend = mod_config.get("recommend", 3)  # 默认推荐度为3
                    ignore = mod_config.get("ignore", False)
                    
                    # 添加到MOD列表
                    self.mods.append({
                        "name": mod_name,
                        "dir": mod_dir,
                        "config": mod_config,
                        "config_file": mod_config_file,
                        "author": author,
                        "version": version,
                        "priority": priority,
                        "recommend": recommend,
                        "ignore": ignore
                    })
                    
                except Exception as e:
                    self.log_text.insert(tk.END, f"[错误] 无法读取配置文件 {mod_config_file}: {e}\n", "red")
            
            # 按优先级排序，优先级相同时按推荐度逆序排序
            self.mods.sort(key=lambda x: (x["priority"], -x["recommend"]))
            
            # 更新树形视图 - 根据ignore字段决定是否选中
            for mod in self.mods:
                # 如果ignore为False，则选中
                checked = "✓" if not mod["ignore"] else ""
                
                item_id = self.mod_tree.insert(
                    "", 
                    tk.END,
                    text=checked,
                    values=(mod["name"], mod["author"], mod["version"], mod["priority"], mod["recommend"]),
                    open=True  # 默认展开
                )
                # 存储MOD名称和对应的树项ID的映射
                mod["item_id"] = item_id
            
            # 添加点击事件绑定
            self.mod_tree.bind("<ButtonRelease-1>", self.on_tree_click)
            # 添加双击事件绑定
            self.mod_tree.bind("<Double-1>", self.on_tree_double_click)
            
            self.status_var.set(f"已加载 {len(self.mods)} 个MOD")
            
        except Exception as e:
            self.log_text.insert(tk.END, f"[错误] 加载MOD列表时出错: {e}\n", "red")
            self.status_var.set("加载MOD列表失败")
    
    def on_tree_click(self, event):
        """处理树形视图的点击事件，实现勾选/取消勾选功能并更新配置文件"""
        region = self.mod_tree.identify_region(event.x, event.y)
        if region == "tree":  # 点击在树形图标区域
            item_id = self.mod_tree.identify_row(event.y)
            if item_id:  # 确保点击在有效行上
                # 获取当前项的值
                current_text = self.mod_tree.item(item_id, "text")
                
                # 切换勾选状态
                new_state = "" if current_text == "✓" else "✓"
                self.mod_tree.item(item_id, text=new_state)
                
                # 更新MOD配置文件中的ignore字段
                for mod in self.mods:
                    if mod["item_id"] == item_id:
                        # 更新ignore字段（选中时ignore为False）
                        mod["ignore"] = (new_state != "✓")
                        
                        # 更新配置文件
                        try:
                            mod["config"]["ignore"] = mod["ignore"]
                            with open(mod["config_file"], 'w', encoding='utf-8') as f:
                                json.dump(mod["config"], f, ensure_ascii=False, indent=2)
                            
                            colored_print(f"[更新] 已更新MOD '{mod['name']}' 的安装状态为: {'不安装' if mod['ignore'] else '安装'}", Colors.BLUE)
                        except Exception as e:
                            colored_print(f"[错误] 无法更新MOD配置文件: {e}", Colors.RED)
                        break
                
                # 更新全选状态
                self.update_select_all_state()
    
    def update_select_all_state(self):
        """更新全选复选框的状态"""
        all_items = self.mod_tree.get_children()
        if not all_items:
            self.select_all_var.set(False)
            return
            
        # 检查是否所有项目都被选中
        all_selected = all(self.mod_tree.item(item, "text") == "✓" for item in all_items)
        
        # 如果状态发生变化，则更新复选框状态
        current_state = self.select_all_var.get()
        if current_state != all_selected:
            self.select_all_var.set(all_selected)
            
            # 更新所有MOD的配置文件
            for mod in self.mods:
                item_id = mod["item_id"]
                is_selected = self.mod_tree.item(item_id, "text") == "✓"
                
                # 如果配置中的ignore状态与当前选中状态不一致，则更新配置文件
                if mod["ignore"] == is_selected:  # ignore为True表示不选中
                    mod["ignore"] = not is_selected
                    
                    # 更新配置文件
                    try:
                        mod["config"]["ignore"] = mod["ignore"]
                        with open(mod["config_file"], 'w', encoding='utf-8') as f:
                            json.dump(mod["config"], f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        colored_print(f"[错误] 无法更新MOD配置文件: {e}", Colors.RED)
        
    def on_tree_double_click(self, event):
        """处理树形视图的双击事件，允许编辑字段"""
        region = self.mod_tree.identify_region(event.x, event.y)
        if region == "cell":  # 点击在单元格区域
            item_id = self.mod_tree.identify_row(event.y)
            column = self.mod_tree.identify_column(event.x)
            
            if not item_id or not column:
                return
            
            # 获取列索引（#0是树形图标列，#1是第一个数据列）
            column_idx = int(column[1:]) - 1
            
            # 获取列名
            column_names = ["name", "author", "version", "priority", "recommend"]
            if column_idx < 0 or column_idx >= len(column_names):
                return
            
            column_name = column_names[column_idx]
            
            # 获取当前值
            current_values = self.mod_tree.item(item_id, "values")
            current_value = current_values[column_idx] if current_values else ""
            
            # 创建编辑框
            self.create_edit_popup(item_id, column_idx, column_name, current_value)
    
    def create_edit_popup(self, item_id, column_idx, column_name, current_value):
        """创建编辑弹出窗口"""
        # 获取单元格的坐标
        x, y, width, height = self.mod_tree.bbox(item_id, column="#" + str(column_idx + 1))
        
        # 创建编辑框
        entry_edit = ttk.Entry(self.mod_tree)
        entry_edit.insert(0, current_value)
        entry_edit.select_range(0, tk.END)
        
        # 放置编辑框
        entry_edit.place(x=x, y=y, width=width, height=height)
        entry_edit.focus_set()
        
        # 绑定事件
        entry_edit.bind("<FocusOut>", lambda e: self.save_edit(e, item_id, column_idx, column_name, entry_edit))
        entry_edit.bind("<Escape>", lambda e: self.cancel_edit(e, entry_edit))
    
    def save_edit(self, event, item_id, column_idx, column_name, entry):
        """保存编辑结果"""
        new_value = entry.get()
        
        # 获取当前值
        current_values = list(self.mod_tree.item(item_id, "values"))
        
        # 对于数值类型的字段，进行类型转换
        if column_name in ["priority", "recommend"]:
            try:
                new_value = int(new_value)
            except ValueError:
                messagebox.showerror("错误", f"{column_name} 必须是整数")
                entry.destroy()
                return
        
        # 更新树形视图
        current_values[column_idx] = new_value
        self.mod_tree.item(item_id, values=current_values)
        
        # 更新MOD配置
        for mod in self.mods:
            if mod["item_id"] == item_id:
                # 更新内存中的值
                mod[column_name] = new_value
                
                # 更新配置文件
                try:
                    mod["config"][column_name] = new_value
                    with open(mod["config_file"], 'w', encoding='utf-8') as f:
                        json.dump(mod["config"], f, ensure_ascii=False, indent=2)
                    
                    colored_print(f"[更新] 已更新MOD '{mod['name']}' 的 {column_name} 为: {new_value}", Colors.BLUE)
                except Exception as e:
                    colored_print(f"[错误] 无法更新MOD配置文件: {e}", Colors.RED)
                break
        
        # 如果修改了优先级，重新排序
        if column_name == "priority":
            self.reload_mods_with_sort()
        
        entry.destroy()
    
    def cancel_edit(self, event, entry):
        """取消编辑"""
        entry.destroy()
        
    def sort_treeview(self, col):
        """对树形视图按列排序"""
        # 初始化或切换排序方向
        if col not in self.sort_reverse:
            self.sort_reverse[col] = False
        else:
            self.sort_reverse[col] = not self.sort_reverse[col]
        
        # 获取所有项目
        items = [(self.mod_tree.set(item, col), item) for item in self.mod_tree.get_children('')]
        
        # 根据列类型进行排序
        if col == "priority":
            # 优先级排序，相同时按推荐度逆序
            items.sort(key=lambda x: (
                int(x[0]) if x[0].isdigit() else 0,
                -int(self.mod_tree.set(x[1], "recommend")) if self.mod_tree.set(x[1], "recommend").isdigit() else 0
            ), reverse=self.sort_reverse[col])
        elif col == "recommend":
            # 推荐度排序
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, 
                      reverse=not self.sort_reverse[col])  # 推荐度默认降序
        else:
            # 字符串排序
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse[col])
        
        # 重新排列项目
        for index, (val, item) in enumerate(items):
            self.mod_tree.move(item, '', index)
            
    def reload_mods_with_sort(self):
        """重新加载MOD列表并排序"""
        # 保存当前选中状态
        selected_mods = {}
        for mod in self.mods:
            item_id = mod["item_id"]
            selected_mods[mod["name"]] = self.mod_tree.item(item_id, "text") == "✓"
        
        # 重新加载MOD列表
        self.load_mods()
    
    def toggle_select_all(self):
        """切换全选/取消全选并更新配置文件"""
        all_items = self.mod_tree.get_children()
        if self.select_all_var.get():
            # 全选
            for item in all_items:
                self.mod_tree.item(item, text="✓")
                
                # 更新MOD配置
                for mod in self.mods:
                    if mod["item_id"] == item:
                        mod["ignore"] = False
                        
                        # 更新配置文件
                        try:
                            mod["config"]["ignore"] = False
                            with open(mod["config_file"], 'w', encoding='utf-8') as f:
                                json.dump(mod["config"], f, ensure_ascii=False, indent=2)
                        except Exception as e:
                            colored_print(f"[错误] 无法更新MOD配置文件: {e}", Colors.RED)
                        break
        else:
            # 取消全选
            for item in all_items:
                self.mod_tree.item(item, text="")
                
                # 更新MOD配置
                for mod in self.mods:
                    if mod["item_id"] == item:
                        mod["ignore"] = True
                        
                        # 更新配置文件
                        try:
                            mod["config"]["ignore"] = True
                            with open(mod["config_file"], 'w', encoding='utf-8') as f:
                                json.dump(mod["config"], f, ensure_ascii=False, indent=2)
                        except Exception as e:
                            colored_print(f"[错误] 无法更新MOD配置文件: {e}", Colors.RED)
                        break
    
    def install_selected_mods(self):
        """安装选中的MOD"""
        all_items = self.mod_tree.get_children()
        selected_items = [item for item in all_items if self.mod_tree.item(item, "text") == "✓"]
        
        if not selected_items:
            messagebox.showinfo("提示", "请先勾选要安装的MOD")
            return
        
        # 获取选中的MOD名称
        selected_mod_names = []
        for item in selected_items:
            values = self.mod_tree.item(item, "values")
            selected_mod_names.append(values[0])
        
        # 确认安装
        confirm = messagebox.askyesno(
            "确认安装", 
            f"确定要安装以下 {len(selected_mod_names)} 个MOD吗？\n\n" + 
            "\n".join([f"- {name}" for name in selected_mod_names])
        )
        
        if not confirm:
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行安装操作
        threading.Thread(target=self._install_mods_thread, daemon=True).start()
    
    def _install_mods_thread(self):
        """在新线程中执行MOD安装"""
        try:
            self.status_var.set("正在安装MOD...")
            
            # 检查并准备MOD配置
            colored_print("[准备阶段] 检查MOD配置和补丁文件...", Colors.CYAN)
            check_mod_configs()
            
            # 安装MOD
            colored_print("\n[安装阶段] 开始处理MOD文件...\n", Colors.CYAN)
            if install_mods():
                colored_print("\n[完成] MOD安装成功", Colors.GREEN + Colors.BOLD)
                self.status_var.set("MOD安装成功")
                
                # 在主线程中显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("安装完成", "MOD安装成功！"))
                
                # 询问是否打开Git工具
                # self.root.after(0, self._ask_open_git_tools)
            else:
                colored_print("\n[警告] MOD安装过程中出现问题，执行还原操作", Colors.YELLOW)
                game_path = get_game_path()
                if game_path:
                    prepare_git_environment(game_path)
                self.status_var.set("MOD安装失败")
                
                # 在主线程中显示失败消息
                self.root.after(0, lambda: messagebox.showwarning("安装失败", "MOD安装过程中出现问题，已执行还原操作。"))
        
        except Exception as e:
            colored_print(f"\n[错误] 发生异常: {e}", Colors.RED)
            colored_print("[警告] 执行还原操作", Colors.YELLOW)
            try:
                game_path = get_game_path()
                if game_path:
                    prepare_git_environment(game_path)
            except:
                colored_print("[错误] 还原操作失败", Colors.RED)
            
            self.status_var.set("安装过程中发生错误")
            
            # 在主线程中显示错误消息
            self.root.after(0, lambda: messagebox.showerror("错误", f"安装过程中发生异常: {e}"))
    
    def _ask_open_git_tools(self):
        """询问是否打开Git工具"""
        open_git = messagebox.askyesno("安装完成", "是否打开Git操作工具？")
        if open_git:
            self.open_git_tools()
    
    def reset_game_config(self):
        """重置游戏配置"""
        confirm = messagebox.askyesno(
            "确认重置", 
            "确定要重置游戏配置吗？这将删除所有已安装的MOD。"
        )
        
        if not confirm:
            return
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行重置操作
        threading.Thread(target=self._reset_config_thread, daemon=True).start()
    
    def _reset_config_thread(self):
        """在新线程中执行配置重置"""
        try:
            self.status_var.set("正在重置游戏配置...")
            
            game_path = get_game_path()
            if not game_path:
                colored_print("[错误] 无法确定游戏路径", Colors.RED)
                self.status_var.set("重置失败: 无法确定游戏路径")
                return
            
            colored_print("[重置] 正在重置游戏配置...", Colors.CYAN)
            prepare_git_environment(game_path)
            
            colored_print("[完成] 游戏配置已重置", Colors.GREEN)
            self.status_var.set("游戏配置已重置")
            
            # 在主线程中显示成功消息
            self.root.after(0, lambda: messagebox.showinfo("重置完成", "游戏配置已重置为初始状态。"))
            
        except Exception as e:
            colored_print(f"[错误] 重置过程中发生异常: {e}", Colors.RED)
            self.status_var.set("重置过程中发生错误")
            
            # 在主线程中显示错误消息
            self.root.after(0, lambda: messagebox.showerror("错误", f"重置过程中发生异常: {e}"))
    
    def open_git_tools(self):
        """打开Git工具"""
        try:
            # 创建新窗口
            git_window = tk.Toplevel(self.root)
            git_window.title("Git操作工具")
            
            # 导入GitToolsGUI
            from git_tools_gui import GitToolsGUI
            
            # 创建Git工具GUI实例
            git_tools = GitToolsGUI(git_window)
            
        except ImportError:
            messagebox.showerror("错误", "无法导入Git工具GUI模块")
        except Exception as e:
            messagebox.showerror("错误", f"启动Git工具时发生错误: {e}")
    
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
    app = ModInstallerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # 添加关闭窗口处理
    root.mainloop()

if __name__ == "__main__":
    main()
import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 设置图标路径
icon_path = os.path.join(current_dir, 'assets', 'icon.ico')

# 定义所有需要打包的程序
programs = [
    {
        'script': 'mod_installer.py',
        'name': '苏丹的游戏mod管理器',
        'console': True
    },
    {
        'script': 'git_tools.py',
        'name': '苏丹的游戏帮助程序',
        'console': True
    },
    # {
    #     'script': 'check_mod_configs.py',
    #     'name': '加载本地Mods配置',
    #     'console': True
    # },
    {
        'script': 'mod_installer_gui.py',
        'name': '苏丹的游戏mod管理器(图形界面)',
        'console': False,
        'additional_args': ['--windowed']  # 添加windowed参数
    },
    {
        'script': 'git_tools_gui.py',
        'name': '苏丹的游戏帮助程序(图形界面)',
        'console': False,
        'additional_args': ['--windowed']  # 添加windowed参数
    }
]

# 执行打包
for program in programs:
    params = [
        program['script'],
        '--onefile',
        '--console' if program['console'] else '--noconsole',
        '--windowed' if not program['console'] else '',  # 为GUI程序添加windowed参数
        # f'--icon={icon_path}',
        f'--name={program["name"]}',
        f'--distpath={current_dir}',
        '--clean',
    ]
    
    # 添加额外参数
    if 'additional_args' in program:
        params.extend(program['additional_args'])
    
    # 移除空字符串参数
    params = [p for p in params if p]
    
    print(f"\n正在打包 {program['name']}...")
    PyInstaller.__main__.run(params)
    print(f"{program['name']} 打包完成")
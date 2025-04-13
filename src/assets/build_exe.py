import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 设置图标路径（如果有）
# icon_path = os.path.join(current_dir, 'icon.ico')

# 打包参数
params = [
    'mod_installer.py',
    '--onefile',
    '--console',
    # f'--icon={icon_path}',  # 如果有图标，取消注释
    '--name=苏丹的游戏mod管理器',
    f'--distpath={current_dir}',
    '--clean',
]

# 执行打包
PyInstaller.__main__.run(params)
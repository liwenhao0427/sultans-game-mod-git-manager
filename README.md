# 苏丹的游戏 MOD 管理器（GIT版）

苏丹的游戏 MOD 管理器是一个用于游戏MOD管理的项目，它使用Git来管理和更新MOD。

访问地址：  https://liwenhao0427.github.io/sultans-game-mod-manager/

相关项目： 苏丹的游戏剧情阅读器： https://liwenhao0427.github.io/sudans-game-reader/


## 快速使用
0. 环境：确保您的游戏在使用该软件前处于未安装任何MOD的初始状态，如果电脑中没有安装过Git，需要先下载Git。
1. 进入网站 https://sultans-game-mod-manager.edgeone.site/
2. 勾选您希望使用的mod，点击左上角的 `导出选中` 按钮，下载 mod 整合包。
3. 解压到任意目录，运行根目录下的 苏丹的游戏mod管理器.exe 
4. 完成了！请享受游戏吧！


## 额外说明
1. Mod 会存放在游戏根目录的 Mods 目录下，您可以随时移除不想要的 mod，之后重新运行 苏丹的游戏mod管理器.exe 即可完成更新
2. 每次游戏版本更新后，请先检查游戏完整性，将游戏配置还原到默认，然后手动删除\Sultan's Game_Data\StreamingAssets\bak文件夹（之后会增加一个删除的命令），重新运行 苏丹的游戏mod管理器.exe 即可完成更新
3. 如果MOD有说明文档，可以在MOD管理器中将鼠标悬停在MOD名称上查看简要说明，或点击MOD名称查看完整说明

## 功能特性
- 支持多种MOD安装模式，包括完全替换、文本替换、标记替换等
- 自动备份原始游戏文件，可随时还原
- 支持MOD冲突检测，避免不兼容MOD同时安装
- 提供MOD筛选、搜索和排序功能
- 支持查看MOD文件详情和说明文档

## Mod 配置文件结构
`modConfig.json`
```json
{
  "name": "string",
  "author": "string",
  "version": "string",
  "gameVersion": "string",
  "updateDate": "YYYY.MM.DD",
  "remark": "string",
  "tag": ["string"],
  "source": {
    "name": "string",
    "url": "string"
  }
}
```

## 字段说明

### 基本信息字段

| 字段名        | 类型   | 是否必填 | 描述                       | 示例值              |
|---------------|--------|---------|--------------------------|---------------------|
| `name`        | string | 否       | Mod 的名称标识                | "困难模式骰子成功率下降" |
| `author`      | string | 否       | Mod 的作者名称                | "萧敷艾荣"          |
| `version`     | string | 否       | Mod 版本号（推荐使用语义化版本格式）     | "1.0.0"            |
| `gameVersion` | string | 否       | 兼容的游戏版本号，后续版本通常也支持，但不做保证 | "17954583"         |
| `updateDate`  | string | 否       | 最后更新日期（格式：YYYY.MM.DD）    | "2025.04.08"       |
| `remark`      | string | 否       | Mod 的备注信息                | "修复了一些bug"     |
| `tag`         | array  | 否       | Mod 的标签，用于分类和筛选        | ["修复", "困难模式"] |
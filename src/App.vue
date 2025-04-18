 <template>
  <div class="mod-manager-container">   
    <div class="header">
      <h1>苏丹的游戏 MOD 管理器</h1>
          <!-- 添加操作指引 -->
      <div class="operation-guide">
        <p>快速开始：勾选需要的MOD并点击“导出选中”按钮。</p>
        <el-button type="text" @click="showGuideDialog">操作指引</el-button>
        <el-button type="text" @click="showFaqDialog">常见问题解答</el-button>
      </div>
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索Mod名称、作者或版本..."
          prefix-icon="el-icon-search"
          clearable
          @clear="handleSearchClear"
          style="width: 300px;" 
        />
      </div>
    </div>
    <FaqDialog v-model:visible="faqDialogVisible" />
    <!-- 详细操作指引对话框 -->
    <el-dialog
      title="详细操作指引"
      v-model="guideDialogVisible"
      width="50%"
    >
      <div class="guide-content">
        <ol>
          <li>选择一个或多个MOD，然后点击“导出选中”按钮。</li>
          <li>在弹出的导出选项对话框中选择要导出的内容，第一次下载时推荐同时导出exe文件，之后仅导出需要的mod放在之前的Mods目录下即可。</li>
          <li>点击“确认导出”按钮完成导出。</li>
          <li>解压到任意目录后运行【苏丹的游戏mod管理器.exe】即可。</li>
        </ol>
      </div>
      <div class="guide-content">
        <ol>
          <h3>程序操作额外说明：</h3>
          <li>程序默认会从C:\Program Files (x86)\Steam\steamapps\common\Sultan's Game寻找游戏，如果找不到游戏路径，需要手动输入</li>
          <li>程序会在当前目录下生成缓存文件game_path_config.json缓存游戏路径，下次默认使用缓存操作</li>
          <li>程序使用Git版本控制系统管理MOD，首次运行时会初始化Git仓库并自动检测旧版本备份文件进行还原</li>
          <li>每次运行程序，都会先重置到游戏原始版本，再按顺序应用选中的MOD补丁</li>
          <li>游戏更新后，程序会自动检测并更新Git仓库中的游戏文件</li>
        </ol>
      </div>
      <div class="guide-content">
        <ol>
          <h3>网站操作额外说明：</h3>
          <li>使用搜索栏查找特定的MOD。</li>
          <li>通过表格中的筛选功能可以过滤MOD列表。</li>
          <li>exe文件和python文件效果完全相同，仅打包</li>
        </ol>
      </div>
      <div class="guide-content">
        <ol>
          <h3>MOD安装器工作流程：</h3>
            <el-image
              ref="workflowImage"
              :src="require('@/assets/install.png')"
              :preview-src-list="[require('@/assets/install.png')]"
            />
        </ol>
      </div>
      <template #footer>
        <el-button @click="guideDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <div class="toolbar">
      <div>
        <el-button type="primary" @click="showExportDialog" :disabled="selectedMods.length === 0">
          <i class="el-icon-download"></i> 导出选中 ({{ selectedMods.length }})
        </el-button>
        <el-button @click="resetFilters" plain>
          <i class="el-icon-refresh"></i> 重置筛选
        </el-button>
      </div>
      <div>
        <el-button plain>
          <a href="https://liwenhao0427.github.io/sudans-game-reader/" target="_blank" class="mod-manager-link">
            事件分支
          </a>
        </el-button>
        <!-- <el-tag type="info">总计 {{ mods.length }} 个MOD</el-tag> -->
      </div>
    </div>

    <!-- 导出选项对话框 -->
    <el-dialog
      v-model="exportDialogVisible"
      title="导出选项"
      width="400px"
    >
    <el-form label-position="top">
        <el-form-item label="导出内容">
          <el-checkbox v-model="exportOptions.includeMods" disabled>MOD文件</el-checkbox>
          <el-checkbox v-model="exportOptions.includeManager">MOD管理器(exe)</el-checkbox>
          <el-checkbox v-model="exportOptions.includeHelper">游戏帮助程序(exe)</el-checkbox>
          <el-checkbox v-model="exportOptions.includeBash">老版本命令界面版本(exe)</el-checkbox>
          <el-checkbox v-model="exportOptions.includeScript">包含安装脚本(python)(Mac试试这个)</el-checkbox>
        </el-form-item>
        <el-form-item label="文件名">
          <el-input v-model="exportOptions.fileName" placeholder="导出文件名"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="exportDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="exportSelected">
            确认导出
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加Git安装提示对话框 -->
    <el-dialog
      v-model="gitInstallDialogVisible"
      title="安装Git提示"
      width="500px"
    >
      <div class="git-install-content">
        <p>MOD管理器需要Git环境才能正常工作。如果您尚未安装Git，请先下载安装：</p>
        <el-link type="primary" href="https://registry.npmmirror.com/-/binary/git-for-windows/v2.49.0.windows.1/Git-2.49.0-64-bit.exe" target="_blank">
          下载Git安装包 (Git-2.49.0-64-bit.exe)
        </el-link>
        <br/>
        <p>另外，如果已经安装了Git，也推荐下载tortoisegit来便捷的查看Mod的安装情况（非必须）：</p>
        <el-link type="primary" href="https://download.tortoisegit.org/tgit/2.17.0.0/TortoiseGit-2.17.0.2-64bit.msi" target="_blank">
          下载tortoisegit安装包 (TortoiseGit-2.17.0.2-64bit.msi)
        </el-link>
        <br/>
        <p>如果您希望安装中文语言包，可以下载tortoisegit汉化包：</p>
        <el-link type="primary" href="https://download.tortoisegit.org/tgit/2.17.0.0/TortoiseGit-LanguagePack-2.17.0.0-64bit-zh_CN.msi" target="_blank">
          下载tortoisegit汉化包 (TortoiseGit-LanguagePack-2.17.0.0-64bit-zh_CN.msi)
        </el-link>
        <div class="git-install-checkbox">
          <el-checkbox v-model="gitInstallOptions.dontShowAgain">我已安装，下次不再提示</el-checkbox>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeGitInstallDialog">关闭</el-button>
          <el-button type="primary" @click="continueExport">继续导出</el-button>
        </span>
      </template>
    </el-dialog>

    <el-card class="table-card">
      <el-table
        ref="table"
        :data="filteredMods"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        @filter-change="handleFilterChange"
        :default-sort="{prop: 'recommend', order: 'descending'}"
        v-loading="loading"
        row-key="name"
        stripe
        height="calc(100vh - 250px)"
        class="scrollable-table"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="MOD名称" min-width="100" sortable>
          <template v-slot="scope">
            <div 
              class="mod-name" 
              v-tooltip="scope.row.remark ? { content: scope.row.remark, placement: 'top' } : null"
              @click="showRemarkDetails(scope.row)"
              :class="{ 'has-remark': scope.row.remark }"
            >
              {{ scope.row.name }}
              <i v-if="scope.row.remark" class="el-icon-info remark-icon"></i>
              <!-- 添加 updateTo 标记 -->
              <el-tag v-if="scope.row.updateTo" type="danger" size="mini" class="update-to-tag">不支持最新游戏版本</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="recommend" label="推荐度" width="100" sortable>
          <template v-slot="scope">
            {{ scope.row.recommend || this.defaultRecommend }}
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" min-width="100" sortable column-key="author" :filters="getColumnFilters('author')" :filter-method="filterHandler">
          <template v-slot="scope">
            <el-tag size="small">{{ scope.row.author }}</el-tag>
            <!-- 添加source链接 -->
            <a v-if="scope.row.source && scope.row.source.url" 
               :href="scope.row.source.url" 
               target="_blank" 
               class="source-link-icon">
              <i class="el-icon-link"></i>
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="gameVersion" label="游戏版本" width="120" sortable column-key="gameVersion" :filters="getColumnFilters('gameVersion')" :filter-method="filterHandler">
          <template v-slot="scope">
            <!-- 添加 updateTo 信息 -->
            <div v-if="scope.row.updateTo" class="update-to-info">
              <el-tooltip effect="dark" placement="top">
                <template #content>
                  <span>此MOD适用于游戏版本 {{ formatUpdateToDate(scope.row.updateTo) }} 及之前的版本，最新版本游戏可能无法兼容</span>
                </template>
                <el-tag type="danger" size="small">{{ formatUpdateToDate(scope.row.updateTo) }}</el-tag>
              </el-tooltip>
            </div>
            <el-tag v-else type="success" size="small">{{ scope.row.gameVersion }}</el-tag>
          </template>
        </el-table-column>
                
        <!-- 添加来源列 -->
        <el-table-column label="来源" width="150">
          <template v-slot="scope">
            <a 
              v-if="scope.row.source && scope.row.source.url" 
              :href="scope.row.source.url" 
              target="_blank" 
              class="source-link"
            >
              {{ scope.row.source?.name || '未知来源' }}
              <i class="el-icon-link"></i>
            </a>
            <span v-else>未知来源</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="updateDate" label="更新时间" width="120" sortable />
        <el-table-column label="标签" width="150" column-key="tag" :filters="getTagFilters()" :filter-method="filterTagHandler">
          <template v-slot="scope">
            <div class="tag-container">
              <el-tag 
                v-for="(tag, index) in getModTags(scope.row)" 
                :key="index" 
                size="small" 
                :type="tag === '纯替换' ? 'danger' : (tag === '压缩包' ? 'warning' : getTagType(index))" 
                effect="plain"
                class="mod-tag"
              >
                {{ tag }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <!-- 修改文件列为补丁文件列 -->
        <el-table-column label="补丁文件" width="150">
          <template v-slot="scope">
            <div v-if="scope.row.patchFile" class="patch-file-container">
              <el-button type="primary" size="small" @click="viewPatchFile(scope.row)">
                查看补丁
              </el-button>
            </div>
            <div v-else class="no-patch-file">
              <el-tag type="info" size="small">无补丁文件</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>

    </el-card>

    <!-- 添加MOD说明详情对话框 -->
    <el-dialog
      title="MOD说明详情"
      v-model="remarkDetailsVisible"
      width="60%"
      class="remark-details-dialog"
    >
      <div v-if="currentModName" class="mod-name-header">
        <h3>{{ currentModName }}</h3>
      </div>
      <div class="remark-content-container">
        <pre>{{ currentRemark }}</pre>
      </div>
      <template #footer>
        <el-button @click="remarkDetailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      title="补丁文件详情"
      v-model="patchDetailsVisible"
      width="60%"
      class="patch-details-dialog"
      destroy-on-close
    >
      <div v-if="currentModName" class="mod-name-header">
        <h3>{{ currentModName }}</h3>
        <div v-if="currentModSource" class="mod-source-info">
          <span>来源: </span>
          <a :href="currentModSource.url" target="_blank" class="source-link">
            {{ currentModSource.name || currentModSource.url }}
          </a>
        </div>
      </div>
      <div v-if="patchContentLoading" class="patch-loading">
        <el-loading :visible="true" text="加载补丁内容中..."></el-loading>
      </div>
      <div v-else class="patch-files-container">
        <el-input
          v-model="patchFileSearchQuery"
          placeholder="搜索文件..."
          prefix-icon="el-icon-search"
          clearable
          @clear="handlePatchFileSearchClear"
          class="patch-search-input"
        />
        <el-tree
          :data="patchFileTree"
          :props="{ label: 'name' }"
          :filter-node-method="filterPatchNode"
          ref="patchFileTree"
          node-key="path"
          default-expand-all
        >
          <template #default="{ node, data }">
            <span class="patch-tree-node">
              <el-tag 
                size="small" 
                :type="data.type === 'delete' ? 'danger' : (data.type === 'add' ? 'success' : 'info')"
                v-if="!data.isDirectory"
              >
                {{ data.type === 'delete' ? '删除' : (data.type === 'add' ? '新增' : '修改') }}
              </el-tag>
              <span :class="{'is-directory': data.isDirectory}">{{ node.label }}</span>
              <el-button 
                v-if="!data.isDirectory"
                type="text" 
                size="small" 
                @click="viewPatchFileDetails(data.fileData)"
              >
                查看差异
              </el-button>
            </span>
          </template>
        </el-tree>
      </div>
      <template #footer>
        <el-button @click="patchDetailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 添加文件差异对话框 -->
    <el-dialog
      :title="selectedPatchFile?.newName || selectedPatchFile?.oldName"
      v-model="patchFileDialogVisible"
      width="90%"
      class="patch-file-dialog"
      append-to-body
      destroy-on-close
    >
      <div v-html="parsedPatchContent" class="diff2html-wrapper"></div>
      <template #footer>
        <el-button @click="patchFileDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <div class="footer">
      <p>苏丹的游戏 MOD 管理器 &copy; 2025 by <a href="https://github.com/liwenhao0427/sultans-game-mod-git-manager" target="_blank">liwenhao0427</a></p>
    </div>
  </div>
</template>

<script>

// 导入FAQ组件
import FaqDialog from '@/components/FaqDialog.vue';

// 导入本地版本信息
import localVersionInfo from '@/assets/version.json';
import JSZip from "jszip";
import * as Diff2Html from 'diff2html';
import 'diff2html/bundles/css/diff2html.min.css';
import { saveAs } from "file-saver";
// Remove the unused import
// import { Search } from '@element-plus/icons-vue';

export default {
  name: 'App',
  components: {
    // 注册FAQ组件
    FaqDialog
    // Remove the unused component registration
    // Search
  },
  data() {
    return {
      // 添加FAQ对话框控制变量
      faqDialogVisible: false,
      patchFileSearchQuery: '', // 补丁文件搜索关键字
      patchFileTree: [], // 补丁文件树形结构
      patchFiles: [], // 存储补丁中的文件列表
      selectedPatchFile: null, // 当前选中的补丁文件
      patchFileDialogVisible: false, // 控制文件差异对话框的显示
      currentVersion: '1.0.0', // 当前版本号
      guideDialogVisible: false, // 控制操作指引对话框的显示
      remarkDetailsVisible: false,
      currentRemark: '',
      currentModName: '',
      columnFilters: {}, // 存储当前应用的列筛选
      authorColors: {}, // 用于存储作者对应的颜色类型
      defaultRecommend: 3, // 默认推荐值
      fileDetailsVisible: false,
      fileContent: '', // Stores the content of the selected file
      currentModSource: null, // 存储当前查看的MOD的source信息
      mods: [], // 存储 Mod 信息
      selectedMods: [], // 存储选中的 Mod
      loading: true,
      searchQuery: '',
      currentPage: 1,
      pageSize: 10,
      exportDialogVisible: false,
      exportOptions: {
        includeMods: true, // 默认必须包含MOD文件
        includeManager: true, // 默认包含管理器
        includeHelper: false, // 添加帮助程序选项
        includeBash: false, // 添加历史版本命令行界面
        includeScript: false, // 默认不包含脚本
        includeTextLoader: false, // 默认不包含文本加载器
        fileName: 'mods.zip'
      },
      // 添加Git安装提示相关数据
      gitInstallDialogVisible: false,
      gitInstallOptions: {
        dontShowAgain: false
      },
      isExportInProgress: false,
      // 模式描述映射
      modeDescriptions: {
        'REPLACE': '完全替换',
        'REPLACE0': '查找替换文本',
        'REPLACE1': '替换两个标记间内容',
        'APPEND': '末尾追加内容',
        'INSERT': '指定位置插入内容'
      },

      // 新增补丁文件相关属性
      patchDetailsVisible: false,
      currentPatchFile: null,
      fullPatchContent: '',
      displayedPatchContent: '',
      patchContentLoading: false,
      patchContentChunkSize: 10000, // 每次显示的字符数
      currentPatchContentPosition: 0,
      hasMorePatchContent: false,

      // 模式标签类型映射
      modeTagTypes: {
        'REPLACE': 'danger',
        'REPLACE0': 'warning',
        'REPLACE1': 'warning',
        'APPEND': 'info',
        'INSERT': 'info'
      }
    };
  },
  computed: {
    filteredMods() {
      let result = this.mods;
      
      // 应用搜索筛选
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(mod => {
          return (
            mod.name.toLowerCase().includes(query) ||
            (mod.author && mod.author.toLowerCase().includes(query)) ||
            (mod.gameVersion && mod.gameVersion.toLowerCase().includes(query)) ||
            (mod.tag && mod.tag.some(tag => tag.toLowerCase().includes(query)))
          );
        });
      }
      
      // 应用表格列筛选
      if (this.columnFilters && Object.keys(this.columnFilters).length > 0) {
        Object.entries(this.columnFilters).forEach(([key, values]) => {
          if (values && values.length > 0) {
            result = result.filter(mod => {
              if (key === 'tag') {
                // 标签特殊处理
                const modTags = this.getModTags(mod);
                return values.some(value => modTags.includes(value));
              } else {
                // 普通列筛选
                return values.includes(mod[key]);
              }
            });
          }
        });
      }
      
      // 排序
      return this.sortMods(result);
    },
    paginatedData() {
      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = startIndex + this.pageSize;
      return this.filteredMods.slice(startIndex, endIndex);
    }
  },
  mounted() {
    this.loadMods();
    // 将版本检查放在 setTimeout 中异步执行
    setTimeout(() => {
      this.checkVersion();
    }, 2000); // 延迟2秒执行，避免影响初始加载
    
    // Use setTimeout to ensure DOM is fully rendered
    setTimeout(() => {
      if (this.$refs.table) {
        try {
          this.$refs.table.doLayout();
        } catch (error) {
          console.warn('Table layout calculation deferred:', error);
        }
      }
    }, 500);
  },
  watch: {
    patchFileSearchQuery(val) {
      this.$refs.patchFileTree?.filter(val);
    }
  },
  methods: {
    // 添加显示FAQ对话框的方法
    showFaqDialog() {
      this.faqDialogVisible = true;
    },
    // 版本号比较函数
    compareVersions (v1, v2) {
      // Handle undefined or null values
      if (!v1) return -1; // If v1 is undefined/null, consider it older
      if (!v2) return 1;  // If v2 is undefined/null, consider it older
      
      const parts1 = v1.split('.').map(Number);
      const parts2 = v2.split('.').map(Number);
      
      for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const part1 = parts1[i] || 0;
        const part2 = parts2[i] || 0;
        
        if (part1 > part2) return 1;
        if (part1 < part2) return -1;
      }
      
      return 0; // Versions are the same
    }, 
    async checkVersion() {
      try {
        // Get remote version info
        const response = await fetch('https://raw.githubusercontent.com/liwenhao0427/sultans-game-mod-git-manager/refs/heads/main/src/assets/version.json?t=' + new Date().getTime());
        const remoteData = await response.json();
        
        // Get local version - ensure it exists
        const localVersion = localVersionInfo?.version || '0.0.0';
        const remoteVersion = remoteData?.version || '0.0.0';
        
        // Compare versions
        const isNewer = this.compareVersions(remoteVersion, localVersion) > 0;
        
        if (isNewer) {
          if (window.confirm(`发现新版本 ${remoteVersion}, 当前版本 ${localVersion}. 是否刷新页面更新到最新版本?`)) {
            // // 添加时间戳作为缓存破坏参数
            // const newUrl = "https://liwenhao0427.github.io/sultans-game-mod-git-manager/?t=" + new Date().getTime();
            // window.location.href = newUrl;
            window.location.reload(true);
          } else {
            console.log('User chose to update later');
          }
        } else {
          console.log('Already on the latest version');
        }
      } catch (error) {
        console.error('Failed to check for updates:', error);
      }
    },
    // 构建文件树结构
    buildPatchFileTree(files) {
      const tree = [];
      const dirs = new Map();

      files.forEach(file => {
        const path = (file.newName || file.oldName);
        const parts = path.split('/');
        let currentLevel = tree;
        let currentPath = '';

        parts.forEach((part, index) => {
          currentPath = currentPath ? `${currentPath}/${part}` : part;
          
          if (index === parts.length - 1) {
            // 这是文件
            currentLevel.push({
              name: part,
              path: currentPath,
              isDirectory: false,
              type: file.isDeleted ? 'delete' : (file.isNew ? 'add' : 'modify'),
              fileData: file
            });
          } else {
            // 这是目录
            if (!dirs.has(currentPath)) {
              const dirNode = {
                name: part,
                path: currentPath,
                isDirectory: true,
                children: []
              };
              currentLevel.push(dirNode);
              dirs.set(currentPath, dirNode);
            }
            currentLevel = dirs.get(currentPath).children;
          }
        });
      });

      return this.sortPatchFileTree(tree);
    },

    // 排序文件树（目录在前，文件在后）
    sortPatchFileTree(tree) {
      return tree.sort((a, b) => {
        if (a.isDirectory && !b.isDirectory) return -1;
        if (!a.isDirectory && b.isDirectory) return 1;
        return a.name.localeCompare(b.name);
      }).map(node => {
        if (node.isDirectory) {
          node.children = this.sortPatchFileTree(node.children);
        }
        return node;
      });
    },

    // 修改查看补丁文件方法
    async viewPatchFile(mod) {
      this.currentModName = mod.name;
      this.currentModSource = mod.source || null;
      this.patchContentLoading = true;
      this.patchDetailsVisible = true;
      this.patchFileSearchQuery = '';
      
      try {
        const patchContent = await this.getPatchFileContent(mod);
        const diffJson = Diff2Html.parse(patchContent);
        this.patchFileTree = this.buildPatchFileTree(diffJson);
      } catch (error) {
        console.error('加载补丁文件失败:', error);
        this.$message.error('加载补丁文件失败: ' + error.message);
      } finally {
        this.patchContentLoading = false;
      }
    },

    // 文件搜索过滤方法
    filterPatchNode(value, data) {
      if (!value) return true;
      return data.name.toLowerCase().includes(value.toLowerCase());
    },

    // 处理搜索框清空
    handlePatchFileSearchClear() {
      this.patchFileSearchQuery = '';
    },

    // 添加查看具体文件差异的方法
    viewPatchFileDetails(file) {
      this.selectedPatchFile = file;
      this.patchFileDialogVisible = true;
      // 生成选中文件的HTML
      const diffHtml = Diff2Html.html([{
        oldName: file.oldName,
        newName: file.newName,
        isDeleted: file.isDeleted,
        isNew: file.isNew,
        blocks: file.blocks
      }], {
        drawFileList: false,
        matching: 'lines',
        outputFormat: 'side-by-side',
        renderNothingWhenEmpty: false,
      });
      this.parsedPatchContent = diffHtml;
    },
    
    // 加载初始补丁内容
    loadInitialPatchContent() {
      if (this.fullPatchContent.length <= this.patchContentChunkSize) {
        // 如果内容较少，直接全部显示
        this.displayedPatchContent = this.fullPatchContent;
        this.hasMorePatchContent = false;
      } else {
        // 否则只显示一部分
        this.displayedPatchContent = this.fullPatchContent.substring(0, this.patchContentChunkSize);
        this.currentPatchContentPosition = this.patchContentChunkSize;
        this.hasMorePatchContent = true;
      }
    },
    
    // 加载更多补丁内容
    loadMorePatchContent() {
      const nextChunk = this.fullPatchContent.substring(
        this.currentPatchContentPosition,
        this.currentPatchContentPosition + this.patchContentChunkSize
      );
      
      this.displayedPatchContent += nextChunk;
      this.currentPatchContentPosition += this.patchContentChunkSize;
      
      // 检查是否还有更多内容
      this.hasMorePatchContent = this.currentPatchContentPosition < this.fullPatchContent.length;
    },
    
    // 处理补丁内容滚动
    handlePatchContentScroll(event) {
      const container = event.target;
      // 如果滚动到底部附近且还有更多内容，自动加载更多
      if (container.scrollHeight - container.scrollTop - container.clientHeight < 100 && this.hasMorePatchContent) {
        this.loadMorePatchContent();
      }
    },
    
     // 获取补丁文件内容
    async getPatchFileContent(mod) {
      if (!mod.patchFile) {
        return '此MOD没有补丁文件';
      }
      
      try {
        // 加载补丁文件
        // 将反斜杠替换为正斜杠，确保路径格式正确
        const normalizedPatchFile = mod.patchFile.replace(/\\/g, '/');
        const patchPath = `@/assets/Mods/${mod.name}/${normalizedPatchFile}`;
        console.log('尝试加载补丁文件:', patchPath);
        
        // 使用动态导入而不是require
        try {
          const patchContent = await import(
            /* webpackChunkName: "patch-content" */
            `!!raw-loader?esModule=false!@/assets/Mods/${mod.name}/${normalizedPatchFile}`
          );
          return typeof patchContent === 'string' ? patchContent : patchContent.default;
        } catch (importError) {
          console.error('动态导入失败，尝试使用require:', importError);
          const patchContent = require(`!!raw-loader?esModule=false!@/assets/Mods/${mod.name}/${normalizedPatchFile}`);
          return patchContent;
        }
      } catch (error) {
        console.error(`无法加载补丁文件: ${mod.name}/${mod.patchFile}`, error);
        throw new Error(`无法加载补丁文件: ${mod.patchFile}`);
      }
    },

    showGuideDialog() {
      this.guideDialogVisible = true;
    },
    // 显示MOD说明详情
    showRemarkDetails(mod) {
      if (mod.remark) {
        this.currentModName = mod.name;
        this.currentRemark = mod.remark;
        this.remarkDetailsVisible = true;
      }
    },
    handleFilterChange(filters) {
      // 更新筛选状态
      Object.keys(filters).forEach(key => {
        if (filters[key] && filters[key].length > 0) {
          this.columnFilters[key] = filters[key];
        } else {
          // 如果筛选被清除，从状态中移除
          if (this.columnFilters[key]) {
            delete this.columnFilters[key];
          }
        }
      });
      
      // 移除重置页码的代码
      // this.currentPage = 1;
    },
    // 显示导出对话框
    showExportDialog() {
      // 设置默认文件名
      this.exportOptions.fileName = `mods_${this.selectedMods.length}.zip`;
      this.exportDialogVisible = true;
    },
    
    // 修改导出方法，先检查是否需要显示Git安装提示
    exportSelected() {
      this.exportDialogVisible = false;
      this.isExportInProgress = true;
      
      // 检查cookie，判断是否需要显示Git安装提示
      const gitInstalled = this.getCookie('gitInstalled');
      if (gitInstalled !== 'true') {
        this.gitInstallDialogVisible = true;
      } else {
        this.performExport();
      }
    },
    
    // 关闭Git安装提示对话框
    closeGitInstallDialog() {
      this.gitInstallDialogVisible = false;
      this.isExportInProgress = false;
    },
    
    // 继续导出
    continueExport() {
      // 如果用户选择不再提示，设置cookie
      if (this.gitInstallOptions.dontShowAgain) {
        this.setCookie('gitInstalled', 'true', 365); // 设置365天有效期
      }
      
      this.gitInstallDialogVisible = false;
      this.performExport();
    },
    
    // 设置cookie
    setCookie(name, value, days) {
      let expires = '';
      if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
      }
      document.cookie = name + '=' + (value || '') + expires + '; path=/';
    },
    
    // 获取cookie
    getCookie(name) {
      const nameEQ = name + '=';
      const ca = document.cookie.split(';');
      for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
      }
      return null;
    },
    
    async viewFileDetails(modName, fileSource) {
      try {
        // 获取当前MOD的source信息
        const currentMod = this.mods.find(mod => mod.name === modName);
        this.currentModSource = currentMod?.source || null;
        
        // 使用require动态导入文件内容
        const fileContent = await this.getFileContent(modName, fileSource);
        
        // 只有modConfig.json才尝试格式化为JSON
        if (fileSource === 'modConfig.json') {
          try {
            const jsonObj = JSON.parse(fileContent);
            this.fileContent = JSON.stringify(jsonObj, null, 2);
          } catch (e) {
            // 如果解析失败，仍然显示原始文本
            this.fileContent = fileContent;
          }
        } else {
          // 其他JSON文件直接显示为文本
          this.fileContent = fileContent;
        }
        
        this.fileDetailsVisible = true;
      } catch (error) {
        console.error('Error loading file details:', error);
        this.$message.error('无法加载文件详情');
      }
    },
    
    // 修改从assets目录获取文件内容的方法
    async getFileContent(modName, fileSource) {
      try {
        // 根据文件扩展名选择不同的加载方式
        const fileExt = fileSource.split('.').pop().toLowerCase();
        
        if (fileExt === 'json' || fileExt === 'txt' || fileExt === 'config') {
          // 所有文本文件都使用raw-loader，并指定esModule: false
          try {
            const textContent = require(`!!raw-loader?esModule=false!@/assets/Mods/${modName}/${fileSource}`);
            return textContent; // 不再需要 .default，因为设置了 esModule: false
          } catch (error) {
            console.error(`无法加载文件: ${modName}/${fileSource}`, error);
            throw error;
          }
        } else {
          // 其他类型文件
          this.$message.warning(`不支持查看此类型文件: ${fileExt}`);
          return `[不支持查看此类型文件: ${fileExt}]`;
        }
      } catch (error) {
        console.error(`无法加载文件: @/assets/Mods/${modName}/${fileSource}`, error);
        throw new Error(`无法加载文件: ${modName}/${fileSource}`);
      }
    },
    // 修改排序方法，使用recommend字段，相同时按日期倒序
    sortMods(mods) {
      return [...mods].sort((a, b) => {
        const recommendA = a.recommend !== undefined ? a.recommend : this.defaultRecommend;
        const recommendB = b.recommend !== undefined ? b.recommend : this.defaultRecommend;
        
        // 如果推荐度不同，按推荐度排序
        if (recommendB !== recommendA) {
          return recommendB - recommendA;
        }
        
        // 如果推荐度相同，按更新日期倒序排序
        const dateA = a.updateDate || '';
        const dateB = b.updateDate || '';
        return dateB.localeCompare(dateA);
      });
    },

    // 获取作者标签类型
    getAuthorTagType(author) {
      return this.authorColors[author] || '';
    },
    
    // 获取标签筛选选项
    getTagFilters() {
      if (!this.mods || this.mods.length === 0) return [];
      
      // 收集所有标签
      const allTags = [];
      this.mods.forEach(mod => {
        const tags = this.getModTags(mod);
        tags.forEach(tag => {
          if (!allTags.includes(tag)) {
            allTags.push(tag);
          }
        });
      });
      
      // 转换为筛选选项格式
      return allTags.map(tag => ({
        text: tag,
        value: tag
      }));
    },
    

  
    loadMods() {
      this.loading = true;
      try {
        // 使用require.context获取所有modConfig.json文件
        const requireMod = require.context('@/assets/Mods', true, /modConfig\.json$/);
        const modFiles = requireMod.keys();
  
        this.mods = modFiles.map((filePath) => {
          try {
            // 获取文本内容
            const modConfigText = requireMod(filePath);
            
            // 手动解析JSON
            const modConfig = JSON.parse(modConfigText);
            const modDir = filePath.split('/')[1];
            return {
              ...modConfig,
              name: modDir,
              recommend: modConfig.recommend || this.defaultRecommend,
            };
          } catch (error) {
            console.error(`解析modConfig.json失败: ${filePath}`, error);
            // 返回一个基本的mod对象，避免整个加载过程失败
            const modDir = filePath.split('/')[1];
            return {
              name: modDir,
              author: '未知',
              version: '未知',
              gameVersion: '未知',
              updateDate: '未知',
              files: [],
              tag: ['加载失败'],
              recommend: this.defaultRecommend,
            };
          }
        });
      } catch (error) {
        console.error('加载Mods失败:', error);
        this.mods = [];
      }
      this.loading = false;
    },
    handleSelectionChange(selection) {
      this.selectedMods = selection;
    },
    // 添加检查MOD冲突的方法
    checkModConflicts(mods) {
      // 用于存储每个文件路径对应的MOD和操作模式
      const filePathMap = new Map();
      const conflicts = [];
      
      // 遍历所有选中的MOD
      for (const mod of mods) {
        if (!mod.files || !Array.isArray(mod.files)) continue;
        
        // 遍历MOD中的每个文件
        for (const file of mod.files) {
          if (!file.source) continue;
          
          // 获取目标路径（如果没有destination则使用source）
          const targetPath = file.destination || file.source;
          const mode = file.mode || 'REPLACE'; // 默认为REPLACE模式
          
          // 检查此路径是否已存在于映射中
          if (filePathMap.has(targetPath)) {
            const existingEntry = filePathMap.get(targetPath);
            
            // 检查是否至少有一个是全量替换模式
            const isCurrentReplace = mode === 'REPLACE';
            const hasExistingReplace = existingEntry.modes.includes('REPLACE');
            
            if (isCurrentReplace || hasExistingReplace) {
              // 添加当前MOD到已存在的条目
              existingEntry.mods.push(mod.name);
              existingEntry.modes.push(mode);
              
              // 如果这是第一次发现冲突，添加到冲突列表
              if (existingEntry.mods.length === 2) {
                conflicts.push({
                  filePath: targetPath,
                  mods: [...existingEntry.mods],
                  modes: [...existingEntry.modes]
                });
              }
            }
          } else {
            // 添加新条目到映射
            filePathMap.set(targetPath, {
              mods: [mod.name],
              modes: [mode]
            });
          }
        }
      }
      return conflicts;
    },
    // 修改导出方法，使用补丁文件而不是files
    async performExport() {
      // 检查MOD之间的文件冲突 - 由于使用补丁文件，不再需要检查文件冲突
      // 移除冲突检查代码
      
      this.loading = true;
      this.exportDialogVisible = false;
      
      const zip = new JSZip();
  
      // 创建Mods文件夹
      const modsFolder = zip.folder("Mods");
  
      // 根据选项添加主程序文件
      if (this.exportOptions.includeManager) {
        try {
          // 二进制文件需要使用file-loader，并指定esModule: false
          const mainAppPath = require('!!file-loader?esModule=false!@/assets/苏丹的游戏mod管理器(图形界面).exe');
          const mainAppResponse = await fetch(mainAppPath);
          const mainAppBlob = await mainAppResponse.blob();
          zip.file('苏丹的游戏mod管理器(图形界面).exe', mainAppBlob);
        } catch (error) {
          console.error('主程序加载出错:', error);
          // 尝试从备用源下载
          try {
            this.$message.warning('正在从备用源下载主程序文件...');
            const backupUrl = "https://github.com/liwenhao0427/sultans-game-mod-git-manager/raw/refs/heads/main/src/assets/苏丹的游戏mod管理器(图形界面).exe";
            const backupResponse = await fetch(backupUrl);
            
            if (backupResponse.ok) {
              const backupBlob = await backupResponse.blob();
              zip.file('苏丹的游戏mod管理器(图形界面).exe', backupBlob);
              this.$message.success('已从备用源下载主程序文件');
            } else {
              throw new Error(`备用源响应错误: ${backupResponse.status}`);
            }
          } catch (backupError) {
            console.error('备用源下载失败:', backupError);
            this.$message.error('无法加载主程序文件，但Mod文件将正常导出');
          }
        }
      }
      
      // 添加帮助程序
      if (this.exportOptions.includeHelper) {
        try {
          const helperPath = require('!!file-loader?esModule=false!@/assets/苏丹的游戏帮助程序(图形界面).exe');
          const helperResponse = await fetch(helperPath);
          const helperBlob = await helperResponse.blob();
          zip.file('苏丹的游戏帮助程序(图形界面).exe', helperBlob);
        } catch (error) {
          console.error('帮助程序加载出错:', error);
          // 尝试从备用源下载
          try {
            this.$message.warning('正在从备用源下载主程序文件...');
            const backupUrl = "https://github.com/liwenhao0427/sultans-game-mod-git-manager/raw/refs/heads/main/src/assets/苏丹的游戏帮助程序(图形界面).exe";
            const backupResponse = await fetch(backupUrl);
            
            if (backupResponse.ok) {
              const backupBlob = await backupResponse.blob();
              zip.file('苏丹的游戏帮助程序(图形界面).exe', backupBlob);
              this.$message.success('已从备用源下载主程序文件');
            } else {
              throw new Error(`备用源响应错误: ${backupResponse.status}`);
            }
          } catch (backupError) {
            console.error('备用源下载失败:', backupError);
            this.$message.error('无法加载主程序文件，但Mod文件将正常导出');
          }
          this.$message.warning('无法加载帮助程序文件，但其他文件将正常导出');
        }
      }

      // 添加帮助程序
      if (this.exportOptions.includeBash) {
        try {
          const helperPath = require('!!file-loader?esModule=false!@/assets/苏丹的游戏mod管理器.exe');
          const helperResponse = await fetch(helperPath);
          const helperBlob = await helperResponse.blob();
          zip.file('苏丹的游戏mod管理器.exe', helperBlob);
        } catch (error) {
          console.error('帮助程序加载出错:', error);
          // 尝试从备用源下载
          try {
            this.$message.warning('正在从备用源下载主程序文件...');
            const backupUrl = "https://github.com/liwenhao0427/sultans-game-mod-git-manager/raw/refs/heads/main/src/assets/苏丹的游戏mod管理器.exe";
            const backupResponse = await fetch(backupUrl);
            
            if (backupResponse.ok) {
              const backupBlob = await backupResponse.blob();
              zip.file('苏丹的游戏mod管理器.exe', backupBlob);
              this.$message.success('已从备用源下载主程序文件');
            } else {
              throw new Error(`备用源响应错误: ${backupResponse.status}`);
            }
          } catch (backupError) {
            console.error('备用源下载失败:', backupError);
            this.$message.error('无法加载主程序文件，但Mod文件将正常导出');
          }
          this.$message.warning('无法加载帮助程序文件，但其他文件将正常导出');
        }

        try {
          const helperPath = require('!!file-loader?esModule=false!@/assets/苏丹的游戏帮助程序.exe');
          const helperResponse = await fetch(helperPath);
          const helperBlob = await helperResponse.blob();
          zip.file('苏丹的游戏帮助程序.exe', helperBlob);
        } catch (error) {
          console.error('帮助程序加载出错:', error);
          // 尝试从备用源下载
          try {
            this.$message.warning('正在从备用源下载主程序文件...');
            const backupUrl = "https://github.com/liwenhao0427/sultans-game-mod-git-manager/raw/refs/heads/main/src/assets/%E8%8B%8F%E4%B8%B9%E7%9A%84%E6%B8%B8%E6%88%8F%E5%B8%AE%E5%8A%A9%E7%A8%8B%E5%BA%8F.exe";
            const backupResponse = await fetch(backupUrl);
            
            if (backupResponse.ok) {
              const backupBlob = await backupResponse.blob();
              zip.file('苏丹的游戏帮助程序.exe', backupBlob);
              this.$message.success('已从备用源下载主程序文件');
            } else {
              throw new Error(`备用源响应错误: ${backupResponse.status}`);
            }
          } catch (backupError) {
            console.error('备用源下载失败:', backupError);
            this.$message.error('无法加载主程序文件，但Mod文件将正常导出');
          }
          this.$message.warning('无法加载帮助程序文件，但其他文件将正常导出');
        }
      }
      
      // // 根据选项添加文本加载器
      // if (this.exportOptions.includeTextLoader) {
      //   try {
      //     const textLoaderPath = require('!!file-loader?esModule=false!@/assets/加载本地Mods配置.exe');
      //     const textLoaderResponse = await fetch(textLoaderPath);
      //     const textLoaderBlob = await textLoaderResponse.blob();
      //     zip.file('加载本地Mods配置.exe', textLoaderBlob);
      //   } catch (error) {
      //     console.error('文本加载器加载出错:', error);
      //     this.$message.warning('无法加载本地加载器文件，但其他文件将正常导出');
      //   }
      // }
      
      // 根据选项添加安装脚本
      if (this.exportOptions.includeScript) {        
        // 添加Python脚本依赖文件
        if (this.exportOptions.includePythonScripts) {
          try {
            // mod_installer.py
            const scriptPath = require('!!raw-loader?esModule=false!@/assets/mod_installer.py');
            zip.file('mod_installer.py', scriptPath);

            // 加载common_utils.py
            const commonUtilsPath = require('!!raw-loader?esModule=false!@/assets/common_utils.py');
            zip.file('common_utils.py', commonUtilsPath);
            
            // 加载check_mod_configs.py
            const checkModConfigsPath = require('!!raw-loader?esModule=false!@/assets/check_mod_configs.py');
            zip.file('check_mod_configs.py', checkModConfigsPath);
            
            // 加载git_tools.py
            const gitToolsPath = require('!!raw-loader?esModule=false!@/assets/git_tools.py');
            zip.file('git_tools.py', gitToolsPath);

            // 加载check_mod_configs.py
            const mod_installer_gui = require('!!raw-loader?esModule=false!@/assets/mod_installer_gui.py');
            zip.file('mod_installer_gui.py', mod_installer_gui);
            
            // 加载git_tools_gui.py
            const git_tools_gui = require('!!raw-loader?esModule=false!@/assets/git_tools_gui.py');
            zip.file('git_tools_gui.py', git_tools_gui);


            // 加载git_tools.py
            const git_tools = require('!!raw-loader?esModule=false!@/assets/git_tools.py');
            zip.file('git_tools.py', git_tools);

            const batPath = require('!!raw-loader?esModule=false!@/assets/启动Mod管理器.sh');
            zip.file('启动Mod管理器.sh', batPath);            
            
            this.$message.success('已添加Python脚本依赖文件');
          } catch (error) {
            console.error('Python脚本依赖文件加载出错:', error);
            this.$message.warning('无法加载Python脚本依赖文件，但其他文件将正常导出');
          }
        }
      }
  
      // 添加MOD文件
      for (const mod of this.selectedMods) {
        const modFolder = modsFolder.folder(mod.name);
        
        // 添加modConfig.json
        try {
          // 作为文本加载modConfig.json，并指定esModule: false
          const modConfigText = require(`!!raw-loader?esModule=false!@/assets/Mods/${mod.name}/modConfig.json`);
          modFolder.file('modConfig.json', modConfigText);
        } catch (error) {
          console.error(`无法加载modConfig.json: ${mod.name}`, error);
        }
        
        // 添加补丁文件
        if (mod.patchFile) {
          try {
            // 确保patches目录存在
            const patchesFolder = modFolder.folder('patches');
            
            // 获取补丁文件名，先将路径中的反斜杠替换为正斜杠
            const normalizedPatchFile = mod.patchFile.replace(/\\/g, '/');
            const patchFileName = normalizedPatchFile.split('/').pop();
            
            // 加载补丁文件内容
            const patchContent = await this.getPatchFileContent(mod);
            
            // 添加到zip
            patchesFolder.file(patchFileName, patchContent);
            
            // this.$message.success(`已添加补丁文件: ${mod.name}/${patchFileName}`);
          } catch (error) {
            console.error(`无法加载补丁文件: ${mod.name}/${mod.patchFile}`, error);
            this.$message.error(`无法加载补丁文件: ${mod.patchFile}`);
          }
        } else {
          this.$message.warning(`MOD ${mod.name} 没有补丁文件`);
        }
      }
      
      try {
        // 生成zip文件并下载
        const content = await zip.generateAsync({
          type: 'blob',
          compression: 'DEFLATE',
          compressionOptions: {
            level: 9
          }
        });
        
        saveAs(content, this.exportOptions.fileName);
        this.$message.success('导出成功！');
      } catch (error) {
        console.error('导出出错:', error);
        this.$message.error('导出失败，请查看控制台获取详细信息');
      } finally {
        this.loading = false;
      }
    },
    
    // 修改获取MOD标签方法，不再检查files
    getModTags(mod) {
      const tags = [...(mod.tag || [])];
      
      // 如果有补丁文件，添加"补丁"标签
      if (mod.patchFile) {
        if (!tags.includes('补丁')) {
          tags.unshift('补丁');
        }
      }
      
      return tags;
    },
    handleSearchClear() {
      this.searchQuery = '';
    },
    resetFilters() {
      this.searchQuery = '';
      this.columnFilters = {};
      // 移除重置页码的代码
      // this.currentPage = 1;
      
      // 重置表格筛选
      if (this.$refs.table) {
        // 清除所有列的筛选条件
        const tableColumns = this.$refs.table.columns;
        if (tableColumns) {
          tableColumns.forEach(column => {
            if (column.filteredValue && column.filteredValue.length > 0) {
              column.filteredValue = [];
            }
          });
        }
      }
    },
    // 获取标签类型（循环使用不同颜色）
    getTagType(index) {
      const types = ['', 'success', 'info', 'warning', 'danger'];
      return types[index % types.length];
    },
    // 获取模式描述
    getModeDescription(mode) {
      return this.modeDescriptions[mode] || mode;
    },
    // 获取模式标签类型
    getModeTagType(mode) {
      return this.modeTagTypes[mode] || '';
    },
    // 获取列筛选选项
    getColumnFilters(prop) {
      if (!this.mods || this.mods.length === 0) return [];
      
      // 获取唯一值
      const uniqueValues = [...new Set(this.mods.map(mod => mod[prop]))].filter(Boolean);
      
      // 转换为筛选选项格式
      return uniqueValues.map(value => ({
        text: value,
        value: value
      }));
    },
    formatUpdateToDate(updateTo) {
      if (!updateTo) return '';
      
      // 如果是字符串，尝试格式化
      if (typeof updateTo === 'string') {
        // 移除所有非数字字符
        const numericDate = updateTo.replace(/\D/g, '');
        
        // 确保至少有8位数字（YYYYMMDD）
        if (numericDate.length >= 8) {
          const year = numericDate.substring(0, 4);
          const month = numericDate.substring(4, 6);
          const day = numericDate.substring(6, 8);
          return `${year}.${month}.${day}`;
        }
      }
      
      return updateTo;
    },
     // 修改筛选方法，添加对 updateTo 的处理
    filterHandler(value, row, column) {
      const property = column.property || column.columnKey;
      
      // 更新筛选状态
      if (!this.columnFilters[property]) {
        this.columnFilters[property] = [];
      }
      
      // 如果值不在筛选列表中，添加它
      if (!this.columnFilters[property].includes(value)) {
        this.columnFilters[property].push(value);
      }
      
      return true; // 返回true，因为我们在computed中处理筛选
    },
    
    // 标签筛选处理函数
    filterTagHandler(value) {
      // 更新筛选状态
      if (!this.columnFilters['tag']) {
        this.columnFilters['tag'] = [];
      }
      
      // 如果值不在筛选列表中，添加它
      if (!this.columnFilters['tag'].includes(value)) {
        this.columnFilters['tag'].push(value);
      }
      
      return true; // 返回true，因为我们在computed中处理筛选
    },
  }
};
</script>

<style>
.mod-manager-container {
  max-width: 1500px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eaeaea;
}

.header h1 {
  margin: 0;
  color: #409EFF;
  font-size: 28px;
}

.search-bar {
  display: flex;
  align-items: center;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.mod-name {
  font-weight: bold;
  color: #303133;
}

.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.mod-tag {
  margin-right: 5px;
}

.file-count {
  font-size: 14px;
  color: #606266;
}

.file-item {
  display: block;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  flex: 1;
}

.file-source {
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}

.file-mode {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.file-mode-params {
  font-size: 12px;
  color: #909399;
  margin-left: 5px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.file-content-container {
  background-color: #f8f8f8;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
}

.file-content-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

/* 美化表格 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-table th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: bold;
}

.el-table--border th, .el-table--border td {
  border-right: 1px solid #ebeef5;
}

/* 美化按钮 */
.el-button {
  border-radius: 4px;
  font-weight: 500;
}

.el-button--primary {
  background-color: #409EFF;
}

.el-button--primary:hover {
  background-color: #66b1ff;
}

/* 美化对话框 */
.el-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.el-dialog__header {
  background-color: #f5f7fa;
  padding: 15px 20px;
}

.el-dialog__title {
  font-weight: bold;
  color: #303133;
}

.el-dialog__body {
  padding: 20px;
}

/* 美化折叠面板 */
.el-collapse {
  border: none;
}

.el-collapse-item__header {
  background-color: #f5f7fa;
  padding: 0 15px;
  border-radius: 4px;
  height: 40px;
  line-height: 40px;
}

.el-collapse-item__content {
  padding: 15px;
  background-color: #fafafa;
  border-radius: 0 0 4px 4px;
}

/* 添加导出对话框样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.footer {
  margin-top: 30px;
  text-align: center;
  color: #606266;
  padding: 20px 0;
  border-top: 1px solid #eaeaea;
}

.footer a {
  color: #409EFF;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}

.mod-source-info {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.source-link {
  color: #409EFF;
  text-decoration: none;
}

.source-link:hover {
  text-decoration: underline;
}

.source-link-icon {
  margin-left: 8px;
  color: #409EFF;
  font-size: 14px;
}

.source-link {
  color: #409EFF;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 5px;
}

.source-link:hover {
  text-decoration: underline;
}

.source-link .el-icon-link {
  font-size: 14px;
}

.zip-file-notice {
  padding: 15px;
  background-color: #f0f9eb;
  border-radius: 4px;
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.zip-file-notice .el-icon-info {
  font-size: 18px;
}

.mod-name {
  font-weight: bold;
  color: #303133;
  cursor: default;
  display: flex;
  align-items: center;
}

.mod-name.has-remark {
  cursor: pointer;
}

.mod-name.has-remark:hover {
  color: #409EFF;
}

.remark-icon {
  margin-left: 5px;
  font-size: 14px;
  color: #909399;
}

.mod-name-header {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eaeaea;
}

.remark-content-container {
  background-color: #f8f8f8;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
}

.remark-content-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
}

.operation-guide {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f0f9eb;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.operation-guide p {
  margin: 0;
  font-weight: bold;
  color: #67c23a;
}

.guide-content {
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

/* 优化Mod管理链接样式 */
.mod-manager-link {
  font-size: 0.85rem;
  color: #606266;
  text-decoration: none;
  padding: 4px 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 添加 updateTo 相关样式 */
.update-to-tag {
  margin-left: 8px;
  font-size: 10px;
  padding: 0 4px;
  height: 18px;
  line-height: 16px;
}

.update-to-info {
  margin-top: 4px;
  font-size: 12px;
}

/* Git安装提示对话框样式 */
.git-install-content {
  padding: 15px;
  background-color: #f8f8f8;
  border-radius: 4px;
  margin-bottom: 15px;
}

.git-install-content p {
  margin-top: 0;
  margin-bottom: 15px;
}

.git-install-checkbox {
  margin-top: 20px;
}

/* 补丁文件详情样式 */
.patch-details-dialog .el-dialog__body {
  padding: 0 20px;
}

.patch-content-container {
  max-height: 70vh;
  overflow: auto;
}

/* diff2html 自定义样式 */
:deep(.d2h-file-header) {
  background-color: #f8f9fa;
  padding: 10px;
  border-bottom: 1px solid #e1e4e8;
}

:deep(.d2h-file-list) {
  margin-bottom: 20px;
}

:deep(.d2h-file-name) {
  color: #24292e;
  font-weight: bold;
}

:deep(.d2h-code-line) {
  padding: 4px 10px;
}

:deep(.d2h-code-side-line) {
  padding: 4px 10px;
}


.patch-files-list {
  max-height: 60vh;
  overflow-y: auto;
}

.patch-file-dialog .el-dialog__body {
  padding: 10px 20px;
}

.diff2html-wrapper {
  max-height: 70vh;
  overflow: auto;
}

.patch-files-container {
  max-height: 60vh;
  overflow: auto;
}

.patch-search-input {
  margin-bottom: 15px;
}

.patch-tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.is-directory {
  font-weight: bold;
  color: #606266;
}

.el-tree-node__content {
  height: 32px;
}

/* 在样式部分添加以下代码 */
.scrollable-table {
  overflow-y: auto;
  scrollbar-width: thin;
}

.scrollable-table::-webkit-scrollbar {
  width: 8px;
}

.scrollable-table::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.scrollable-table::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.scrollable-table::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 确保表格卡片有足够的高度 */
.table-card {
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

/* 确保表格填充卡片空间 */
.table-card .el-card__body {
  flex: 1;
  padding: 10px;
  display: flex;
  flex-direction: column;
}
/* 可以添加一些FAQ相关的样式 */
.operation-guide .el-button {
  margin-right: 10px;
}
</style>

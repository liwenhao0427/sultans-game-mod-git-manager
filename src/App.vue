 <template>
  <div class="mod-manager-container">   
    <div class="header">
      <h1>苏丹的游戏 MOD 管理器</h1>
          <!-- 添加操作指引 -->
      <div class="operation-guide">
        <p>快速开始：勾选需要的MOD并点击“导出选中”按钮。</p>
        <el-button type="text" @click="showGuideDialog">查看详细操作指引</el-button>
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
          <li>程序会在当前目录下生成缓存文件game_path_config.json缓存游戏路径和游戏更新时间，下次默认使用缓存操作</li>
          <li>每次运行程序，都会先使用备份还原游戏文件，再进行mod安装操作，游戏备份目录在config同级bak目录下</li>
          <li>游戏更新后，点击运行mod会清除之前的备份文件</li>
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
      <div class="guide-content">
        <ol>
          <h3>MOD加载器工作流程：</h3>
            <el-image
              ref="workflowImage"
              :src="require('@/assets/check.png')"
              :preview-src-list="[require('@/assets/check.png')]"
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

    <el-card class="table-card">
      <el-table
        ref="table"
        :data="paginatedData"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        @filter-change="handleFilterChange"
        :default-sort="{prop: 'recommend', order: 'descending'}"
        v-loading="loading"
        row-key="name"
        stripe
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

      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[5, 10, 20, 50]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredMods.length"
          background
        />
      </div>
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
    
    <!-- 修改为补丁文件详情对话框 -->
    <el-dialog
      title="补丁文件详情"
      v-model="patchDetailsVisible"
      width="80%"
      class="patch-details-dialog"
      destroy-on-close
    >
      <div v-if="currentModName" class="mod-name-header">
        <h3>{{ currentModName }}</h3>
        <div v-if="currentModSource" class="mod-source-info">
          <span>来源: </span>
          <a :href="currentModSource.url" target="_blank" class="source-link">{{ currentModSource.name || currentModSource.url }}</a>
        </div>
      </div>
      <div class="patch-content-container" ref="patchContentContainer" @scroll="handlePatchContentScroll">
        <div v-if="patchContentLoading" class="patch-loading">
          <el-loading :visible="true" text="加载补丁内容中..."></el-loading>
        </div>
        <pre v-else>{{ displayedPatchContent }}</pre>
        <div v-if="hasMorePatchContent" class="load-more-indicator">
          <el-button type="text" @click="loadMorePatchContent">加载更多内容</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="patchDetailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <div class="footer">
      <p>苏丹的游戏 MOD 管理器 &copy; 2025 by <a href="https://github.com/liwenhao0427/sultans-game-mod-git-manager" target="_blank">liwenhao0427</a></p>
    </div>
  </div>
</template>

<script>
import JSZip from "jszip";
import { saveAs } from "file-saver";
// Remove the unused import
// import { Search } from '@element-plus/icons-vue';

export default {
  name: 'App',
  components: {
    // Remove the unused component registration
    // Search
  },
  data() {
    return {
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
        includeScript: false, // 默认不包含脚本
        includeTextLoader: false, // 默认不包含文本加载器
        fileName: 'mods.zip'
      },
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
  methods: {
    // 新增查看补丁文件方法
    async viewPatchFile(mod) {
      this.currentModName = mod.name;
      this.currentModSource = mod.source || null;
      this.patchContentLoading = true;
      this.patchDetailsVisible = true;
      this.fullPatchContent = '';
      this.displayedPatchContent = '';
      this.currentPatchContentPosition = 0;
      
      try {
        // 加载补丁文件内容
        const patchContent = await this.getPatchFileContent(mod);
        this.fullPatchContent = patchContent;
        
        // 初始加载部分内容
        this.loadInitialPatchContent();
      } catch (error) {
        console.error('加载补丁文件失败:', error);
        this.displayedPatchContent = '加载补丁文件失败: ' + error.message;
      } finally {
        this.patchContentLoading = false;
      }
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
    // 处理表格筛选变化
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
      
      // 重置到第一页
      this.currentPage = 1;
    },
    // 显示导出对话框
    showExportDialog() {
      // 设置默认文件名
      this.exportOptions.fileName = `mods_${this.selectedMods.length}.zip`;
      this.exportDialogVisible = true;
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
    async exportSelected() {
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
          const mainAppPath = require('!!file-loader?esModule=false!@/assets/苏丹的游戏mod管理器.exe');
          const mainAppResponse = await fetch(mainAppPath);
          const mainAppBlob = await mainAppResponse.blob();
          zip.file('苏丹的游戏mod管理器.exe', mainAppBlob);
        } catch (error) {
          console.error('主程序加载出错:', error);
          this.$message.warning('无法加载主程序文件，但Mod文件将正常导出');
        }
      }
      
      // 根据选项添加文本加载器
      if (this.exportOptions.includeTextLoader) {
        try {
          const textLoaderPath = require('!!file-loader?esModule=false!@/assets/加载本地Mods配置.exe');
          const textLoaderResponse = await fetch(textLoaderPath);
          const textLoaderBlob = await textLoaderResponse.blob();
          zip.file('加载本地Mods配置.exe', textLoaderBlob);
        } catch (error) {
          console.error('文本加载器加载出错:', error);
          this.$message.warning('无法加载本地加载器文件，但其他文件将正常导出');
        }
      }
      
      // 根据选项添加安装脚本
      if (this.exportOptions.includeScript) {
        try {
          const scriptPath = require('!!raw-loader?esModule=false!@/assets/mod_installer.py');
          zip.file('mod_installer.py', scriptPath);
        } catch (error) {
          console.error('安装脚本加载出错:', error);
          this.$message.warning('无法加载安装脚本，但其他文件将正常导出');
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
            
            this.$message.success(`已添加补丁文件: ${mod.name}/${patchFileName}`);
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
    handleSizeChange(val) {
      this.pageSize = val;
      this.currentPage = 1;
    },
    handleCurrentChange(val) {
      this.currentPage = val;
    },
    handleSearchClear() {
      this.searchQuery = '';
    },
    resetFilters() {
      // 先清空搜索和筛选状态
      this.searchQuery = '';
      this.currentPage = 1;
      this.columnFilters = {}; // 清空所有筛选状态
      
      // 使用nextTick确保状态更新后再操作DOM
      this.$nextTick(() => {
        if (this.$refs.table) {
          try {
            // 获取表格实例
            const table = this.$refs.table;
            
            // 清除所有列的筛选
            const columnKeys = ['author', 'gameVersion', 'tag'];
            columnKeys.forEach(key => {
              table.clearFilter(key);
            });
            
            // 强制更新表格数据
            this.$forceUpdate();
            
            // 额外延时确保UI更新
            setTimeout(() => {
              // 再次强制更新组件
              this.$forceUpdate();
              // 重新布局表格
              table.doLayout();
            }, 200);
          } catch (error) {
            console.warn('清除表格筛选时出错:', error);
          }
        }
      });
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

</style>

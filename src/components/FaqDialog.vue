<template>
    <el-dialog
      title="常见问题解答 (FAQ)"
      v-model="dialogVisible"
      width="60%"
      class="faq-dialog"
    >
      <div class="faq-content">
        <el-collapse accordion>
          <el-collapse-item v-for="(item, index) in faqItems" :key="index" :title="item.question" :name="index">
            <div class="faq-answer" v-html="item.answer"></div>
            <!-- 添加图片显示区域 -->
            <div v-if="item.images && item.images.length > 0" class="faq-images">
              <div v-for="(image, imgIndex) in item.images" :key="imgIndex" class="faq-image-container">
                <img :src="image.src" :alt="image.alt || '说明图片'" @click="showImagePreview(image.src)" />
                <div class="image-caption" v-if="image.caption">{{ image.caption }}</div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <!-- 图片预览对话框 -->
      <el-dialog
        v-model="imagePreviewVisible"
        append-to-body
        :show-close="true"
        class="image-preview-dialog"
        width="80%"
      >
        <img :src="previewImageSrc" class="preview-image" alt="预览图片" />
      </el-dialog>
      
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </template>
  
  <script>
  export default {
    name: 'FaqDialog',
    props: {
      visible: {
        type: Boolean,
        default: false
      }
    },
    data() {
      return {
        dialogVisible: false,
        imagePreviewVisible: false,
        previewImageSrc: '',
        faqItems: [
          {
            question: "如何安装MOD？",
            answer: `
              <ol>
                <li>在MOD列表中选择您想要安装的MOD（可以多选）</li>
                <li>点击"导出选中"按钮</li>
                <li>在弹出的对话框中选择导出选项（首次使用建议勾选"MOD管理器"）</li>
                <li>解压下载的文件到任意目录</li>
                <li>运行"苏丹的游戏mod管理器.exe"</li>
                <li>程序会自动安装选中的MOD</li>
              </ol>
            `,
            images: [
            //   { 
            //     src: require('@/assets/images/faq/mod_selection.png'), 
            //     alt: "选择MOD", 
            //     caption: "选择您想要安装的MOD" 
            //   },
            //   { 
            //     src: require('@/assets/images/faq/export_dialog.png'), 
            //     alt: "导出对话框", 
            //     caption: "导出对话框选项" 
            //   }
            ]
          },
          {
            question: "MOD管理器有好多红色提示报安装失败？",
            answer: `
              <p>如果安装了很多Mod的话，其中几个Mod之前存在冲突是很有可能的，放心，这些安装失败的Mod已经被清除了，如果您仍然可以正常启动，则无需太过在意这些提示，这仅仅是没有安装成功几个Mod，不影响游戏运行</p>
              <p>如果您仍然希望同时安装这些Mod，以下是几种方案：</p>
              <ul>
                <li>管理器会为安装失败的Mod创建fail前缀的分支，使用TortoiseGit或其他工具将对应分支合并到当前分支，此时通常会提示冲突，请双击红色的冲突文件，在窗口中尝试解决冲突，详细说明请见下一条QA</li>
                <li>管理器会提示和该Mod冲突的其他Mod名称，尝试先移除这些其他Mod后重新运行Mod管理器</li>
                <li>如果您仅需要使用该Mod，可以直接切换到对应Mod分支，这通常不会带来更多问题</li>
              </ul>
            `
          },
          {
            question: "我想要自己解决冲突，应该怎么做？",
            answer: `
              <p>该操作需要一定动手能力和对游戏配置文件的理解</p>
              <ul>
                <li>选择帮助选项7，打开游戏配置目录</li>
                <li>空白处右键，选择TortoiseGit => 合并(M)，在从分支(B)中选择你需要合并的fail分支，点击确定</li>
                <li>不用管冲突提示，可以勾选不再提醒，点击左下角的解决按钮</li>
                <li><b>双击红色的冲突文件，进入冲突解决窗口</b></li>
                <li>左边文件为:有冲突的Mod文件,右边为本地文件(也就是你当前修改的文件)</li>
                <li>下边的文件是你合并操作后的文件,所以你要对比左右文件的差异:</li>
                <li>使用此文本块：即使用你觉得正确的那部分代码</li>
                <li>使用整个文件：即完全使用当前的文件或者Mod文件，通常如果Mod的修改内容和已有的Mod功能重复，推荐完全使用当前文件</li>
                <li>优先使用右侧文本块：即对于冲突逻辑，先使用当前代码，再使用冲突Mod代码，如果你看到Mod是以数组类型插入项，可以尝试使用该项</li>
                <li>你可以在上方选择（上一冲突、下一冲突）来快速跳转到冲突的部分代码查看</li>
                <li>直到下方文件已不再有红色问号，点击保存或快捷键ctrl+s，看到“文件已没有冲突”后点击标记为解决，即解决了该文件的冲突</li>
                <li>所有文件冲突解决后，右键=>Git提交=》提交，即可应用该失败Mod，弹出的窗口可以选择不再提示（忽略），后面的弹窗关闭即可</li>
                <li>你可以继续合并其他失败分支，解决冲突</li>
                <li>当你觉得一个Mod的冲突太多，无法解决时，请右键TortoiseGit => 中止冲突 => 硬重置 => 确定以放弃合并该Mod</li>
              </ul>
            `
          },
          {
            question: "MOD安装后游戏启动失败，卡在梅姬祈祷中怎么办？",
            answer: `
              <p>可能的原因和解决方案：</p>
              <ol>
                <li>回忆初始化仓库时是否安装了其他Mod，导致初始化的仓库并不是干净的游戏配置：
                    可以尝试在帮助程序中选择"重置游戏到纯净状态"选项来还原到安装前状态；
                    也可以尝试使用"从Gitee仓库恢复游戏配置"来使用作者的游戏仓库</li>
                <li>MOD与游戏版本不兼容：检查MOD的游戏版本是否与您的游戏版本一致</li>
                <li>MOD之间存在冲突或者MOD本身存在错误：尝试减少安装的MOD数量，逐个排查</li>
                <li>如果以上方法都无效，可以尝试删除游戏配置目录后验证Steam游戏文件完整性或者卸载后重新下载</li>
              </ol>
            `
          },
          {
            question: "我可以用MOD管理器管理其他渠道下载的MOD吗？",
            answer: `
              <p>当然可以！</p>
              <p>请确保：</p>
              <ol>
                <li>MOD与游戏版本兼容</li>
                <li>MOD文件夹应该放在和Mod管理器同级目录的Mods目录下</li>
                <li>MOD文件夹对应游戏的config目录，你下载的MOD文件夹的下一级通常可能存在event、rite、loot、init等目录，或者cards.json、upgrade.json等常见的修改配置文件</li>
              </ol>
            `
          },
          {
            question: "你这网站Mod好少？",
            answer: `
              <p>精力有限，只搬运了一些看到的Mod，如果需要使用从渠道渠道下载的Mod，见上一条说明</p>
              <p>该项目主要实现使用Git管理苏丹的游戏Mod，主要提供Mod管理器下载，网站只是简单显示方便使用，提供的Mod仅供操作演示，没有作为平台提供Mod的打算</p>
            `
          },
          {
            question: "为什么有些MOD显示'不支持最新游戏版本'？",
            answer: `
              <p>这表示该MOD是为游戏的旧版本开发的，可能与最新版本不兼容。原因可能是：</p>
              <ul>
                <li>游戏更新改变了MOD修改的文件结构、空格等导致补丁无法应用</li>
                <li>MOD作者尚未更新MOD以适配新版本</li>
                <li>MOD功能在新版本游戏中已经被官方实现或改变</li>
              </ul>
              <p>您仍然可以通过删除 modConfig.json 文件中的 updateTo 字段来尝试安装这些MOD，但可能会导致游戏崩溃或功能异常。</p>
              <p>推荐的做法是在网站中查看补丁修改的文件内容，自行修改。</p>
            `
          },
          {
            question: "Mac电脑打不开exe管理器文件",
            answer: `
              <p>请选择包含安装脚本的选项，在对于目录命令行运行 python3 mod_installer.py </p>
            `
          },
          {
            question: "我打不开网站",
            answer: `
              <p> ？ </p>
              <p> 如果网站打不开，也可以通过下载网站到本地，解压后打开 index.html 的形式本地运行网站 </p>
              <p> 下载地址： https://gitee.com/notnow/sultans-game-mod-git-manager/repository/archive/gh-pages.zip </p>
            `
          },
          {
            question: "会持续更新吗？",
            answer: `
              <p>工具主要更新到我认为比较完善为止，网站上的Mod可能不会频繁更新，不过随时欢迎<a href="https://github.com/liwenhao0427/sultans-game-mod-git-manager/pulls">PR</a></p>
              <p>之后请自行去各个渠道下载Mod，在本地就可以通过在文件夹中移动Mod文件夹的形式管理安装Mod了</p>
            `
          },
        ]
      };
    },
    watch: {
      visible(val) {
        this.dialogVisible = val;
      },
      dialogVisible(val) {
        this.$emit('update:visible', val);
      }
    },
    methods: {
      // 显示图片预览
      showImagePreview(src) {
        this.previewImageSrc = src;
        this.imagePreviewVisible = true;
      }
    }
  };
  </script>
  
  <style scoped>
  .faq-dialog {
    max-width: 800px;
  }
  
  .faq-content {
    max-height: 70vh;
    overflow-y: auto;
    padding: 0 10px;
  }
  
  .faq-answer {
    padding: 10px;
    background-color: #f9f9f9;
    border-radius: 4px;
    line-height: 1.6;
  }
  
  .faq-answer ul, .faq-answer ol {
    padding-left: 20px;
    margin: 10px 0;
  }
  
  .faq-answer li {
    margin-bottom: 8px;
  }
  
  /* 添加图片相关样式 */
  .faq-images {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-top: 15px;
  }
  
  .faq-image-container {
    width: calc(50% - 10px);
    border: 1px solid #eaeaea;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .faq-image-container img {
    width: 100%;
    height: auto;
    cursor: pointer;
    transition: transform 0.3s;
  }
  
  .faq-image-container img:hover {
    transform: scale(1.02);
  }
  
  .image-caption {
    padding: 8px;
    text-align: center;
    background-color: #f5f5f5;
    color: #666;
    font-size: 0.9em;
  }
  
  /* 图片预览样式 */
  .image-preview-dialog :deep(.el-dialog__body) {
    padding: 10px;
    text-align: center;
  }
  
  .preview-image {
    max-width: 100%;
    max-height: 80vh;
  }
  
  @media (max-width: 768px) {
    .faq-image-container {
      width: 100%;
    }
  }
  </style>
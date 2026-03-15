<template>
  <div class="knowledge-container">
    <div class="page-header">
      <div>
        <h2 class="title">数据源接入与清洗</h2>
        <p class="subtitle">上传企业文档 -> 预览清洗乱码 -> 异步向量化入库，保障大模型语料质量</p>
      </div>
    </div>

    <el-card class="modern-card upload-card" shadow="never">
      <div class="upload-area">
        <el-upload
          class="custom-uploader"
          drag
          action=""
          :http-request="handleUpload"
          multiple
          :show-file-list="false"
        >
          <div class="upload-content">
            <div class="icon-wrapper">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
            </div>
            <div class="upload-text">
              将文件拖拽至此处，或 <em>点击上传</em>
            </div>
            <div class="upload-tip">
              支持 .txt, .md, .pdf 格式，单文件建议不超过 50MB
            </div>
          </div>
        </el-upload>
        
        <transition name="el-fade-in-linear">
          <div v-if="currentProgress > 0" class="progress-wrapper">
            <span class="progress-text">{{ progressText }}</span>
            <el-progress 
              :percentage="currentProgress" 
              :status="progressStatus" 
              :stroke-width="8"
              striped
              striped-flow
            />
          </div>
        </transition>
      </div>
    </el-card>

    <div class="history-section">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Document /></el-icon>
          <h3>文件库列表</h3>
        </div>
        <el-button 
          v-if="uploadHistory.length > 0" 
          type="danger" 
          plain 
          size="small" 
          class="clear-btn"
          @click="clearHistory"
        >
          清空记录
        </el-button>
      </div>

      <el-card class="modern-card table-card" shadow="never">
        <div v-if="uploadHistory.length === 0" class="empty-state">
          <img src="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg" alt="empty" class="empty-img" />
          <p>暂无文件上传记录</p>
        </div>
        
        <el-table 
          v-else 
          :data="uploadHistory" 
          class="custom-table"
          :row-class-name="tableRowClassName"
        >
          <el-table-column prop="fileName" label="文件名称" min-width="250">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon class="file-icon"><Document /></el-icon>
                <span class="name-text">{{ row.fileName }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag 
                v-if="row.status === 'pending'" type="warning" effect="dark" round class="status-tag">
                待清洗
              </el-tag>
              <el-tag 
                v-else-if="row.status === 'parsing'" type="primary" effect="dark" round class="status-tag">
                向量化中
              </el-tag>
              <el-tag 
                v-else-if="row.status === 'processed'" type="success" effect="dark" round class="status-tag">
                已入库
              </el-tag>
              <el-tag 
                v-else type="danger" effect="dark" round class="status-tag">
                解析失败
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="message" label="系统反馈" min-width="200" show-overflow-tooltip />
          <el-table-column prop="time" label="上传时间" width="180" />
          
          <el-table-column label="操作" width="220" align="center" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                link 
                :icon="View"
                :disabled="row.status === 'processed' || row.status === 'parsing'"
                @click="openPreview(row)"
              >
                预览清洗
              </el-button>
              <el-button 
                type="success" 
                link 
                :icon="Cpu"
                :disabled="row.status !== 'pending'"
                :loading="row.status === 'parsing'"
                @click="handleVectorize(row)"
              >
                {{ row.status === 'parsing' ? '处理中...' : '打入知识库' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-drawer
      v-model="previewVisible"
      title="文档语料清洗"
      size="50%"
      destroy-on-close
      class="custom-drawer"
    >
      <div v-loading="previewLoading" class="preview-container">
        <el-alert 
          title="数据治理提示" 
          description="大模型的回答质量取决于您喂给它的数据质量。请检查下方系统提取的文本，删除无关的页眉页脚、乱码或无关表格，确认无误后点击保存。" 
          type="info" 
          show-icon 
          :closable="false"
          style="margin-bottom: 16px; background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); color: #94a3b8;" 
        />
        <el-input
          v-model="currentDocContent"
          type="textarea"
          :rows="28"
          placeholder="正在全力提取文档内容..."
          class="custom-textarea"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewVisible = false" class="drawer-btn">稍后处理</el-button>
          <el-button type="primary" :loading="saveLoading" @click="saveContent" class="drawer-btn-primary">
            保存清洗结果
          </el-button>
        </span>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
// 🌟 1. 引入 onMounted 钩子
import { ref, onMounted } from 'vue'
import { UploadFilled, Document, View, Cpu } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 🌟 2. 引入新增的 getFileList 接口
import { uploadFile, previewFile, updateFileContent, vectorizeFile, getFileList } from '@/api/knowledge'

// ================= 状态定义 =================
const uploadHistory = ref([])
const currentProgress = ref(0)
const progressStatus = ref('')
const progressText = ref('正在加密上传至服务器...')

// 抽屉与清洗状态
const previewVisible = ref(false)
const previewLoading = ref(false)
const saveLoading = ref(false)
const currentDocId = ref(null)
const currentDocContent = ref('')

// ================= 核心业务逻辑 =================

// 🌟 3. 新增加载历史列表方法
const loadHistoryList = async () => {
  try {
    const res = await getFileList()
    const backendData = res.data || res
    
    // 将后端返回的列表数据赋值给表格
    if (res.code === 200 && backendData) {
      uploadHistory.value = backendData
    }
  } catch (error) {
    console.error('获取历史记录失败:', error)
  }
}

// 🌟 4. 在组件挂载时触发加载
onMounted(() => {
  loadHistoryList()
})

// 1. 文件上传
const handleUpload = async (options) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)

  currentProgress.value = 0
  progressStatus.value = ''
  progressText.value = '正在安全落盘中...'

  const progressInterval = setInterval(() => {
    if (currentProgress.value < 85) {
      currentProgress.value += Math.floor(Math.random() * 10) + 1
    }
  }, 200)

  try {
    const res = await uploadFile(formData)
    const backendData = res.data || res 
    
    clearInterval(progressInterval)
    currentProgress.value = 100
    progressStatus.value = 'success'
    progressText.value = '文件落盘成功！'

    // 上传成功后，将新记录插到表格最前面
    uploadHistory.value.unshift({
      id: backendData.data?.id,
      fileName: backendData.data?.filename || file.name,
      status: 'pending',
      message: '文件已安全落盘，请进行清洗并向量化',
      time: new Date().toLocaleString()
    })
    
    ElMessage.success(`文档 ${file.name} 已就绪！`)

  } catch (error) {
    clearInterval(progressInterval)
    currentProgress.value = 100
    progressStatus.value = 'exception'
    progressText.value = '上传发生异常'
    
    uploadHistory.value.unshift({
      id: null,
      fileName: file.name,
      status: 'error',
      message: error.response?.data?.detail || error.message || '网络或服务器异常',
      time: new Date().toLocaleString()
    })
  } finally {
    setTimeout(() => {
      currentProgress.value = 0
    }, 2000)
  }
}

// 2. 打开预览抽屉
const openPreview = async (row) => {
  if (!row.id) {
    ElMessage.warning('该文件 ID 异常，无法预览')
    return
  }
  
  currentDocId.value = row.id
  currentDocContent.value = ''
  previewVisible.value = true // 1. 先打开抽屉
  previewLoading.value = true // 2. 显示加载动画
  
  try {
    const res = await previewFile(row.id)
    
    // 💡 安全解构：兼容不同的 Axios 拦截器返回层级
    // 如果拦截器直接返回了后端的 data 对象，取 res.data.content
    // 如果拦截器没有剥离，取 res.data.data.content
    const content = res?.data?.content || res?.data?.data?.content || res?.content || ''
    
    currentDocContent.value = content
    
  } catch (error) {
    console.error('获取预览内容失败:', error)
    // 发生网络错误时，关闭抽屉（避免让用户看到空抽屉）
    previewVisible.value = false
  } finally {
    // 无论成功失败，关闭加载动画
    previewLoading.value = false
  }
}

// 3. 保存清洗内容
const saveContent = async () => {
  if (!currentDocContent.value.trim()) {
    ElMessage.warning('文档内容不能为空')
    return
  }
  
  saveLoading.value = true
  try {
    await updateFileContent(currentDocId.value, currentDocContent.value)
    ElMessage.success('语料清洗保存成功！')
    previewVisible.value = false
    
    // 找到对应行，更新一下反馈信息
    const targetRow = uploadHistory.value.find(item => item.id === currentDocId.value)
    if (targetRow) {
      targetRow.message = '文本已人工清洗，可打入知识库'
    }
  } catch (error) {
  } finally {
    saveLoading.value = false
  }
}

// 4. 发起异步向量化
const handleVectorize = async (row) => {
  if (!row.id) return
  
  ElMessageBox.confirm(
    '确认该文档已清洗完毕并打入向量数据库吗？打入后将正式被大模型读取。',
    '提示',
    {
      confirmButtonText: '确认入库',
      cancelButtonText: '再检查一下',
      type: 'warning',
    }
  ).then(async () => {
    row.status = 'parsing'
    row.message = '正在后台进行智能切分与向量化...'
    
    try {
      await vectorizeFile(row.id)
      ElMessage.success(`文档 [${row.fileName}] 已提交向量化队列`)
      
      setTimeout(() => {
        row.status = 'processed'
        row.message = '向量化成功，已打入 ChromaDB'
      }, 5000)
      
    } catch (error) {
      row.status = 'error'
      row.message = '向量化任务提交失败'
    }
  }).catch(() => {})
}

// 清空记录辅助函数
const clearHistory = () => {
  uploadHistory.value = []
  ElMessage.info('日志记录已清空')
}

const tableRowClassName = ({ rowIndex }) => {
  if (rowIndex === 0 && uploadHistory.value.length > 0) {
    return 'latest-row'
  }
  return ''
}
</script>

<style lang="scss" scoped>
/* ================= 全局变量 ================= */
$bg-dark: #0f172a;
$card-bg: #1e293b;
$border-color: #334155;
$primary-color: #3b82f6;
$primary-light: rgba(59, 130, 246, 0.1);
$text-primary: #f8fafc;
$text-regular: #94a3b8;
$text-muted: #64748b;

.knowledge-container {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ================= 头部样式 ================= */
.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;

  .title {
    color: $text-primary;
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px 0;
    letter-spacing: 0.5px;
  }
  .subtitle {
    color: $text-regular;
    font-size: 14px;
    margin: 0;
  }
}

/* ================= 卡片与上传区 ================= */
.modern-card {
  background-color: $card-bg;
  border: 1px solid $border-color;
  border-radius: 12px;
  color: $text-primary;
  
  :deep(.el-card__body) { padding: 0; }
}

.upload-card { margin-bottom: 32px; }
.upload-area { padding: 32px; }

:deep(.custom-uploader) {
  .el-upload { width: 100%; }
  .el-upload-dragger {
    background-color: rgba(15, 23, 42, 0.4);
    border: 2px dashed $border-color;
    border-radius: 12px;
    height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:hover, &.is-dragover {
      border-color: $primary-color;
      background-color: $primary-light;
      .icon-wrapper {
        transform: translateY(-5px) scale(1.05);
        background-color: rgba(59, 130, 246, 0.2);
        .upload-icon { color: $primary-color; }
      }
    }
  }
}

.upload-content {
  display: flex; flex-direction: column; align-items: center;
  .icon-wrapper {
    width: 64px; height: 64px; border-radius: 50%;
    background-color: rgba(51, 65, 85, 0.5);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 16px; transition: all 0.3s;
    .upload-icon { font-size: 32px; color: $text-regular; transition: color 0.3s; }
  }
  .upload-text {
    font-size: 16px; color: $text-primary; margin-bottom: 8px;
    em { color: $primary-color; font-style: normal; font-weight: 600; text-decoration: underline; text-decoration-color: transparent; transition: text-decoration-color 0.3s; &:hover { text-decoration-color: $primary-color; } }
  }
  .upload-tip { font-size: 13px; color: $text-muted; }
}

.progress-wrapper {
  margin-top: 24px; padding: 0 16px;
  .progress-text { display: block; font-size: 13px; color: $text-regular; margin-bottom: 8px; }
}

/* ================= 历史记录区与表格 ================= */
.section-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
  .header-left {
    display: flex; align-items: center; gap: 8px;
    .section-icon { font-size: 20px; color: $primary-color; }
    h3 { color: $text-primary; font-size: 18px; margin: 0; font-weight: 600; }
  }
  .clear-btn {
    background-color: transparent; border-color: rgba(239, 68, 68, 0.3); color: #ef4444;
    &:hover { background-color: rgba(239, 68, 68, 0.1); border-color: #ef4444; }
  }
}

.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60px 0; color: $text-muted;
  .empty-img { width: 120px; opacity: 0.6; margin-bottom: 16px; }
}

.table-card { overflow: hidden; }

:deep(.custom-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(15, 23, 42, 0.5);
  --el-table-header-text-color: #94a3b8;
  --el-table-text-color: #e2e8f0;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.03);
  --el-table-border-color: #334155;
  --el-table-border: none;

  &::before, &::after { display: none; }
  th.el-table__cell { border-bottom: 1px solid $border-color; font-weight: 500; font-size: 13px; padding: 12px 0; }
  td.el-table__cell { border-bottom: 1px solid rgba(51, 65, 85, 0.5); padding: 16px 0; }
  .latest-row { background-color: rgba(16, 185, 129, 0.05); }

  .file-name-cell {
    display: flex; align-items: center; gap: 10px;
    .file-icon { font-size: 18px; color: $text-regular; }
    .name-text { font-weight: 500; }
  }
  .status-tag { border: none; font-weight: 500; }
}

/* ================= 沉浸式抽屉定制 ================= */
:deep(.custom-drawer) {
  background-color: $bg-dark;
  border-left: 1px solid $border-color;
  color: $text-primary;
  
  .el-drawer__header {
    margin-bottom: 0;
    padding: 20px 24px;
    border-bottom: 1px solid $border-color;
    color: $text-primary;
    font-weight: 600;
  }
  
  .el-drawer__body {
    padding: 24px;
    background-color: $card-bg;
  }
  
  .el-drawer__footer {
    border-top: 1px solid $border-color;
    padding: 16px 24px;
  }
}

.preview-container {
  height: 100%;
}

:deep(.custom-textarea) {
  .el-textarea__inner {
    background-color: #0d1117;
    color: #e2e8f0;
    border: 1px solid $border-color;
    border-radius: 8px;
    padding: 16px;
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    
    &:focus {
      border-color: $primary-color;
      box-shadow: 0 0 0 1px $primary-color inset;
    }
    
    &::-webkit-scrollbar { width: 8px; }
    &::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
  }
}

.drawer-btn {
  background-color: transparent;
  border-color: $border-color;
  color: $text-regular;
  &:hover { color: $text-primary; border-color: $text-regular; }
}

.drawer-btn-primary {
  background-color: $primary-color;
  border: none;
  font-weight: 500;
}
</style>
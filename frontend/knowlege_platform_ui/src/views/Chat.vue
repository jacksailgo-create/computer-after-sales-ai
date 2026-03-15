<template>
  <div class="chat-container">
    <div class="chat-box">
      <div class="chat-header">
        <div class="header-left">
          <el-icon class="header-icon"><Monitor /></el-icon>
          <h2>售后技术专家 AI</h2>
        </div>
        <el-button size="small" type="danger" plain @click="clearConversation">
          <el-icon><Delete /></el-icon> 清空会话
        </el-button>
      </div>

      <div class="messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="empty-state">
          <img src="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg" alt="empty" class="empty-img" />
          <h3>您可以这样提问：</h3>
          <div class="suggestion-tags">
            <el-tag effect="dark" round @click="fillInput('电脑开机一直蓝屏，错误代码 0x0000007B 怎么办？')">蓝屏 0x0000007B</el-tag>
            <el-tag effect="dark" round @click="fillInput('如何使用U盘安装Windows 7操作系统？')">U盘安装 Win7</el-tag>
            <el-tag effect="dark" round @click="fillInput('联想 ThinkPad 连不上 WiFi 怎么排查？')">无法连接 WiFi</el-tag>
          </div>
        </div>
        
        <div 
          v-for="(msg, index) in messages" 
          :key="index" 
          class="message-item"
          :class="msg.role"
        >
          <div class="avatar">
            <el-avatar 
              :icon="msg.role === 'user' ? User : Service" 
              :class="msg.role === 'user' ? 'avatar-user' : 'avatar-ai'" 
            />
          </div>

          <div class="content">
            <div class="bubble">
              <div v-if="msg.loading" class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
              
              <div v-else class="markdown-body" v-html="formatContent(msg.content)"></div>
            </div>

            <div v-if="msg.sources && msg.sources.length > 0" class="sources-area">
              <div class="sources-title"><el-icon><Link /></el-icon> 参考文档：</div>
              <div class="source-tags">
                <el-tag 
                  v-for="(source, sIdx) in msg.sources" 
                  :key="sIdx" 
                  size="small" 
                  type="info" 
                  effect="plain"
                  class="source-tag"
                >
                  {{ source }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <el-input
          v-model="input"
          placeholder="请输入您的售后问题... (Enter 发送，Shift + Enter 换行)"
          :rows="3"
          type="textarea"
          resize="none"
          @keydown.enter.prevent.exact="handleSend"
        />
        <el-button 
          type="primary" 
          class="send-btn" 
          @click="handleSend" 
          :loading="loading" 
          :disabled="!input.trim()"
        >
          <el-icon><Position /></el-icon> 发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { queryKnowledge } from '@/api/knowledge' 
import { User, Service, Position, Delete, Monitor, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

const input = ref('')
const loading = ref(false)
const messages = ref([])
const messagesRef = ref(null)

// 视图滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 清空历史对话
const clearConversation = () => {
  messages.value = []
  ElMessage.info('会话已清空')
}

// 点击推荐词自动发送
const fillInput = (text) => {
  input.value = text
  handleSend()
}

// 解析 Markdown
const formatContent = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

// 核心发送逻辑
const handleSend = async () => {
  if (!input.value.trim() || loading.value) return
  
  const question = input.value.trim()
  input.value = ''
  
  // 1. 压入用户提问
  messages.value.push({ role: 'user', content: question })
  scrollToBottom()
  
  // 2. 压入 AI 加载占位符
  const botMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', sources: [], loading: true })
  loading.value = true
  scrollToBottom()
  
  try {
    // 发起网络请求
    const res = await queryKnowledge({ query: question })
    
    // 🌟 终极防弹脱壳逻辑：自适应 Axios 的不同返回结构
    const backendData = res.code !== undefined ? res : res.data
    
    // 3. 校验业务状态码
    if (backendData && backendData.code === 200) {
      const businessData = backendData.data || {}
      messages.value[botMsgIndex].content = businessData.answer || '大模型返回了空内容'
      messages.value[botMsgIndex].sources = businessData.sources || []
    } else {
      messages.value[botMsgIndex].content = `⚠️ ${backendData?.message || '服务器返回异常，请稍后再试。'}`
    }
    
  } catch (error) {
    console.error('API 请求报错:', error)
    
    // 提取 FastAPI 抛出的 HttpException 详情
    const errorDetail = error.response?.data?.detail 
                     || error.response?.data?.message 
                     || error.message 
                     || '网络通讯出错，请检查后端服务是否启动。'
                     
    messages.value[botMsgIndex].content = `❌ 请求失败：${errorDetail}`
  } finally {
    loading.value = false
    messages.value[botMsgIndex].loading = false
    scrollToBottom()
  }
}
</script>

<style lang="scss" scoped>
/* 极客暗黑主题变量 */
$bg-dark: #0f172a;
$card-bg: #1e293b;
$border-color: #334155;
$primary-color: #3b82f6;
$text-primary: #f8fafc;
$text-regular: #94a3b8;
$ai-bubble: #273449;
$user-bubble: #3b82f6;

.chat-container {
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  max-width: 1000px;
  margin: 0 auto;
}

.chat-box {
  flex: 1;
  background-color: $bg-dark;
  border: 1px solid $border-color;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.chat-header {
  padding: 16px 24px;
  background-color: $card-bg;
  border-bottom: 1px solid $border-color;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .header-icon {
      font-size: 20px;
      color: $primary-color;
    }
    
    h2 {
      color: $text-primary;
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      letter-spacing: 1px;
    }
  }
}

.messages {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  scroll-behavior: smooth;
  
  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
  
  .empty-state {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    
    .empty-img { width: 150px; opacity: 0.5; margin-bottom: 20px; }
    h3 { color: $text-regular; font-weight: normal; margin-bottom: 16px; }
    
    .suggestion-tags {
      display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;
      .el-tag { 
        cursor: pointer; padding: 16px 20px; font-size: 14px; 
        background-color: rgba(59, 130, 246, 0.1); border-color: $primary-color; color: $primary-color;
        transition: all 0.3s;
        &:hover { background-color: $primary-color; color: #fff; transform: translateY(-2px); }
      }
    }
  }
}

.message-item {
  display: flex;
  margin-bottom: 28px;
  animation: fadeIn 0.3s ease-out;
  
  &.user {
    flex-direction: row-reverse;
    .content { align-items: flex-end; }
    .avatar { margin-left: 16px; margin-right: 0; }
    .bubble {
      background-color: $user-bubble;
      color: #fff;
      border-top-right-radius: 2px;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
  }
  
  &.assistant {
    .content { align-items: flex-start; }
    .avatar { margin-right: 16px; }
    .bubble {
      background-color: $ai-bubble;
      color: $text-primary;
      border: 1px solid $border-color;
      border-top-left-radius: 2px;
    }
  }
}

.avatar {
  .avatar-user { background-color: transparent; border: 2px solid $primary-color; color: $primary-color; }
  .avatar-ai { background-color: #10b981; color: #fff; }
}

.content {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  
  .bubble {
    padding: 12px 18px;
    border-radius: 12px;
    line-height: 1.6;
    font-size: 15px;
    word-break: break-word;
  }
}

/* 引用来源样式 */
.sources-area {
  margin-top: 8px;
  padding-left: 4px;
  
  .sources-title {
    font-size: 12px;
    color: $text-regular;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .source-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    
    .source-tag {
      background-color: rgba(51, 65, 85, 0.5);
      border: 1px solid $border-color;
      color: #cbd5e1;
      border-radius: 6px;
    }
  }
}

/* Markdown 渲染定制样式 */
.markdown-body {
  :deep(p) { margin: 0 0 12px 0; &:last-child { margin-bottom: 0; } }
  :deep(a) { color: #60a5fa; text-decoration: none; &:hover { text-decoration: underline; } }
  :deep(ul), :deep(ol) { padding-left: 20px; margin: 8px 0; }
  :deep(li) { margin-bottom: 4px; }
  :deep(code) {
    background-color: rgba(0, 0, 0, 0.3);
    color: #fca5a5;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Fira Code', monospace;
    font-size: 0.9em;
  }
  :deep(pre) {
    background-color: #0d1117;
    border: 1px solid $border-color;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    
    code { background-color: transparent; color: #e2e8f0; padding: 0; }
  }
  :deep(table) {
    width: 100%; border-collapse: collapse; margin: 12px 0;
    th, td { border: 1px solid $border-color; padding: 8px 12px; }
    th { background-color: rgba(255, 255, 255, 0.05); }
  }
}

/* 输入区样式 */
.input-area {
  padding: 20px 24px;
  background-color: $card-bg;
  border-top: 1px solid $border-color;
  display: flex;
  gap: 16px;
  align-items: flex-end;
  
  :deep(.el-textarea__inner) {
    background-color: $bg-dark;
    border: 1px solid $border-color;
    color: $text-primary;
    box-shadow: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 15px;
    transition: all 0.3s;
    
    &:focus { border-color: $primary-color; box-shadow: 0 0 0 1px $primary-color inset; }
    &::-webkit-scrollbar { width: 6px; }
    &::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
  }
  
  .send-btn {
    height: 48px;
    padding: 0 24px;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 1px;
  }
}

/* 动画特效 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.typing-indicator {
  padding: 4px 8px;
  span {
    display: inline-block; width: 6px; height: 6px; background-color: $text-regular;
    border-radius: 50%; margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both;
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
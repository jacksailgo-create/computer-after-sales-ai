<template>
  <div class="app-container">
    <div v-if="!isLoggedIn" class="login-container">
      <div class="login-form">
        <div class="tech-logo-box login-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
        </div>
        <h1 class="login-title">SYSTEM_LOGIN</h1>
        <div class="login-input-group">
          <label for="username">> USERNAME_</label>
          <input 
            id="username" v-model="username" type="text"
            placeholder="Enter username" @keyup.enter="handleLogin"
          />
        </div>
        <div class="login-input-group">
          <label for="password">> PASSWORD_</label>
          <input 
            id="password" v-model="password" type="password"
            placeholder="Enter password" @keyup.enter="handleLogin"
          />
        </div>
        <div v-if="loginError" class="login-error">
          [ERROR] {{ loginError }}
        </div>
        <button class="login-button btn-primary" @click="handleLogin">
          AUTHENTICATE
        </button>
        <div class="login-hint">
          <p>测试用户：root1, root2, root3</p>
          <p>密码：123456</p>
        </div>
      </div>
    </div>
    
    <template v-else>
      <div class="main-content">
        <div class="sidebar-wrapper">
          <div class="sidebar-content" :class="{ 'expanded': isSidebarExpanded }">
            <div class="app-branding">
              <div class="tech-logo-box sidebar-logo">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
              </div>
              <button class="toggle-sidebar-btn" @click="toggleSidebar" :title="isSidebarExpanded ? '收起侧边栏' : '展开侧边栏'">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path v-if="isSidebarExpanded" d="M15 18l-6-6 6-6"/>
                  <path v-else d="M9 18l6-6-6-6"/>
                </svg>
              </button>
            </div>
            
            <div class="session-button-container" v-show="isSidebarExpanded">
              <a href="#" class="new-chat-btn" @click.prevent="createNewSession">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                <span class="text">新建终端会话</span>
                <span class="shortcut"><span class="key">Ctrl+K</span></span>
              </a>
            </div>
            
            <div class="navigation-container" v-show="isSidebarExpanded">
              <div class="navigation-item" :class="{ 'selected': selectedNavItem === 'knowledge' }" @click="handleKnowledgeBase">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" class="nav-icon" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                <span class="nav-text">知识库检索</span>
              </div>
              <div class="navigation-item" :class="{ 'selected': selectedNavItem === 'service' }" @click="handleServiceStation">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" class="nav-icon" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span class="nav-text">服务站定位</span>
              </div>
              <div class="navigation-item" :class="{ 'selected': selectedNavItem === 'network' }" @click="handleNetworkSearch">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" class="nav-icon" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                <span class="nav-text">广域网搜索</span>
              </div>
            </div>

            <div v-show="isSidebarExpanded" class="sidebar-main">
              <div class="navigation-item history-title" @click="toggleSessions">
                <span class="nav-text">会话历史_</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="collapse-icon" :class="{'rotated': !showSessions}">
                  <path d="M6 9l6 6 6-6"/>
                </svg>
              </div>
              <div class="sessions-list" v-show="showSessions">
                <div v-if="isLoadingSessions" class="loading-state">Syncing data...</div>
                <div v-else-if="sessions.length === 0" class="empty-state">No records found.</div>
                <div
                  v-for="session in sessions"
                  :key="session.session_id"
                  :class="['session-item', { 'selected': session.session_id === selectedSessionId }]"
                  @click="selectSession(session.session_id)"
                >
                  <div class="session-info">
                    <span class="session-preview">{{ session.memory[0]?.content || '[EMPTY_LOG]' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="main-container">
          
          <div class="top-user-section">
            <div class="user-avatar-container" ref="avatarContainerRef">
              
              <div class="user-avatar-placeholder" @click="toggleUserInfo" tabindex="0">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              </div>

              <transition name="fade-slide">
                <div class="user-info-dropdown" v-show="showUserInfo">
                  <div class="dropdown-header">
                    <span class="user-name">@{{ currentUser || 'Guest' }}</span>
                    <span class="user-role">SYS_ADMIN</span>
                  </div>
                  <div class="dropdown-body">
                    <button v-if="currentUser" class="btn-tertiary logout-button" @click="handleLogout">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                      注销连接
                    </button>
                    <button v-else class="btn-primary" @click="goToLogin">建立连接</button>
                  </div>
                </div>
              </transition>
            </div>
          </div>

          <div class="result-container">
            <div class="chat-message-container" ref="chatContainerRef">
              <div v-if="chatMessages.length === 0" class="welcome-screen">
                <h2>AWAITING_INPUT_</h2>
              </div>
              
              <div v-for="(msg, index) in chatMessages" :key="index" :class="['message-wrapper', msg.type]">
                 
                 <div class="message-role-label" v-if="msg.type === 'THINKING'" @click="toggleThinking(index)">
                   <div class="thinking-header">
                     <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="thinking-icon" :class="{ 'collapsed': msg.collapsed }"><polyline points="6 9 12 15 18 9"></polyline></svg>
                     <span class="thinking-text">{{ isProcessing && index === chatMessages.length - 1 ? 'PROCESSING...' : 'SYSTEM_LOG' }}</span>
                   </div>
                 </div>
                 
                 <div class="message-content" v-show="msg.type !== 'THINKING' || !msg.collapsed">
                   <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                 </div>
              </div>
            </div>
              
            <div class="input-container">
              <div class="textarea-with-button" :class="{ 'processing-glow': isProcessing }">
                <textarea
                  v-model="userInput"
                  placeholder="Input command..."
                  @keyup.enter.exact="handleSend($event)"
                  :disabled="isProcessing"
                  rows="1"
                ></textarea>
                <button 
                  class="send-button"
                  :class="{ 'cancel-mode': isProcessing, 'disabled': !userInput.trim() && !isProcessing }"
                  :disabled="!userInput.trim() && !isProcessing"
                  @click="isProcessing ? handleCancel() : handleSend()"
                >
                  <svg v-if="isProcessing" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12"></rect></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                </button>
              </div>
              <div class="input-footer">System responses may contain inaccuracies. Verify output.</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
// [Script 逻辑无变化，安全保留]
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue';
import { marked } from 'marked';

marked.setOptions({ breaks: true, gfm: true });

const renderMarkdown = (text) => {
  if (!text) return '';
  try { return marked.parse(text); } catch (e) { console.error('Markdown error:', e); return text; }
};

export default {
  name: 'App',
  setup() {
    const isLoggedIn = ref(true);
    const isSidebarExpanded = ref(true);
    const username = ref('');
    const password = ref('');
    const currentUser = ref('');
    const loginError = ref('');
    const showUserInfo = ref(false);
    const avatarContainerRef = ref(null);
    const chatContainerRef = ref(null);
    
    const toggleUserInfo = () => { showUserInfo.value = !showUserInfo.value; };
    const handleClickOutside = (event) => {
      if (showUserInfo.value && avatarContainerRef.value && !avatarContainerRef.value.contains(event.target)) {
        showUserInfo.value = false;
      }
    };
    
    onMounted(() => { document.addEventListener('click', handleClickOutside); });
    onUnmounted(() => { document.removeEventListener('click', handleClickOutside); });
    
    const savedUserId = localStorage.getItem('currentUserId');
    if (savedUserId) {
      const validUsers = [{ username: 'root1', password: '123456', userId: 'root1' }, { username: 'root2', password: '123456', userId: 'root2' }, { username: 'root3', password: '123456', userId: 'root3' }];
      const savedUser = validUsers.find(u => u.userId === savedUserId);
      if (savedUser) { currentUser.value = savedUser.username; }
    }
    
    const userInput = ref('');
    const chatMessages = ref([]); 
    const isProcessing = ref(false); 
    let reader = null; 
    
    const selectedNavItem = ref('');
    
    const toggleThinking = (index) => {
      const msg = chatMessages.value[index];
      if (msg && msg.type === 'THINKING') { msg.collapsed = !msg.collapsed; }
    };
    
    const handleKnowledgeBase = () => { selectedNavItem.value = 'knowledge'; selectedSessionId.value = ''; };
    const handleNetworkSearch = () => { selectedNavItem.value = 'network'; selectedSessionId.value = ''; };
    const handleServiceStation = () => { selectedNavItem.value = 'service'; selectedSessionId.value = ''; };
    
    const sessions = ref([]);
    const selectedSessionId = ref('');
    const isLoadingSessions = ref(false);
    const showSessions = ref(true); 
    const toggleSessions = () => { showSessions.value = !showSessions.value; };

    const handleLogin = () => {
      loginError.value = '';
      const validUsers = [{ username: 'root1', password: '123456', userId: 'root1' }, { username: 'root2', password: '123456', userId: 'root2' }, { username: 'root3', password: '123456', userId: 'root3' }];
      const user = validUsers.find(u => u.username === username.value && u.password === password.value);
      if (user) {
        isLoggedIn.value = true; currentUser.value = user.username; localStorage.setItem('currentUserId', user.userId);
        window.scrollTo(0, 0); username.value = ''; password.value = '';
        fetchUserSessions();
      } else { loginError.value = '用户名或密码错误'; }
    };

    const fetchUserSessions = async () => {
      if (!currentUser.value) return;
      isLoadingSessions.value = true;
      try {
        const response = await fetch('http://127.0.0.1:8000/api/user_sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({"user_id": currentUser.value}) });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        if (data.success && data.sessions) {
          sessions.value = data.sessions;
          if (data.sessions.length > 0 && !selectedSessionId.value) selectSession(data.sessions[0].session_id);
        }
      } catch (error) { console.error('Error fetching sessions:', error); } finally { isLoadingSessions.value = false; scrollToBottom(); }
    };

    const createNewSession = () => {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const newSession = { session_id: newSessionId, create_time: new Date().toISOString(), memory: [], total_messages: 0 };
      sessions.value.unshift(newSession); userInput.value = '';
      selectSession(newSessionId);
    };
    
    const selectSession = (sessionId) => {
      selectedSessionId.value = sessionId; selectedNavItem.value = '';
      const session = sessions.value.find(s => s.session_id === sessionId);
      chatMessages.value = [];
      
      if (session && session.memory && Array.isArray(session.memory) && session.memory.length > 0) {
        let lastType = null;
        session.memory.forEach(msg => {
          if (!msg || !msg.content) return;
          let type = msg.role; if (type === 'process') type = 'THINKING';
          if (type === 'THINKING' && lastType === 'THINKING') { 
            const lastMsg = chatMessages.value[chatMessages.value.length - 1]; 
            lastMsg.content += '\n' + msg.content; 
          } else { 
            chatMessages.value.push({ type: type, content: msg.content, collapsed: type === 'THINKING' }); 
          }
          lastType = type;
        });
        nextTick(() => { scrollToBottom(); });
      }
    };
    
    const handleLogout = () => {
      isLoggedIn.value = false; currentUser.value = ''; localStorage.removeItem('currentUserId');
      userInput.value = ''; sessions.value = []; selectedSessionId.value = ''; chatMessages.value = [];
    };
    
    const goToLogin = () => { isLoggedIn.value = false; currentUser.value = ''; localStorage.removeItem('currentUserId'); };
    
    const handleSend = async (event) => {
        if (event) event.preventDefault();
        if (!userInput.value.trim()) return;
        
        const userId = localStorage.getItem('currentUserId');
        if (!userId) { isLoggedIn.value = false; return; }
        
        isProcessing.value = true;
        chatMessages.value.forEach(msg => { if (msg.type === 'THINKING') { msg.collapsed = true; }});
        chatMessages.value.push({ type: 'user', content: userInput.value.trim() });
        
        const finalUserId = userId || currentUser.value;
        scrollToBottom();
        
        const requestData = { query: userInput.value.trim(), context: { user_id: finalUserId, session_id: selectedSessionId.value || '' } };
        userInput.value = ''; 
        
        try {
          const response = await fetch('http://127.0.0.1:8000/api/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestData) });
          if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
          
          reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = '';
          
          while (true) {
            const { done, value } = await reader.read();
            if (done) { if (buffer.trim()) { processSSEData(buffer); buffer = ''; } break; }
            const chunk = decoder.decode(value, { stream: true }); buffer += chunk;
            const lines = buffer.split('\n');
            for (let i = 0; i < lines.length - 1; i++) { const line = lines[i]; if (line.trim()) processSSEData(line); }
            buffer = lines[lines.length - 1];
          }
        } catch (error) {
          if (!error.name || error.name !== 'AbortError') { 
            streamTextToProcess(`请求失败: ${error.message}\n`); 
          }
        } finally {
          isProcessing.value = false; reader = null; scrollToBottom(); fetchUserSessions();
        }
    };
      
    const processSSEData = (data) => {
      try {
        if (typeof data !== 'string') return;
        if (data.startsWith('data:')) {
          const jsonStr = data.substring(5).trim();
          if (jsonStr) {
            try {
              const parsedData = JSON.parse(jsonStr);
              let kind; let text;
              if (parsedData.content && typeof parsedData.content === 'object') {
                text = parsedData.content.text;
                if (parsedData.content.kind) kind = parsedData.content.kind; else if (parsedData.content.type) kind = parsedData.content.type;
                if (parsedData.status === 'FINISHED' || parsedData.content.contentType === 'sagegpt/finish') return;
              } else if (parsedData.type && parsedData.content) { kind = parsedData.type; text = parsedData.content; }

              if (kind && text) {
                switch (kind) {
                  case 'ANSWER': streamTextToAnswer(text); break;
                  case 'THINKING': streamTextToProcess(text); break;
                  case 'PROCESS': streamTextToProcess(text + '\n'); break;
                  default: streamTextToProcess(text + '\n');
                }
              }
            } catch (jsonError) { console.error('JSON parse error:', jsonError); }
          }
        }
      } catch (error) { console.error('Error processing SSE data:', error); }
    };
      
    const handleCancel = () => { if (reader) { reader.cancel(); reader = null; } isProcessing.value = false; streamTextToProcess('请求已取消\n'); };

    const streamTextToAnswer = (text) => {
      const lastMsg = chatMessages.value[chatMessages.value.length - 1];
      if ((!text || !text.trim()) && lastMsg && lastMsg.type !== 'assistant') return;
      text = text.replace(/ +/g, ' ').replace(/\n+/g, '\n'); 
      if (lastMsg && lastMsg.type === 'assistant') { lastMsg.content += text; } else { chatMessages.value.push({ type: 'assistant', content: text }); }
      chatMessages.value = [...chatMessages.value]; scrollToBottom();
    };
    
    const streamTextToProcess = (text) => {
      const lastMsg = chatMessages.value[chatMessages.value.length - 1];
      if (lastMsg && lastMsg.type === 'THINKING') { lastMsg.content += text; if (isProcessing.value && lastMsg.collapsed === undefined) { lastMsg.collapsed = false; } } 
      else { chatMessages.value.push({ type: 'THINKING', content: text, collapsed: false }); }
      chatMessages.value = [...chatMessages.value]; scrollToBottom();
    };
    
    const scrollToBottom = () => { 
      nextTick(() => { 
        if (chatContainerRef.value) { 
          chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight; 
        } 
      }); 
    };

    watch(isLoggedIn, (newVal) => { if (newVal && currentUser.value) fetchUserSessions(); });
    onMounted(() => { if (isLoggedIn.value && currentUser.value) { fetchUserSessions(); nextTick(() => { scrollToBottom(); }); } document.addEventListener('keydown', handleKeyDown); });
    onUnmounted(() => { document.removeEventListener('keydown', handleKeyDown); });
    const handleKeyDown = (event) => { if ((event.ctrlKey || event.metaKey) && event.key === 'k') { event.preventDefault(); createNewSession(); } };
    const toggleSidebar = () => { isSidebarExpanded.value = !isSidebarExpanded.value; };
    
    return {
      isLoggedIn, username, password, currentUser, loginError, showUserInfo, toggleUserInfo, avatarContainerRef, chatContainerRef,
      handleLogin, handleLogout, goToLogin, userInput, chatMessages, isProcessing,
      handleSend, handleCancel, renderMarkdown, sessions, selectedSessionId, isLoadingSessions, showSessions, toggleSessions,
      selectedNavItem, handleKnowledgeBase, handleNetworkSearch, handleServiceStation, selectSession, fetchUserSessions, createNewSession,
      isSidebarExpanded, toggleSidebar, toggleThinking
    };
  }
};
</script>

<style>
:root {
  --tech-bg-dark: #0a192f;
  --tech-bg-light: #112240;
  --tech-primary: #64ffda;
  --tech-primary-hover: #535bf2;
  --tech-text-main: #e6f1ff;
  --tech-text-muted: #8892b0;
  --tech-border: #233554;
  
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.3);
  --shadow-glow: 0 0 15px rgba(100, 255, 218, 0.15);
  --shadow-glow-strong: 0 0 20px rgba(100, 255, 218, 0.3);
}

body, html {
  width: 100vw; height: 100vh; overflow: hidden; margin: 0; padding: 0;
  background-color: var(--tech-bg-dark);
  background-image: 
    linear-gradient(rgba(100, 255, 218, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100, 255, 218, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  font-family: 'Inter', 'Fira Code', ui-monospace, SFMono-Regular, monospace, sans-serif;
  color: var(--tech-text-main);
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(136, 146, 176, 0.2); border-radius: 10px; transition: background 0.3s; }
::-webkit-scrollbar-thumb:hover { background: rgba(100, 255, 218, 0.4); }
</style>

<style scoped>
* { box-sizing: border-box; }
a { color: var(--tech-primary); text-decoration: none; transition: all 0.3s; }
a:hover { color: var(--tech-primary-hover); text-shadow: var(--shadow-glow); }

button {
  border-radius: 6px; border: 1px solid transparent; padding: 0.6em 1.2em; font-size: 0.95em;
  font-weight: 500; font-family: inherit; cursor: pointer; transition: all 0.25s; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-primary { background-color: rgba(100, 255, 218, 0.1); border: 1px solid var(--tech-primary); color: var(--tech-primary); box-shadow: var(--shadow-glow); }
.btn-primary:hover:not(:disabled) { background-color: rgba(100, 255, 218, 0.2); box-shadow: var(--shadow-glow-strong); transform: translateY(-1px); }
.btn-tertiary { background-color: transparent; border: none; color: var(--tech-text-muted); }
.btn-tertiary:hover { color: var(--tech-primary); background-color: rgba(100, 255, 218, 0.05); }

/* --- 纯CSS构建的Logo盒子样式 --- */
.tech-logo-box {
  display: flex; align-items: center; justify-content: center;
  background: rgba(100, 255, 218, 0.05); border: 1px solid rgba(100, 255, 218, 0.3);
  color: var(--tech-primary); border-radius: 8px; box-shadow: var(--shadow-glow);
}
.login-logo { width: 64px; height: 64px; margin: 0 auto 24px; border-radius: 12px; }
.login-logo svg { width: 36px; height: 36px; }
.sidebar-logo { width: 36px; height: 36px; }
.sidebar-logo svg { width: 20px; height: 20px; }

/* --- 纯CSS构建的用户头像占位符样式 --- */
.user-avatar-placeholder {
  width: 38px; height: 38px; border-radius: 50%;
  background-color: var(--tech-bg-light);
  border: 1px solid var(--tech-border);
  color: var(--tech-text-muted);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: var(--shadow-sm); backdrop-filter: blur(4px);
}
.user-avatar-placeholder:hover {
  border-color: var(--tech-primary); color: var(--tech-primary);
  transform: scale(1.05); box-shadow: var(--shadow-glow);
}

/* 深度选择器解决 Markdown */
:deep(.markdown-body) { font-size: 0.95rem; line-height: 1.7; color: var(--tech-text-main); }
:deep(.markdown-body p) { margin-bottom: 1em; }
:deep(.markdown-body h1), :deep(.markdown-body h2), :deep(.markdown-body h3) { margin-top: 1.5em; margin-bottom: 0.5em; font-weight: 600; color: var(--tech-text-main); }
:deep(.markdown-body h2) { font-size: 1.4em; border-bottom: 1px solid var(--tech-border); padding-bottom: 0.3em; }
:deep(.markdown-body code) { font-family: 'Fira Code', monospace; background-color: rgba(100, 255, 218, 0.1); color: var(--tech-primary); padding: 0.2em 0.4em; border-radius: 4px; font-size: 0.85em; }
:deep(.markdown-body pre) { background-color: #050b14; border: 1px solid var(--tech-border); border-radius: 8px; padding: 16px; overflow-x: auto; margin: 1em 0; }
:deep(.markdown-body pre code) { background-color: transparent; color: inherit; padding: 0; }
:deep(.markdown-body blockquote) { margin: 1em 0; padding: 0.5em 1em; color: var(--tech-text-muted); border-left: 4px solid var(--tech-primary); background: rgba(100, 255, 218, 0.02); border-radius: 0 4px 4px 0; }

.app-container { width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden; position: relative; background: radial-gradient(circle at 50% 50%, rgba(20, 40, 60, 0.3) 0%, rgba(10, 25, 47, 0.8) 100%);}
.main-content { display: flex; flex: 1; overflow: hidden; position: relative; }

/* 侧边栏 */
.sidebar-wrapper { height: 100%; z-index: 50; }
.sidebar-content {
  width: 68px; height: 100%; background-color: rgba(17, 34, 64, 0.85); border-right: 1px solid var(--tech-border);
  display: flex; flex-direction: column; transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1); backdrop-filter: blur(10px); position: relative;
}
.sidebar-content.expanded { width: 260px; }

.app-branding { display: flex; align-items: center; padding: 16px; border-bottom: 1px solid var(--tech-border); gap: 12px; min-height: 68px; }

.toggle-sidebar-btn {
  position: absolute; top: 24px; right: -12px; width: 24px; height: 24px; padding: 0; border-radius: 50%;
  background-color: var(--tech-bg-light); border: 1px solid var(--tech-primary); color: var(--tech-primary);
  z-index: 10; box-shadow: var(--shadow-sm); outline: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s;
}
.toggle-sidebar-btn:hover { background-color: var(--tech-primary); color: var(--tech-bg-dark); transform: scale(1.1); }

.session-button-container { padding: 16px; border-bottom: 1px dashed rgba(100, 255, 218, 0.15); }
.new-chat-btn {
  display: flex; align-items: center; gap: 10px; padding: 10px; background-color: rgba(100, 255, 218, 0.05); border: 1px solid rgba(100, 255, 218, 0.3);
  color: var(--tech-primary); border-radius: 6px; font-size: 0.9rem; transition: all 0.2s; white-space: nowrap; overflow: hidden; font-family: 'Fira Code', monospace;
}
.new-chat-btn:hover { background-color: rgba(100, 255, 218, 0.15); box-shadow: var(--shadow-glow); }
.new-chat-btn .shortcut { margin-left: auto; font-size: 0.75rem; color: var(--tech-text-muted); background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; }

.navigation-container { padding: 12px 8px; display: flex; flex-direction: column; gap: 4px; border-bottom: 1px dashed rgba(100, 255, 218, 0.15); }
.navigation-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 6px; color: var(--tech-text-muted); cursor: pointer; transition: all 0.2s ease; overflow: hidden; white-space: nowrap;
}
.navigation-item:hover { background-color: rgba(100, 255, 218, 0.05); color: var(--tech-primary); transform: translateX(4px); }
.navigation-item.selected { background-color: rgba(100, 255, 218, 0.1); color: var(--tech-primary); border-left: 2px solid var(--tech-primary); }

.sidebar-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.history-title {
  padding: 16px 20px 8px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--tech-text-muted); display: flex; justify-content: space-between; align-items: center; font-family: 'Fira Code', monospace; cursor: pointer;
}
.collapse-icon { transition: transform 0.3s ease; }
.collapse-icon.rotated { transform: rotate(-90deg); }

.sessions-list { flex: 1; padding: 8px; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; }
.session-item { padding: 10px 12px; border-radius: 6px; cursor: pointer; color: var(--tech-text-muted); border: 1px solid transparent; transition: all 0.2s; font-size: 0.9em; font-family: 'Fira Code', monospace; }
.session-item:hover { background-color: rgba(255, 255, 255, 0.03); color: var(--tech-text-main); }
.session-item.selected { background-color: rgba(100, 255, 218, 0.08); border-color: rgba(100, 255, 218, 0.2); color: var(--tech-primary); }
.session-preview { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;}
.loading-state, .empty-state { padding: 20px; text-align: center; color: var(--tech-text-muted); font-size: 0.85em; font-family: 'Fira Code', monospace; }

/* 聊天展示区 */
.main-container { flex: 1; display: flex; flex-direction: column; position: relative; min-width: 0; }
.result-container { flex: 1; display: flex; flex-direction: column; position: relative; height: 100%; overflow: hidden; }

.top-user-section { position: absolute; top: 20px; right: 24px; z-index: 100; display: flex; justify-content: flex-end; align-items: center; }

.user-info-dropdown {
  position: absolute; top: calc(100% + 12px); right: 0; background-color: var(--tech-bg-light); border: 1px solid var(--tech-border);
  border-radius: 10px; box-shadow: var(--shadow-lg); padding: 8px; min-width: 180px; z-index: 1000; display: flex; flex-direction: column; backdrop-filter: blur(12px);
}
.dropdown-header { padding: 16px; border-bottom: 1px solid var(--tech-border); display: flex; flex-direction: column; }
.dropdown-header .user-name { font-weight: 600; color: var(--tech-text-main); font-size: 14px;}
.dropdown-header .user-role { font-size: 12px; color: var(--tech-text-muted); margin-top: 4px;}
.dropdown-body { padding: 8px; }
.logout-button { color: #ef4444; width: 100%; justify-content: flex-start; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.logout-button:hover { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; }

.chat-message-container { flex: 1; overflow-y: auto; padding: 80px 15% 120px 15%; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth; }
.welcome-screen { flex: 1; display: flex; align-items: center; justify-content: center; flex-direction: column; }
.welcome-screen h2 { font-size: 2rem; color: var(--tech-text-muted); opacity: 0.5; font-family: 'Fira Code', monospace;}

.message-wrapper { display: flex; flex-direction: column; gap: 6px; width: 100%; max-width: 840px; margin: 0 auto; animation: slideIn 0.3s ease-out forwards; }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* 用户气泡 */
.message-wrapper.user { align-items: flex-end; }
.message-wrapper.user .message-content {
  background-color: rgba(100, 255, 218, 0.1); border: 1px solid var(--tech-primary); color: var(--tech-primary);
  padding: 12px 18px; border-radius: 12px 12px 0 12px; font-size: 0.95rem; max-width: 75%; white-space: pre-wrap; box-shadow: var(--shadow-sm);
}

/* AI 气泡 */
.message-wrapper.assistant { align-items: flex-start; }
.message-wrapper.assistant .message-content { background-color: transparent; padding: 10px 0; width: 100%; font-size: 0.95rem; }

/* 思考过程 */
.message-wrapper.THINKING { align-items: flex-start; margin-bottom: -10px; }
.thinking-header {
  display: inline-flex; align-items: center; gap: 8px; padding: 4px 10px; border-radius: 4px; cursor: pointer; color: var(--tech-text-muted); font-size: 0.8rem; font-family: 'Fira Code', monospace; background: rgba(255,255,255,0.02); user-select: none;
}
.thinking-header:hover { background: rgba(255,255,255,0.05); color: var(--tech-primary); }
.thinking-icon { transition: transform 0.3s ease; }
.thinking-icon.collapsed { transform: rotate(-90deg); }
.message-wrapper.THINKING .message-content {
  margin-top: 8px; margin-left: 14px; padding: 8px 0 8px 16px; border-left: 2px dashed var(--tech-border); color: var(--tech-text-muted); font-size: 0.85rem; font-family: 'Fira Code', monospace;
}

/* 悬浮输入区 */
.input-container {
  position: absolute; bottom: 0; left: 0; width: 100%; padding: 0 15% 24px 15%;
  background: linear-gradient(180deg, transparent 0%, var(--tech-bg-dark) 40%);
  display: flex; flex-direction: column; align-items: center; z-index: 100;
}
.textarea-with-button {
  position: relative; width: 100%; max-width: 840px;
  background: rgba(17, 34, 64, 0.9); border: 1px solid var(--tech-border); border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); display: flex; flex-direction: row; align-items: flex-end; padding: 8px; transition: all 0.3s; backdrop-filter: blur(10px);
}
.textarea-with-button:focus-within { border-color: var(--tech-primary); box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(100,255,218,0.2); }
.textarea-with-button.processing-glow { border-color: var(--tech-primary); animation: pulse-border 2s infinite; }

@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(100, 255, 218, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(100, 255, 218, 0); }
  100% { box-shadow: 0 0 0 0 rgba(100, 255, 218, 0); }
}

textarea {
  flex: 1; background: transparent; border: none; color: var(--tech-text-main); font-size: 0.95rem; resize: none; outline: none; min-height: 24px; max-height: 200px; padding: 8px 4px; font-family: inherit; line-height: 1.5; scrollbar-width: none;
}
textarea::-webkit-scrollbar { display: none; }
textarea::placeholder { color: var(--tech-text-muted); font-family: 'Fira Code', monospace; }

.send-button {
  flex-shrink: 0; width: 34px; height: 34px; padding: 0; margin-left: 8px; border-radius: 8px;
  background-color: rgba(100, 255, 218, 0.1); border: 1px solid transparent; color: var(--tech-primary); display: flex; align-items: center; justify-content: center; transition: all 0.2s; cursor: pointer;
}
.send-button:not(.disabled):hover { background-color: var(--tech-primary); color: var(--tech-bg-dark); box-shadow: var(--shadow-glow); }
.send-button.disabled { color: var(--tech-border); cursor: not-allowed; }
.send-button.cancel-mode { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; }
.send-button.cancel-mode:hover { background-color: #ef4444; color: white; }

.input-footer { font-size: 0.7rem; color: var(--tech-text-muted); margin-top: 10px; font-family: 'Fira Code', monospace; }

/* 登录页 */
.login-container { display: flex; justify-content: center; align-items: center; height: 100vh; width: 100vw; background-color: var(--tech-bg-dark); }
.login-form {
  background: var(--tech-bg-light); border: 1px solid var(--tech-border); border-radius: 8px; padding: 40px; box-shadow: var(--shadow-lg); width: 100%; max-width: 400px; text-align: center; position: relative; overflow: hidden;
}
.login-form::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--tech-primary), transparent); }
.login-title { margin: 0 0 30px; font-size: 20px; color: var(--tech-primary); font-family: 'Fira Code', monospace; letter-spacing: 2px;}
.login-input-group { margin-bottom: 20px; text-align: left; }
.login-input-group label { display: block; margin-bottom: 8px; font-size: 12px; color: var(--tech-primary); font-family: 'Fira Code', monospace; }
.login-input-group input { width: 100%; padding: 12px; background: rgba(10, 25, 47, 0.8); border: 1px solid var(--tech-border); color: var(--tech-text-main); border-radius: 4px; font-size: 14px; font-family: 'Fira Code', monospace; transition: all 0.3s; }
.login-input-group input:focus { border-color: var(--tech-primary); box-shadow: 0 0 0 1px rgba(100, 255, 218, 0.2); outline: none; }
.login-button { width: 100%; padding: 12px; margin-top: 10px; font-family: 'Fira Code', monospace; letter-spacing: 1px;}
.login-error { color: #ef4444; margin-bottom: 20px; font-size: 12px; font-family: 'Fira Code', monospace; border-left: 2px solid #ef4444; padding: 8px; text-align: left; background: rgba(239, 68, 68, 0.1); }
.login-hint { margin-top: 24px; font-size: 11px; color: var(--tech-text-muted); font-family: 'Fira Code', monospace; padding: 12px; background: rgba(0,0,0,0.2); border: 1px dashed var(--tech-border); text-align: left;}

.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.2s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
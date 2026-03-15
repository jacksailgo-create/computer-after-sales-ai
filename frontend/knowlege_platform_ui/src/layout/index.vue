<template>
  <div class="app-wrapper">
    <aside class="sidebar">
      <div class="logo">
        <el-icon class="logo-icon"><Cpu /></el-icon>
        <span>ITS Knowledge</span>
      </div>
      
      <div class="menu-container">
        <el-menu
          :default-active="activeMenu"
          router
          class="custom-menu"
          :collapse-transition="false"
        >
          <el-menu-item index="/knowledge">
            <el-icon><Files /></el-icon>
            <template #title>知识库管理</template>
          </el-menu-item>
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>智能问答</template>
          </el-menu-item>
        </el-menu>
      </div>
    </aside>

    <div class="main-container">
      <header class="top-header">
        <div class="header-left">
          <h2 class="page-title">{{ currentPageName }}</h2>
        </div>
        <div class="header-right">
          <el-avatar 
            :size="32" 
            src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" 
          />
          <span class="username">Henry</span>
        </div>
      </header>

      <main class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Files, ChatDotRound, Cpu } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)

// 动态计算当前页面的标题
const routeNames = {
  '/knowledge': '知识库管理',
  '/chat': '智能问答系统'
}
const currentPageName = computed(() => routeNames[route.path] || 'ITS 面板')
</script>

<style lang="scss" scoped>
/* 定义全局主题变量 */
$bg-dark: #0f172a;        /* 右侧主背景色 (深灰蓝) */
$bg-sidebar: #1e293b;     /* 左侧侧边栏背景 */
$text-primary: #f8fafc;
$text-regular: #94a3b8;
$primary-color: #3b82f6;  /* 现代亮蓝色 */
$border-color: #334155;

.app-wrapper {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: $bg-dark;
  color: $text-primary;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: 260px;
  background-color: $bg-sidebar;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.2);
  z-index: 10;
  transition: width 0.3s;

  .logo {
    height: 70px;
    display: flex;
    align-items: center;
    padding: 0 24px;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.5px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    
    .logo-icon {
      margin-right: 10px;
      font-size: 24px;
      color: #00f260;
    }

    span {
      background: linear-gradient(90deg, #00f260, #0575e6);
      -webkit-background-clip: text;
      color: transparent;
    }
  }

  .menu-container {
    flex: 1;
    padding: 16px 12px;
    overflow-y: auto;
  }

  /* 深度重写 Element Plus 菜单样式 (胶囊风格) */
  :deep(.custom-menu) {
    border-right: none;
    background-color: transparent;
    
    .el-menu-item {
      height: 50px;
      line-height: 50px;
      margin-bottom: 8px;
      border-radius: 10px;
      color: $text-regular;
      font-size: 15px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &:hover {
        background-color: rgba(255, 255, 255, 0.05);
        color: $text-primary;
      }

      &.is-active {
        background-color: rgba(59, 130, 246, 0.15); /* 带有透明度的品牌色 */
        color: $primary-color;
        font-weight: 600;
        
        /* 左侧加上一个小小的指示条，极具现代感 */
        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 15%;
          height: 70%;
          width: 4px;
          background-color: $primary-color;
          border-radius: 0 4px 4px 0;
        }
      }

      .el-icon {
        font-size: 18px;
        margin-right: 12px;
      }
    }
  }
}

/* 右侧主区域 */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: $bg-dark;
  position: relative;
  
  /* 保留你的极客风点阵背景，稍微调低透明度使其更柔和 */
  &::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px);
    background-size: 24px 24px;
    pointer-events: none;
    z-index: 0;
  }
}

/* 顶部导航栏 */
.top-header {
  height: 70px;
  min-height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background-color: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px); /* 毛玻璃效果 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  z-index: 5;

  .page-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: $text-primary;
    letter-spacing: 0.5px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    padding: 6px 12px;
    border-radius: 20px;
    transition: background 0.2s;

    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }

    .username {
      font-size: 14px;
      font-weight: 500;
      color: $text-regular;
    }
  }
}

/* 路由内容区 */
.content-wrapper {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  z-index: 1;
  /* 隐藏滚动条但保留滚动功能 (现代 UI 常见做法) */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 4px;
  }
}

/* 路由切换动画 */
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(10px); /* 改为从下方浮现，更丝滑 */
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
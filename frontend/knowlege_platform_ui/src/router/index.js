import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/index.vue'

// 引入顶部进度条插件及其样式
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 进度条全局配置（关闭右上角的原生转圈小动画，更清爽）
NProgress.configure({ showSpinner: false })

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/knowledge',
    children: [
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'), // 确保文件名与你实际的 vue 文件一致
        meta: { title: '知识库管理', icon: 'Files' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: { title: '智能问答', icon: 'ChatDotRound' }
      }
    ]
  },
  // 🌟 404 兜底路由：匹配所有未定义的路径
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    // 假设你后续会写一个简单的 404 页面，这里先重定向回首页作为极简兜底
    redirect: '/knowledge', 
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // 🌟 滚动行为控制：切换路由时每次都回到顶部
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// ==========================================
// 🌟 全局前置守卫 (Global Before Guards)
// ==========================================
router.beforeEach((to, from, next) => {
  // 1. 开启进度条
  NProgress.start()
  
  // 2. 动态修改浏览器标签页标题
  const defaultTitle = 'ITS 智能售后'
  document.title = to.meta.title ? `${to.meta.title} - ${defaultTitle}` : defaultTitle
  
  // 3. 放行路由
  next()
})

// ==========================================
// 🌟 全局后置守卫 (Global After Hooks)
// ==========================================
router.afterEach(() => {
  // 路由跳转完成，关闭进度条
  NProgress.done()
})

export default router
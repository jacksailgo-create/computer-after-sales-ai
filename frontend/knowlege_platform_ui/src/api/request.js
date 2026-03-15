// src/utils/request.js (或者 src/api/request.js)
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 1. 创建 axios 实例
const service = axios.create({
  // 如果你用 Vite 配置了 proxy，这里可以是 '/api/v1'
  // 如果前端直连后端跨域，这里填 FastAPI 的地址 'http://127.0.0.1:8000/api/v1'
  baseURL: import.meta.env.VITE_APP_BASE_API || 'http://127.0.0.1:8001/api/v1',
  // 知识库向量化和大模型推理都比较耗时，建议设为 60 秒
  timeout: 60000 
})

// 2. 请求拦截器 (Request Interceptor)
service.interceptors.request.use(
  config => {
    // 💡 在这里可以自动携带 Token（如果以后你的系统加了登录功能）
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers['Authorization'] = `Bearer ${token}`
    // }
    return config
  },
  error => {
    console.error('发出请求异常:', error)
    return Promise.reject(error)
  }
)

// 3. 响应拦截器 (Response Interceptor)
service.interceptors.response.use(
  response => {
    // Axios 默认把后端返回的数据包装在 response.data 中
    const res = response.data

    // 💡 处理二进制文件流（如果以后有导出 PDF/Excel 的需求，直接放行）
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return res
    }

    // 💡 处理业务状态码
    // 我们后端的统一返回结构类似于 { code: 200, message: "...", data: {...} }
    if (res.code !== undefined && res.code !== 200) {
      // 业务报错，直接在屏幕上方弹出提示
      ElMessage.error(res.message || res.detail || '服务器业务异常')
      
      // 可以针对特定业务 code 做全局拦截，比如 401 token 过期跳回登录页
      // if (res.code === 401) { router.push('/login') }
      
      return Promise.reject(new Error(res.message || 'Error'))
    } else {
      // 成功，直接返回整个响应结构给前端业务代码
      return res
    }
  },
  error => {
    // 💡 集中处理 HTTP 原生状态码异常 (比如 404, 500)
    let message = '网络或服务器异常，请稍后重试'
    
    if (error.response) {
      const status = error.response.status
      // FastAPI 抛出 HTTPException 时，错误信息默认放在 detail 字段里
      const data = error.response.data
      const errorDetail = data.detail || data.message

      switch (status) {
        case 400:
          message = errorDetail || '请求参数错误'
          break
        case 401:
          message = '登录状态已过期，请重新登录'
          break
        case 403:
          message = '您没有权限执行此操作'
          break
        case 404:
          message = '请求的接口或资源不存在 (404)'
          break
        case 413:
          message = '上传的文件体积过大'
          break
        case 422:
          message = '表单参数校验失败 (422 Unprocessable Entity)'
          break
        case 500:
          message = errorDetail || '服务器内部出现严重错误 (500)'
          break
        case 504:
          message = '网关超时，大模型推理可能需要更长时间 (504)'
          break
        default:
          message = errorDetail || `网络请求错误 (${status})`
      }
    } else if (error.message && error.message.includes('timeout')) {
      message = '请求接口超时，请检查网络或稍后重试'
    } else if (error.message && error.message.includes('Network Error')) {
      message = '网络连接中断，请检查后端服务是否启动'
    }

    // 全局弹出红色的错误提示
    ElMessage.error(message)
    
    return Promise.reject(error)
  }
)

export default service
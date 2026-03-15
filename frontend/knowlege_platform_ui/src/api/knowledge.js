import request from './request'

// 1. 上传文件
export function uploadFile(data, onUploadProgress) {
  return request({ url: '/files/upload', method: 'post', data, onUploadProgress })
}

// 2. 获取预览文本
export function previewFile(id) {
  return request({ url: `/files/${id}/preview`, method: 'get' })
}

// 3. 保存清洗后的文本
export function updateFileContent(id, content) {
  return request({ url: `/files/${id}/content`, method: 'put', data: { content } })
}

// 4. 发起异步向量化
export function vectorizeFile(id) {
  return request({ url: `/files/${id}/vectorize`, method: 'post' })
}

// 5. 获取历史上传记录列表
export function getFileList() {
  return request({ 
    url: '/files/list', 
    method: 'get' 
  })
}

// ==========================================
// 🌟 6. 智能问答接口 (对接多路召回 RAG 大模型)
// ==========================================
export function queryKnowledge(data) {
  // 注意：如果你的 request.js 里的 baseURL 已经配了 '/api/v1'，
  // 这里的 url 就写 '/chat/completions' 即可。
  return request({
    url: '/chat/completions',
    method: 'post',
    data // 传入 { query: "你的问题" }
  })
}
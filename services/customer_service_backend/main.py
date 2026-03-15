import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 引入我们封装好的 router
from customer_service_backend.api.router import router as api_router

# ==========================================
# 1. 初始化 FastAPI 应用
# ==========================================
app = FastAPI(
    title="ITS AI Backend",
    description="ITS 客服系统的后端核心服务",
    version="1.0.0"
)

# ==========================================
# 2. 配置跨域中间件 (CORS)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请务必修改为具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. 挂载路由 (将外部的 router 接入主应用)
# ==========================================
app.include_router(api_router)

# ==========================================
# 4. 启动入口
# ==========================================
if __name__ == "__main__":
    # 使用 uvicorn 启动当前文件(main)的 app 实例
    uvicorn.run("customer_service_backend.main:app", host="127.0.0.1", port=8000, reload=True)
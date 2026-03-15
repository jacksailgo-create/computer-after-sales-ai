import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# ==========================================
# 1. 核心基建加载
# ==========================================
# 初始化全局日志
from core.logger import setup_logger

logger = setup_logger("knowledge_service")

# 引入数据库引擎和所有的 Model 类 (这是让 SQLAlchemy 自动建表的前提)
from knowledge_platform_backend.api.database import engine, Base
# 引入路由组
from knowledge_platform_backend.api.routers import files, kb, chat


# ==========================================
# 2. 生命周期管理 (Lifespan)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理 FastAPI 的启动和关闭逻辑。
    类似 Spring Boot 中的 @PostConstruct 和 @PreDestroy。
    """
    logger.info("🚀 [Startup] 正在启动电脑售后多智能体系统后端...")
    try:
        # 自动扫描继承了 Base 的模型并建表 (不会覆盖已有的表数据)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ [Database] 数据库表结构检查与同步完成！")
    except Exception as e:
        logger.error(f"❌ [Database] 数据库初始化失败: {e}")

    yield  # yield 之前是启动逻辑，yield 之后是关闭逻辑

    logger.info("🛑 [Shutdown] 服务接收到终止信号，正在安全清理资源...")


# ==========================================
# 3. 初始化 FastAPI 实例
# ==========================================
app = FastAPI(
    title="ITS Computer After-Sales AI API",
    description="企业级电脑售后多智能体系统后端核心服务",
    version="1.0.0",
    lifespan=lifespan  # 挂载生命周期
)

# ==========================================
# 4. 中间件配置
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 5. 全局异常拦截器 (Global Exception Handler)
# ==========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局兜底异常拦截。防止未捕获的代码 Bug 导致应用崩溃，
    并确保给前端返回统一的 JSON 结构，而不是难看的 HTML 报错。
    """
    logger.error(f"⚠️ 拦截到未处理的系统异常 - URL: {request.url} | Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "系统内部发生未知异常，请联系系统管理员",
            "detail": str(exc)
        }
    )


# ==========================================
# 6. 路由挂载
# ==========================================
app.include_router(files.router)
app.include_router(kb.router)
app.include_router(chat.router)


# app.include_router(chat.router) # 预留给未来的大模型对话接口

# ==========================================
# 7. 探针接口
# ==========================================
@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "up", "message": "After-Sales AI Backend is running gracefully!"}


# ==========================================
# 8. 启动脚本
# ==========================================
if __name__ == "__main__":
    # 在 Mac 环境本地调试，reload=True 极其方便
    # 后期上生产环境可以用 gunicorn + uvicorn workers
    uvicorn.run("knowledge_platform_backend.main:app", host="0.0.0.0", port=8001, reload=True)
下面是在你现有设计基础上 **进一步工程化后的完整目录结构**。
特点：

* 明确 **四模块架构**
* 加入 **共享基础设施层**
* 加入 **AI系统必备模块（evaluation / observability / infra）**
* 每个目录都有 **职责注释**

整体是 **Monorepo + 多服务架构**。

---

# 完整目录结构（带详细注释）

```text
computer-after-sales-ai/
│
├── README.md                          # 项目说明、系统架构、启动方式
├── LICENSE                            # 开源协议
├── .env                               # 全局环境变量 (API KEY / DB / Redis)
├── .gitignore
│
├── docker-compose.yml                 # 本地开发环境编排 (MySQL / Redis / ChromaDB / MCP)
│
├── core/                              # ⭐ 全局核心基础设施
│   ├── config.py                      # OmegaConf 配置单例 (AppConfigManager)
│   ├── conf/                          # 全局 YAML 配置文件
│   ├── logger.py                      # 全局日志初始化
│   ├── exceptions.py                  # 自定义异常类
│   └── constants.py                   # 全局常量
│
├── services/                          # ⭐ 双核微服务集群
│
│   ├── customer_service_backend/      # ==========================================
│   │                                  # 🤖 智能客服后端 (多 Agent 调度中枢)
│   │                                  # ==========================================
│   │   ├── main.py                    # FastAPI 启动总入口 (挂载中间件与 router)
│   │   │
│   │   ├── api/                       # 🌐 API 路由层 (Controller)
│   │   │   ├── router.py              # 🚀 重构: 干净的流式对话与历史记录接口 (SSE)
│   │   │   └── schemas/               # 🚀 新增: Pydantic 强类型数据契约
│   │   │       ├── request.py         # 入参校验 (ChatMessageRequest 等)
│   │   │       └── response.py        # 出参校验 (StreamPacket, Union 多态等)
│   │   │
│   │   ├── service/                   # 🧠 业务逻辑层 (Service)
│   │   │   ├── agent_service.py       # 🚀 重构: astream_events v2 核心流式调度器
│   │   │   └── session_service.py     # 🚀 重构: 基于本地 JSON 的长效记忆管理系统
│   │   │
│   │   ├── utils/                     # 🧰 业务工具箱
│   │   │   ├── response_util.py       # 🚀 新增: ResponseFactory (统一构建前端 SSE 数据包)
│   │   │   └── text_util.py           # 🚀 新增: HTML 卡片生成器、工具名中英映射提取
│   │   │
│   │   ├── workflows/                 # 🗺️ Agent 编排逻辑
│   │   │   └── after_sales_graph.py   # 基于 LangGraph 的状态机流转 (包含 Supervisor)
│   │   │
│   │   ├── agents/                    # 🤖 具体智能体节点
│   │   │   ├── supervisor_agent.py    # 大管家 Agent 
│   │   │   ├── tech_agent.py          # 技术支持 Agent
│   │   │   └── service_agent.py       # 售后服务 Agent
│   │   │
│   │   ├── mcp/                       # 🌟 Model Context Protocol
│   │   │   ├── client.py              
│   │   │   └── servers/               # db_mcp.py / device_mcp.py
│   │   │
│   │   └── llm/                       # 大模型调用封装 (llm_client.py)
│   │
│   ├── knowledge_platform_backend/    # ==========================================
│   │                                  # 📚 知识平台后端 (RAG 数据治理与召回引擎)
│   │                                  # ==========================================
│   │   ├── main.py                    # 端口 8001
│   │   ├── api/                       # 上传、搜索接口
│   │   ├── rag/                       # 🚀 三路召回、切分器、Query 重写引擎
│   │   ├── vector_store/              # ChromaDB 实例封装
│   │   └── database/                  # 知识库侧业务表
│
│
├── frontend/                          # ⭐ 前端系统 (Vue 3 + Vite)
│
│   ├── customer_service_frontend/     # 💬 2C 端：用户聊天系统
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   └── src/
│   │       ├── App.vue                # 🚀 重构: 极客暗黑风 UI (集成流式打字机、折叠动画)
│   │       ├── api/                   # 对接后端 /api/query 与 /api/user_sessions
│   │       └── assets/                # svg 图标、全局 css
│   │
│   └── knowledge_platform_frontend/   # ⚙️ 2B 端：内部知识管理后台
│       ├── package.json
│       └── src/
│           ├── layout/index.vue       # 胶囊导航栏、顶部面包屑布局
│           └── views/
│               └── KnowledgeBase.vue  # 拖拽上传、切片预览
│
│
├── data_pipeline/                     # ⭐ 离线数据处理流水线
│   ├── crawlers/                      # 数据采集 (官网维修手册)
│   ├── processing/                    # 数据清洗 (去重、提取)
│   └── utils/
│
│
├── data/                              # ⭐ 本地数据存储 (已加入 .gitignore)
│   ├── sessions/                      # 🚀 新增: 用户的 JSON 历史对话记忆存放区
│   │   └── root1/                     # └─ 隔离的用户目录
│   │       ├── session_xxx.json       #    └─ 完整的 BaseMessage 上下文
│   │       └── session_yyy.json       
│   ├── raw/                           # 原始网页/PDF
│   ├── cleaned/                       # 清洗后的标准 Markdown
│   └── vector_store/                  # ChromaDB 持久化 SQLite 数据文件
│
│
├── evaluation/                        # ⭐ AI 质量评估模块 (rag_eval, agent_eval)
├── observability/                     # ⭐ 系统监控与可观测性 (tracing, metrics)
├── scripts/                           # ⭐ 自动化与运维脚本 (init_mysql.py, start_all.sh)
└── logs/                              # ⭐ 全局日志输出目录
```

---

# 这个结构的核心优势

### 1️⃣ 清晰的四模块系统

```text
frontend/
services/
```

拆成：

* 客服系统
* 知识库系统

完全独立。

---

### 2️⃣ AI核心层集中在

```text
customer_service_backend/
```

包含：

* Agent
* RAG
* LLM
* Memory

---

### 3️⃣ 知识库平台独立

```text
knowledge_platform_backend/
```

只负责：

* 文档上传
* 文档解析
* 向量化

---

### 4️⃣ 数据流水线独立

```text
data_pipeline/
```

专门处理：

```
爬虫 → 清洗 → chunk → vector db
```

---

### 5️⃣ 加入 AI 产品必须的模块

```text
evaluation/        # AI质量评估
observability/     # AI监控
```

很多项目一开始没有，但 **生产环境一定需要**。

---

如果是 **真正做成企业级 AI 客服系统**，我还会再补一个 **最终形态架构（很多 AI 公司都这样）**：

```
infra/
gateway/
workers/
```

这样你的系统可以支持 **异步任务、队列、AI推理扩展**。

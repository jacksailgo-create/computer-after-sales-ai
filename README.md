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

# ITS 智能客服与知识库平台 —— 全栈技术架构

##  1、概览

本项目主要围绕 **ITS（Intelligent Technical Service）智能客服系统** 与 **ITS 知识库平台** 两大核心项目展开，涵盖 **两个前端 + 两个后端** 的完整技术栈，构建从需求分析 → 架构设计 → 编码实现 → 全链路能力。

| 项目                 | 类型             | 核心价值                                                     |
| -------------------- | ---------------- | ------------------------------------------------------------ |
| **ITS 智能客服系统** | 多智能体对话系统 | 实现“调度-技术-业务”三层智能体协作，支持服务站导航、技术问答等复杂场景 |
| **ITS 知识库平台**   | RAG 文档问答系统 | 支持私域知识上传、向量化存储、语义检索与生成式问答           |


## 2、ITS 智能客服（多智能体架构）

### 1.1 技术栈全景

| 层级             | 技术选型                                 | 说明                           |
| ---------------- |--------------------------------------| ------------------------------ |
| **语言**         | Python 3.x                           | 主力开发语言                   |
| **Web 框架**     | FastAPI                              | 高性能异步框架                 |
| **服务器**       | Uvicorn                              | 高性能web 服务器               |
| **智能体框架**   | `langgraph`（基于 supervisor 模式）        | 轻量级多 Agent 编排            |
| **LLM 接入**     | OpenAI SDK（兼容阿里百炼等）                  | 统一接口，模型可替换           |
| **外部工具协议** | **MCP (Model Context Protocol)**     | 标准化连接地图、搜索等外部服务 |
| **数据库**       | MySQL + `pymysql` + `sqlite_pool` + `sqlite` | 连接池保障高并发稳定性         |
| **数据验证**     | `pydantic`                           | 运行时类型检查与序列化         |
| **HTTP 客户端**  | `httpx`（异步）、`requests`（同步）           | 外部 API 调用                  |
| **日志**         | Python `logging`                     | 结构化日志输出                 |

### 1.2 分层架构设计
看上面的架构图，可以清晰地看到整个系统架构。

### 1.3 关键工作流

1. 请求处理流:

  前端发送请求 -> `routes.py` 接收 -> `AgentService` 初始化上下文 -> `SessionManager` 加载历史 -> 启动 `Runner`。



2. 智能体编排流:

  `Supervisor` 分析意图 -> (Handoff) -> `TechnicalAgent` / `ServiceAgent` -> 执行工具 (Tools/MCP) -> 返回结果 -> `Supervisor` 汇总 -> 输出给用户。



3. 流式响应流:

  智能体产生的每个 Token 或事件 (Event) -> `stream_response_service.py` 捕获并格式化 -> SSE 响应 -> 前端实时渲染。



### 1.4 关键设计



- 模块化提示词管理: 提示词 (Prompts) 从代码中剥离，存储在 `prompts/` 目录，便于非技术人员维护和迭代。

- 连接池管理: 使用 `sqlite` 管理数据库连接，避免频繁创建/销毁连接带来的开销。

- MCP 扩展性: 通过 MCP 协议集成外部工具，使得系统可以轻松扩展新的能力（如接入新的搜索源或 API）而不破坏核心逻辑。



##  3、ITS 智能客服前端（Vue 3 ）

### 3.1 技术栈全景

| 类别              | 技术                             | 作用                                 |
| ----------------- | -------------------------------- | ------------------------------------ |
| **框架**          | Vue 3 (Composition API)          | 组件化开发，逻辑复用                 |
| **构建工具**      | Vite                             | 极速冷启动 + HMR                     |
| **UI 库**         | Element Plus                     | 企业级组件（Input, Button, Loading） |
| **Markdown 渲染** | `marked` + `github-markdown.css` | 实时渲染 AI 返回的富文本             |
| **通信**          | `fetch` + `ReadableStream`       | 处理 SSE 流式响应                    |

------

### 3.2 分层架构设计

系统代码组织在 `front/its_front`，遵循标准的 Vue + Vite 项目结构：

\-  `src/`: 源代码目录

  \-  `assets/`: 静态资源（图片、样式文件）。

  \-  `App.vue`: 应用的根组件，通常包含主要的布局和对话窗口逻辑。

  \-  `main.js`: 入口文件，负责初始化 Vue 应用、引入 Element Plus 和全局样式。

  \-  `style.css`: 全局样式定义。



### 3.3 关键工作流

前端主要负责与后端 `AgentService` 进行实时交互，核心流程如下：



1. 消息发送:

  \-  用户在输入框输入问题。

  \-  前端通过 `fetch` 或 `axios` (或其他 HTTP 客户端) 向后端 `/api/query` 接口发送 POST 请求。

  \-  请求体包含：`query` (用户问题), `context` (包含 sessionId, userId 等上下文信息)。



2. 流式接收 (Server-Sent Events):

  \-  由于智能体生成回答需要时间，且需要打字机效果，后端采用流式响应。

  \-  前端利用 `fetch` API 的 `ReadableStream` 或 `EventSource` 监听响应流。

  \-  增量渲染: 每接收到一个数据块 (Chunk)，立即追加到当前对话气泡的消息内容中，并调用 `marked.parse()` 实时更新 HTML。



3. 状态管理:

  \-  虽然项目规模较小可能未引入 Pinia/Vuex，但组件内部利用 Vue 3 的 `ref` 和 `reactive` 管理以下状态：

​    \-  `messages`: 消息列表数组 (用户提问 + AI 回答)。

​    \-  `isLoading`: 加载状态，用于显示 Loading 动画或禁用输入框。

​    \-  `inputText`: 输入框当前内容。



### 3.4 关键设计

- Chat UI 布局：消息列表 + 输入框
- 实时打字机效果
- Markdown 支持：代码块、列表、加粗等自动高亮
- Loading 状态：禁用输入框 + 动画提示



## 4、ITS 知识库平台（RAG 架构）

### 4.1 技术栈全景

| 类别               | 技术                                        | 说明                           |
| ------------------ | ------------------------------------------- | ------------------------------ |
| **框架**           | FastAPI + Uvicorn                           | 同智能客服后端                 |
| **RAG 编排**       | LangChain                                   | 文档加载 → 切分 → 检索 → 生成  |
| **向量数据库**     | ChromaDB                                    | 本地持久化，轻量级             |
| **Embedding 模型** | OpenAI text-embedding-ada-002（或兼容模型） | 文本向量化                     |
| **LLM**            | OpenAI GPT / 通义千问（兼容 OpenAI API）    | 生成答案                       |
| **文档处理**       | `unstructured`, `markdownify`, `jieba`      | PDF/HTML → Markdown → 中文分词 |
| **配置管理**       | `pydantic-settings` + `.env`                | 环境变量驱动                   |



### 4.2 分层架构设计

系统代码组织在 `backend/knowlege` 下，主要分为以下几层：
看上面的架构图，可以清晰地看到整个系统架构

### 4.3 关键工作流

**知识入库流程 (Upload )**

1. 上传: 用户通过 `/upload` 接口上传文件 (如 HTML, PDF)。

2. 预处理: `FileProcessor` 调用 `TextUtils` 清洗文本，将 HTML 转换为 Markdown。

3. 切分: 使用 LangChain 的 Splitter 将长文档切分为较小的 Chunks。

4. 向量化与存储: 调用 Embedding 模型将 Chunks 转换为向量，并存入 `ChromaDB` (`data_access` 层)。

**知识问答流程 (Retrieval )**

1. 提问: 用户通过 `/query` 接口发送问题。

2. 检索: `RetrievalService` 将问题向量化，在 `ChromaDB` 中查找 Top-K 相关文档片段。

3. 生成: `QueryService` 将“系统指令 + 检索到的上下文 + 用户问题”组装成 Prompt。

4. 回答: 调用 LLM 生成回答，并返回给用户。



### 4.4 关键设计

\-	本地化向量存储:	使用 ChromaDB 本地持久化，无需依赖外部复杂的向量数据库服务，部署轻量。

\-	格式标准化:	 统一将多源文档转换为 Markdown 格式处理，保留了文档的结构信息（标题、列表），有助于提升 LLM 的理解能力。

 \-	模块化:	 RAG将检索 (Retrieval) 和生成 (Generation) 解耦，便于独立优化（例如更换检索算法或更换 LLM 模型）。



##  5、知识库平台前端（Vue 3）

### 4.1 技术栈全景

| 技术                     | 作用                           |
| ------------------------ | ------------------------------ |
| Vue 3 + `<script setup>` | 组合式 API 开发                |
| Vite                     | 构建工具                       |
| Vue Router 4             | 路由管理（/knowledge ↔ /chat） |
| Element Plus             | Upload、Table、Card 等组件     |
| Axios                    | HTTP 请求封装（带拦截器）      |
| marked                   | Markdown 渲染                  |



### 4.2 分层架构设计

项目遵循标准的 Vue 3 + Vite 工程结构，位于 `front/its_knowlege_platform`：

\-  `src/api/`: API 接口封装。

  \-  `request.js`: Axios 实例配置，包含 baseURL (`/api`) 和响应拦截器。

  \-  `knowledge.js`: 定义具体业务接口（如 `uploadFile`）。

\-  `src/assets/`: 静态资源（图片、SVG）。

\-  `src/components/`: 公共组件。

\-  `src/layout/`: 布局组件。

  \-  `index.vue`: 应用的主布局框架（通常包含侧边栏/导航栏和 `RouterView`）。

\-  `src/router/`: 路由配置。

  \-  `index.js`: 定义路由表，包括 `/knowledge` (知识库管理) 和 `/chat` (智能问答) 两个主要页面。

\-  `src/views/`: 页面级组件。

  \-  `Knowledge.vue`: 知识库管理页，提供文件上传和上传记录展示功能。

  \-  `Chat.vue`: 智能问答页，提供对话交互界面。

\-  `src/App.vue`: 根组件。

\-  `src/main.js`: 入口文件，负责初始化 Vue 应用、注册 Element Plus 和 Router。



### 4.3 关键工作流

1. 知识库管理 (****`Knowledge.vue`****)

   文件上传: 使用 Element Plus 的 `el-upload` 组件，支持拖拽上传。

   交互逻辑:

     \-  前端通过 `FormData` 封装文件。

     \-  调用后端 `/api/upload` 接口。

     \-  实时维护 `uploadHistory` 列表，展示文件名、新增切片数 (Chunks) 和上传状态。

2. 智能问答 (****`Chat.vue`****)

   \-  **(根据路由推断)** 提供对话界面，用户输入问题后，调用后端 `/api/query` 接口。

   \-  使用 `marked` 将后端返回的 Markdown 答案渲染为 HTML，并应用 `github-markdown.css` 样式以保证良好的阅读体验。

3. 网络请求封装

   \-  `src/api/request.js` 统一封装了 Axios 实例。

   \-  BaseURL: 设置为 `/api`，配合 Vite 的代理配置 (Proxy) 解决开发环境跨域问题。

   \- 拦截器: 统一处理响应数据（直接返回 `response.data`）和错误捕获。


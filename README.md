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
├── core/                              # ⭐ 全局核心基础设施（双端微服务共享）
│   ├── config.py                      # 👈 我们写的 OmegaConf 配置单例 (AppConfigManager)
│   ├── conf/                          # 全局 YAML 配置文件
│   │   ├── config.yaml                # 主配置文件 (llm, rag, database 等)
│   │   ├── logging.yaml               # 日志滚动策略
│   │   └── crawler.yaml               # 爬虫策略
│   ├── logger.py                      # 全局日志初始化
│   ├── exceptions.py                  # 自定义异常类
│   ├── constants.py                   # 全局常量
│   └── utils/                         # 通用工具函数 (time_utils, file_utils)
│
├── services/                          # ⭐ 双核微服务集群
│
│   ├── customer_service_backend/      # ==========================================
│   │                                  # 🤖 智能客服后端 (多 Agent 调度中枢)
│   │                                  # ==========================================
│   │   ├── main.py                    # FastAPI 启动入口 (端口 8000)
│   │   ├── api/                       
│   │   │   └── routes_chat.py         # 👈 给 Vue 前端调用的对话接口 (支持 SSE 流式)
│   │   │
│   │   ├── clients/                   # 🔌 微服务通信层
│   │   │   └── kb_client.py           # 🌟 封装 HTTP/RPC 请求，去调用隔壁知识库后端的 /search 接口
│   │   │
│   │   ├── mcp/                       # 🌟 Model Context Protocol (模型上下文协议)
│   │   │   ├── client.py              # MCP 客户端 (供 Agent 统一调用底下的 Server)
│   │   │   └── servers/               # MCP 协议服务器端
│   │   │       ├── db_mcp.py          # 暴露本地 MySQL (查保修期、订单状态)
│   │   │       └── device_mcp.py      # 暴露设备硬件级检测工具
│   │   │
│   │   ├── agents/                    # 🧠 多 Agent 团队
│   │   │   ├── supervisor_agent.py    # 大管家 Agent (判断意图：查知识库? 查订单? 转人工?)
│   │   │   ├── diagnosis_agent.py     # 故障诊断 Agent (负责排障逻辑)
│   │   │   └── human_handoff_agent.py # 转人工兜底 Agent
│   │   │
│   │   ├── workflows/                 # Agent 编排逻辑
│   │   │   └── after_sales_graph.py   # 基于 LangGraph 的状态机流转
│   │   │
│   │   ├── llm/                       # 大模型调用封装
│   │   │   └── llm_client.py          # LLM API 统一出口
│   │   │
│   │   ├── prompts/                   # Prompt 模板库 (.yaml 或 .py)
│   │   │
│   │   ├── memory/                    # AI 记忆系统
│   │   │   ├── short_term_redis.py    # Redis：管理当前 Session 的多轮对话历史
│   │   │   └── long_term_db.py        # MySQL：记录用户的历史维修偏好
│   │   │
│   │   └── database/                  # 关系型数据库 (客服侧业务表)
│   │       ├── models_ticket.py       # 工单表、用户会话表
│   │       └── session.py             
│
│
│   ├── knowledge_platform_backend/    # ==========================================
│   │                                  # 📚 知识平台后端 (RAG 数据治理与召回引擎)
│   │                                  # ==========================================
│   │   ├── main.py                    # FastAPI 启动入口 (端口 8001)
│   │   ├── api/                       
│   │   │   ├── routes_upload.py       # 内部运营人员传文档的接口
│   │   │   └── routes_search.py       # 🌟 专供 customer_service_backend 调用的检索引擎入口
│   │   │
│   │   ├── rag/                       # 👈 我们手写的最硬核的 RAG 核心
│   │   │   ├── hybrid_search.py       # 🚀 三路召回引擎 (Dense + BM25正文 + BM25标题)
│   │   │   ├── splitters/             
│   │   │   │   └── smart_splitter.py  # 🚀 Markdown 层级与 QA 结构防断裂切分器
│   │   │   └── query_optimizer.py     # 🚀 Jieba 同义词正则规整 + LLM Query 扩写
│   │   │
│   │   ├── loaders/                   # 文档解析
│   │   │   ├── pdf_loader.py
│   │   │   └── markdown_loader.py
│   │   │
│   │   ├── vector_store/              # 向量数据库接口
│   │   │   └── chroma_store.py        # ChromaDB 实例封装
│   │   │
│   │   └── database/                  # 关系型数据库 (知识库侧业务表)
│   │       ├── models_doc.py          # 知识库文档元数据表、向量化任务状态表
│   │       └── session.py
│
│
├── frontend/                          # ⭐ 前端系统 (Vue 3 + Vite)
│
│   ├── customer_service_frontend/     # 💬 2C 端：用户聊天系统
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   └── src/
│   │       ├── api/knowledge.js       # 请求客服后端的对话接口
│   │       ├── views/
│   │       │   └── Chat.vue           # 👈 我们写的极客暗黑风对话框 (带防脱壳、打字机特效)
│   │       └── components/
│   │           └── ChatBubble.vue     # 抽离出的 Markdown + 代码高亮气泡组件
│   │
│   └── knowledge_platform_frontend/   # ⚙️ 2B 端：内部知识管理后台
│       ├── package.json
│       └── src/
│           ├── layout/index.vue       # 👈 左侧胶囊导航栏、顶部面包屑布局
│           ├── router/index.js        # 👈 NProgress 进度条与动态路由守卫
│           ├── api/request.js         # Axios 统一拦截器
│           └── views/
│               └── KnowledgeBase.vue  # 拖拽上传、切片预览、打入知识库界面
│
│
├── data_pipeline/                     # ⭐ 离线数据处理流水线
│   ├── crawlers/                      # 数据采集 (爬取联想/戴尔官网维修手册)
│   │   ├── forum_crawler.py
│   │   └── manual_crawler.py
│   ├── processing/                    # 数据清洗
│   │   ├── html_parser.py
│   │   ├── cleaner.py                 # 清理 HTML 标签、水印、无效字符
│   │   └── deduplicator.py            # 文本去重
│   └── utils/
│       └── storage.py
│
│
├── data/                              # ⭐ 本地数据存储 (不提交 Git)
│   ├── raw/                           # 原始网页/PDF
│   ├── cleaned/                       # 清洗后的标准 Markdown
│   ├── chunks/                        # 切分后的 JSON 块备份
│   └── vector_store/                  # ChromaDB 持久化 SQLite 数据文件
│
│
├── evaluation/                        # ⭐ AI 质量评估模块
│   ├── rag_eval.py                    # 评估召回率 (Hit Rate)、MRR
│   ├── agent_eval.py                  # 评估 Agent 路由准确率、幻觉率 (Faithfulness)
│   └── datasets/                      # 黄金测试集 (100 个极其刁钻的售后问题)
│
│
├── observability/                     # ⭐ 系统监控与可观测性
│   ├── tracing.py                     # LangSmith / Phoenix 调用链追踪配置
│   ├── metrics.py                     # Prometheus 统计 Token 消耗与接口 Latency
│   └── cost_tracker.py                # 记录不同模型的费用支出
│
│
├── scripts/                           # ⭐ 自动化与运维脚本
│   ├── init_mysql.py                  # 初始化数据库表结构
│   ├── build_vector_db.py             # 一键将 data/cleaned 跑通流水线打入 ChromaDB
│   └── start_all.sh                   # 一键拉起前后端双微服务
│
│
├── tests/                             # ⭐ 自动化测试
│   ├── test_agents/
│   ├── test_rag/                      # 针对三路召回、Jieba分词写单测
│   └── test_pipeline/
│
└── logs/
    ├── customer_service.log           # 客服后端日志
    └── knowledge_platform.log         # 知识库后端日志
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

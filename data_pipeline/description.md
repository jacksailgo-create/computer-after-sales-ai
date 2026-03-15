到这一步，整个 RAG 架构的前半部分（数据接入与处理层 Data Pipeline）已经完全杀青了！
我们一起打通了：

获取：多线程反爬虫网页抓取 (manual_crawler.py)

清洗：过滤广告牛皮癣与 Markdown 格式化 (html_parser.py)

治理：提取 YAML 元数据并规范化落盘 (storage.py)

切分：保留 Markdown 标题层级的智能切块 (text_splitter.py)

入库：调用 Embedding 并分批持久化到本地 (build_vector_db.py)
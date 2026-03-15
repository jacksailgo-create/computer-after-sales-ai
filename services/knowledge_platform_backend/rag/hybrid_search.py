import logging
import re

import jieba
import numpy as np
from typing import List
from langchain_core.documents import Document

# 全文检索依然用 LangChain 封装的
from langchain_community.retrievers.bm25 import BM25Retriever
# 标题检索我们直接用底层的 rank_bm25，更加灵活
from rank_bm25 import BM25Okapi

from knowledge_platform_backend.rag.vector_store import vector_db
from core.config import app_config

logger = logging.getLogger(__name__)


STOP_WORDS = {"的", "了", "和", "是", "就", "都", "而", "及", "与", "着", "怎么", "如何", "办", "什么", "为何", "？",
              "。"}

def jieba_preprocess(text: str) -> List[str]:
    """
    工业级文本预处理与分词流水线
    """
    if not text:
        return []

    # ==========================================
    # 🌟 核心拦截层 1：全局小写化 (Lowercase)
    # 解决 Windows vs windows 的匹配问题
    # ==========================================
    text = text.lower()

    # 这一行正则会捕获：win, window, windows + 任意数量的空格 + 任意数字
    # 然后统一替换为：windows + 空格 + 提取到的数字
    text = re.sub(r'win(?:dow|dows)?\s*(\d+)', r'windows \1', text)

    # (如果是苹果电脑的代称，也可以用正则搞定)
    # 比如把 mac、macpro、macbook pro 统一规整为 macbook
    text = re.sub(r'mac(?:book)?\s*(?:pro|air)?', 'macbook', text)

    # 你可以顺手加上其他的售后常见同义词
    # text = text.replace("macbook", "mac")
    # text = text.replace("没网", "无法连接网络")
    # text = text.replace("卡死", "死机")

    # ==========================================
    # 🌟 核心拦截层 3：中英文/数字智能加空格 (可选但极其强大)
    # 防止用户输入 "U盘安装" (连着)，而文档是 "U盘 安装"
    # ==========================================
    # 在英文字母/数字和中文之间强行插入空格，帮助 jieba 更好地切分边界
    text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fa5])', r'\1 \2', text)
    text = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9])', r'\1 \2', text)

    # 最后再交给 Jieba 进行分词
    tokens = jieba.lcut_for_search(text)

    # 过滤停用词和空白字符
    return [token for token in tokens if token.strip() and token not in STOP_WORDS]


class HybridRetrieverManager:
    """
    企业级三路检索器 (Triple-Way Hybrid Retriever)
    1. Dense Vector: 负责语义泛化
    2. Content BM25: 负责正文细节匹配
    3. Title BM25: 负责主标题/核心症状的“一击必杀”
    """

    def __init__(self):
        logger.info("⚙️ 正在初始化三路召回 (Triple-Way Hybrid) 检索器...")
        self.retrieval_top_k = app_config.rag.retrieval_top_k

        # 1. 向量检索路 (Dense)
        self.dense_retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.retrieval_top_k}
        )

        self.original_docs = []
        self.content_bm25 = None
        self.title_bm25 = None

        self.reload_index()

    def reload_index(self):
        """全量热刷新：同时构建正文和标题两套倒排索引"""
        logger.info("🔄 正在构建双重 BM25 倒排索引树 (正文 + 标题)...")
        try:
            db_data = vector_db.get(include=['documents', 'metadatas'])
            docs = db_data.get('documents', [])
            metas = db_data.get('metadatas', [])

            if not docs:
                logger.warning("⚠️ 向量库为空，退化为纯向量检索。")
                return

            self.original_docs = [
                Document(page_content=doc, metadata=meta or {})
                for doc, meta in zip(docs, metas)
            ]

            # ==========================================
            # 2. 正文 BM25 (负责捞细节)
            # ==========================================
            self.content_bm25 = BM25Retriever.from_documents(
                documents=self.original_docs,
                preprocess_func=jieba_preprocess
            )
            self.content_bm25.k = self.retrieval_top_k

            # ==========================================
            # 3. 标题专属 BM25 (一击必杀的狙击枪)
            # ==========================================
            # 强行把 main_title
            title_texts = []
            for meta in metas:
                t = meta.get('main_title', '')
                title_texts.append(t)

            tokenized_titles = [jieba_preprocess(t) for t in title_texts]
            self.title_bm25 = BM25Okapi(tokenized_titles)

            logger.info(f"✅ 双重 BM25 刷新完成！当前语料块: {len(self.original_docs)}")

        except Exception as e:
            logger.error(f"❌ 刷新索引时发生严重错误: {e}")

    def search(self, query: str) -> List[Document]:
        logger.info(f"🔍 [Triple Search] 启动三路并发召回: '{query}'")
        try:
            # 1. 获取向量结果
            dense_docs = self.dense_retriever.invoke(query)

            # 2. 获取正文 BM25 结果
            content_docs = self.content_bm25.invoke(query) if self.content_bm25 else []

            # 3. 获取标题 BM25 结果
            title_docs = []
            if self.title_bm25:
                tokenized_query = jieba_preprocess(query)
                scores = self.title_bm25.get_scores(tokenized_query)
                # 取出得分大于 0 的前 5 名
                top_indices = np.argsort(scores)[::-1][:self.retrieval_top_k]
                title_docs = [self.original_docs[i] for i in top_indices if scores[i] > 0]

            # 4. 执行倒数排名融合 (RRF)
            final_docs = self._rrf_fusion([dense_docs, content_docs, title_docs])
            logger.info(f"🎯 融合完毕，提取出 {len(final_docs)} 个最优切片。")
            return final_docs

        except Exception as e:
            logger.error(f"❌ 多路检索发生异常: {e}")
            return []

    def _rrf_fusion(self, results_list: List[List[Document]], k=60) -> List[Document]:
        """
        手写 RRF (Reciprocal Rank Fusion) 融合算法。
        将三路召回的结果按排名打分，并根据哈希去重。
        """
        score_map = {}
        doc_map = {}

        for doc_list in results_list:
            for rank, doc in enumerate(doc_list):
                # 使用内容的哈希值来做去重的主键
                doc_hash = hash(doc.page_content)
                if doc_hash not in doc_map:
                    doc_map[doc_hash] = doc
                    score_map[doc_hash] = 0.0

                # RRF 核心数学公式
                # 公式：Score = Score + 1 / (k + rank)
                score_map[doc_hash] += 1.0 / (k + rank)

        # 按照最终融合得分降序排列
        sorted_hashes = sorted(score_map.keys(), key=lambda x: score_map[x], reverse=True)

        # 截取最终的 Top 5 返回给大模型
        return [doc_map[h] for h in sorted_hashes[:self.retrieval_top_k]]


hybrid_retriever = HybridRetrieverManager()
import sys
from pathlib import Path

# 确保能正确引入项目根目录下的模块
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 引入全局日志初始化，让我们的输出漂漂亮亮
from core.logger import setup_global_logger
import logging

# 引入我们亲手打造的两大神器
from services.knowledge_platform_backend.rag import MarkdownDirectoryLoader
from services.knowledge_platform_backend.rag import QADocumentSplitter

# 也可以引入配置，动态获取路径
from core.config import AppConfig

# 获取当前模块的 logger
logger = logging.getLogger(__name__)


def run_pipeline():
    print("\n" + "=" * 50)
    print("🚀 开始联调：Markdown 文件加载与智能切分流水线")
    print("=" * 50 + "\n")

    # ==========================================
    # 阶段 1：Extract (提取) - 加载本地 Markdown
    # ==========================================
    logger.info("【阶段 1】初始化 Markdown 加载器...")
    # 我们指定读取 data/cleaned/manuals 目录（你之前爬虫存数据的地方）
    # 如果你想测试所有数据，可以只传 "data/cleaned"
    target_dir = f"{AppConfig.storage.cleaned_dir}/manuals"
    loader = MarkdownDirectoryLoader(directory_path=target_dir)

    raw_documents = loader.load()

    if not raw_documents:
        logger.error("❌ 没有读取到任何文档，请检查目录路径或先运行爬虫脚本！")
        return

    logger.info(f"✅ 成功从 {target_dir} 加载了 {len(raw_documents)} 篇长文档。\n")

    # ==========================================
    # 阶段 2：Transform (转换) - 智能双重切分
    # ==========================================
    logger.info("【阶段 2】初始化 Markdown 智能切分器...")
    # 设置 chunk_size 为 1500 字符，overlap 100 字符，适合大多数中文大模型的上下文窗口
    splitter = QADocumentSplitter(chunk_size=1500, chunk_overlap=100)

    final_chunks = splitter.split_documents(raw_documents)

    logger.info(f"✅ 魔法完成！{len(raw_documents)} 篇文档被切分成了 {len(final_chunks)} 个向量块。\n")

    # ==========================================
    # 阶段 3：效果抽查 (验证结构化数据)
    # ==========================================
    print("=" * 50)
    print("🎯 切分效果抽查 (展示前 2 个 Chunk)")
    print("=" * 50)

    # 抽取前两个切块展示
    for i, chunk in enumerate(final_chunks):
        print(f"\n📦 【Chunk {i + 1}】")
        print(f"📄 正文片段 (长度: {len(chunk.page_content)} 字符):")
        # 截取前 150 个字符展示，避免刷屏
        preview_text = chunk.page_content[:350].replace('\n', ' ')
        print(f"   {preview_text}...")

        print("\n🏷️  融合后的极致 Metadata:")
        for key, value in chunk.metadata.items():
            # 突出显示标题层级和来源信息
            if "Header" in key or key in ["source", "category"]:
                print(f"   ⭐ {key}: {value}")
            else:
                print(f"   - {key}: {value}")
        print("-" * 50)


if __name__ == "__main__":
    # 初始化全局日志
    setup_global_logger()
    # 运行流水线
    run_pipeline()
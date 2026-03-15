import logging
import random
import time
from http.client import HTTPException

import requests
from core.config import AppConfig

from data_pipeline.processing.html_parser import HtmlToMarkdownTool
from data_pipeline.utils.storage import LocalStorageHandler

# ✅ 核心修复：必须在最前面引入我们自己写的 logger 模块
# 这样 setup_global_logger() 就会被执行，把文件写入规则挂载到全局
import core.logger
# 使用我们配置好的全局日志
logger = logging.getLogger(__name__)

class ManualCrawler:
    def __init__(self):
        self.config = AppConfig

    def get_html(self, knowledge_no:int) -> str:
        """
        根据知识库编号，获取联想知识库内容：
        :param self:
        :param knowledge_no: 编号
        :return:
        """

        # 1. 定义url
        base_url = self.config.sites.manuals[0].base_url
        knowledge_base_url = self.config.sites.manuals[0].knowledge_base_url

        # 2. 定义参数
        params = {'knowledgeNo':knowledge_no}

        try:
            # 3. 发起请求
            response = requests.get(url=base_url+knowledge_base_url, params=params, timeout=10)
            if response.status_code == 200:
                # 知识库内容
                knowledge_dict = response.json()
                return knowledge_dict['data']
        except HTTPException as e:
            logging.error(f"Error fetching URL: {e}")
            raise HTTPException(f'知识库请求异常:{e}')

    def batch_crawl_manuals(self, start_id: int = 1, end_id: int = 100, base_delay: float = 1.0):
        """
        批量抓取售后手册并保存到本地

        :param start_id: 起始知识库 ID
        :param end_id: 结束知识库 ID
        :param base_delay: 每次抓取后的基础延迟(秒)，防止触发反爬被封 IP
        """
        logger.info(f"🚀 开始批量抓取手册任务，范围: {start_id} 到 {end_id}")

        # ==========================================
        # 1. 实例化工具 (必须放在循环外，避免重复创建消耗内存)
        # ==========================================
        parser = HtmlToMarkdownTool(strip_images=False)
        storage = LocalStorageHandler(base_output_dir=self.config.storage.cleaned_dir)

        # 提取配置中的常用变量
        manual_config = self.config.sites.manuals[0]
        site_name = manual_config.name
        # 提前拼接好 URL 的基础部分
        base_url = manual_config.base_url + manual_config.knowledge_base_url

        # 统计数据
        success_count = 0
        fail_count = 0

        # ==========================================
        # 2. 进入批量遍历
        # ==========================================
        for current_id in range(start_id, end_id + 1):
            target_url = f"{base_url}?knowledgeNo={current_id}"
            logger.info(f"⏳ 正在处理 [{current_id - start_id + 1}/{end_id - start_id + 1}] ID={current_id}...")

            # 【核心】：一定要加上 try-except，防止某一个坏数据导致整个脚本崩溃！
            try:
                # 步骤 A: 爬取 HTML
                html_result = crawler.get_html(current_id)
                if not html_result:
                    logger.warning(f"⚠️ ID {current_id} 页面获取为空，已跳过。")
                    fail_count += 1
                    continue

                # 步骤 B: 转换 Markdown
                # 注意: 这里顺应你代码里写的 parser_html 方法名
                clean_markdown = parser.parser_html(knowledge_no=current_id, html_data=html_result)
                if not clean_markdown:
                    logger.warning(f"⚠️ ID {current_id} 转换 Markdown 后为空。")
                    fail_count += 1
                    continue

                # 步骤 C: 落盘保存
                saved_path = storage.save_markdown(
                    content=clean_markdown,
                    source_name=site_name,
                    url=target_url,
                    category="manuals"  # 明确分类为手册
                )

                if saved_path:
                    success_count += 1
                    logger.debug(f"✅ ID {current_id} 成功落盘: {saved_path.name}")
                else:
                    fail_count += 1

            except Exception as e:
                # logger.exception 会自动把报错代码的行数和堆栈打出来，极其方便排错
                logger.exception(f"❌ 处理 ID {current_id} 时发生未捕获异常: {e}")
                fail_count += 1

            # ==========================================
            # 3. 反爬虫礼貌延时 (极度重要)
            # ==========================================
            # 加入一个随机抖动，比如基础延迟 1秒，实际延迟 1.0 ~ 2.0 秒之间，模拟人类操作
            sleep_time = base_delay + random.uniform(0, 1.0)
            time.sleep(sleep_time)

        # 循环结束，打印汇总报告
        logger.info("=" * 40)
        logger.info(f"🎉 批量抓取任务结束！")
        logger.info(f"📊 总计划: {end_id - start_id + 1} 篇")
        logger.info(f"✅ 成功: {success_count} 篇")
        logger.info(f"❌ 失败/跳过: {fail_count} 篇")
        logger.info("=" * 40)

if __name__ == '__main__':
    crawler = ManualCrawler()
    # 执行抓取 1 到 100，每次抓完至少休息 1.5 秒
    crawler.batch_crawl_manuals(start_id=1, end_id=1000, base_delay=1.5)






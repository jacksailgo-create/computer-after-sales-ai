from core.config import AppConfig

if __name__ == "__main__":
    # 原来啰嗦的写法：AppConfig.llm_model
    # 现在的点语法：
    print(AppConfig.llm.model)         # 输出: gpt-3.5-turbo
    print(AppConfig.llm.temperature)   # 输出: 0.1
    print(AppConfig.rag.retrieval_top_k) # 输出: 5
    print(AppConfig.llm.base_url)
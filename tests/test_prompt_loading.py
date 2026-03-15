# 引入我们写好的单例
from core.prompt_manager import prompt_manager


def test_prompt_loading():
    # 传入：(文件名不带.md, 角色标识符)
    prompt_text, vars_list = prompt_manager.get_prompt_with_vars("tech_prompts", "tech_agent")

    print("===== 获取到的纯文本 =====")
    print(prompt_text)

    print("\n===== 解析出的必填变量 =====")
    print(vars_list)
    # 输出: ['device_context', 'user_preference']
    # 这可以帮你检查 Markdown 里是不是手滑写错了变量名

if __name__ == "__main__":
    test_prompt_loading()
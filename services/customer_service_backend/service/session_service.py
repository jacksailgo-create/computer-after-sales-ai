import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from core.paths import SESSION_DIR

# 引入 LangChain 核心消息对象及序列化工具
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    messages_to_dict,
    messages_from_dict
)

logger = logging.getLogger(__name__)


class SessionService:
    """
    会话业务管理服务类。
    数据将以友好的、带缩进的中文 JSON 格式存储在 /data/sessions/{user_id}/{session_id}.json
    """

    DEFAULT_SESSION_ID = "default_session"

    def __init__(self, base_data_dir: str = str(SESSION_DIR)):
        self.base_data_dir = base_data_dir
        if not os.path.exists(self.base_data_dir):
            os.makedirs(self.base_data_dir)

    def _get_file_path(self, user_id: str, session_id: str) -> str:
        """内部方法：构建文件路径并确保目录存在"""
        target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID
        user_dir = os.path.join(self.base_data_dir, str(user_id))

        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        return os.path.join(user_dir, f"{target_session_id}.json")

    def prepare_history(self, user_id: str, session_id: str, user_input: str, max_turn: int = 3) -> List[BaseMessage]:
        """准备历史会话 (Agent 运行前调用)"""
        chat_history = self.load_history(user_id, session_id)
        chat_history.append(HumanMessage(content=user_input))
        return self._truncate_history(chat_history, max_turn)

    def load_history(self, user_id: str, session_id: str) -> List[BaseMessage]:
        """
        加载历史会话（读取本地 JSON 文件）
        """
        file_path = self._get_file_path(user_id, session_id)

        # 如果文件不存在，返回初始化的系统指令
        if not os.path.exists(file_path):
            target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID
            return self._init_system_msg_instruct(target_session_id)

        try:
            # 🌟 强制使用 utf-8 读取
            with open(file_path, "r", encoding="utf-8") as f:
                messages_dict = json.load(f)

            # 将字典列表还原为 LangChain 的 Message 对象
            return messages_from_dict(messages_dict)

        except json.JSONDecodeError as e:
            logger.error(f"用户 {user_id} 会话 {session_id} 文件解析失败 原因: {e}")
            return [SystemMessage(content="会话文件读取失败，可能已损坏。")]
        except Exception as e:
            logger.error(f"读取历史记录发生未知错误: {e}")
            return []

    def save_history(self, user_id: str, session_id: str, chat_history: List[BaseMessage]):
        """
        保存历史会话 (Agent 运行后调用)
        """
        if not chat_history:
            return

        try:
            file_path = self._get_file_path(user_id, session_id)

            # 1. 将 LangChain 的 Message 对象转换为字典
            messages_dict = messages_to_dict(chat_history)

            # 2. 🌟 核心修复：ensure_ascii=False 保证中文正常显示，indent=2 保证换行缩进美观
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages_dict, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存用户 {user_id} 会话 {session_id} 文件失败:{str(e)}")

    def get_all_sessions_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有会话列表（供前端侧边栏展示）。
        """
        user_dir = os.path.join(self.base_data_dir, str(user_id))
        if not os.path.exists(user_dir):
            return []

        formatted_sessions = []

        for filename in os.listdir(user_dir):
            if not filename.endswith(".json"):
                continue

            session_id = filename.replace(".json", "")
            file_path = os.path.join(user_dir, filename)

            c_timestamp = os.path.getctime(file_path)
            create_time = datetime.fromtimestamp(c_timestamp).isoformat()

            session_item = {
                "session_id": session_id,
                "create_time": create_time,
            }

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    messages_dict = json.load(f)

                messages = messages_from_dict(messages_dict)

                # 过滤 System 消息，转换为前端字典
                user_visible_memory = [
                    self._msg_to_dict(msg)
                    for msg in messages
                    if not isinstance(msg, SystemMessage)
                ]

                session_item.update({
                    "memory": user_visible_memory,
                    "total_messages": len(user_visible_memory),
                })
            except Exception as e:
                logger.error(f"读取会话 {session_id} 失败: {str(e)}")
                session_item.update({
                    "memory": [],
                    "total_messages": 0,
                    "error": "无法读取会话数据",
                })

            formatted_sessions.append(session_item)

        formatted_sessions.sort(key=lambda x: x.get("create_time") or "", reverse=True)
        return formatted_sessions

    def _init_system_msg_instruct(self, session_id: str) -> List[BaseMessage]:
        return [SystemMessage(content=f"你是一个有记忆的智能体助手，请基于上下文历史会话回答问题 (会话ID {session_id})")]

    def _truncate_history(self, chat_history: List[BaseMessage], max_turn: int = 3) -> List[BaseMessage]:
        system_msgs = [msg for msg in chat_history if isinstance(msg, SystemMessage)]
        non_system_msgs = [msg for msg in chat_history if not isinstance(msg, SystemMessage)]
        msg_limit = max_turn * 2
        truncate_msg = non_system_msgs[-msg_limit:] if msg_limit > 0 else non_system_msgs
        return system_msgs + truncate_msg

    def _msg_to_dict(self, msg: BaseMessage) -> Dict[str, str]:
        role = "unknown"
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, SystemMessage):
            role = "system"
        return {"role": role, "content": msg.content}


# 全局单例
session_service = SessionService()

# ================= 测试代码 =================
if __name__ == '__main__':
    # 配置基础日志
    logging.basicConfig(level=logging.INFO)

    # 测试用户和会话
    test_user = "user_hzk"
    test_session = "session_666"

    print(f"--- 1. 准备/加载历史 (会自动在项目根目录创建 data/{test_user} 文件夹) ---")
    current_history = session_service.prepare_history(test_user, test_session, "我的电脑蓝屏了！")

    print("\n--- 2. 模拟 Agent 运行并生成回答 ---")
    # 追加 Agent 的回答
    current_history.append(AIMessage(content="您好，请问蓝屏时有显示什么错误代码吗？"))

    print("\n--- 3. 保存到文件中 ---")
    session_service.save_history(test_user, test_session, current_history)

    print("\n--- 4. 前端拉取所有会话列表 ---")
    frontend_data = session_service.get_all_sessions_memory(test_user)
    import pprint

    pprint.pprint(frontend_data)
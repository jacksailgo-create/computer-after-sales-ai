import asyncio
import json
import logging
import math
import sqlite3
from typing import Optional
from langchain_core.tools import tool

from customer_service_backend.clients.mcp.mcp_client import load_mcp_map_tools
from customer_service_backend.database.sqlite_pool import SQLiteConnectionPool
from core.paths import DATA_DIR
from customer_service_backend.utils.geo_utils import bd09mc_to_bd09

logger = logging.getLogger(__name__)

@tool()
async def get_user_coordinates(
    user_input: Optional[str] = None,
    user_ip: Optional[str] = None
) -> str:
    """
    智能解析用户当前位置（起点），用于导航或服务站查询。
    ⚠️ 注意：
    - 仅用于获取**起点**，不可作为终点使用。

    Args:
        user_input (str): 用户提到的**明确地名**。⚠️重要：如果用户只说了“附近”、“这里”、“我的位置”等相对方位词，请**留空**此参数（传空字符串），不要填入这些词。
        user_ip (str): 用户当前的**ip**。

    返回 JSON 字符串：
    {
        "ok": bool,
        "lat": float,
        "lng": float,
        "source": "geocode" | "ip" | "fallback",
        "original_input": str,
        "error": str?  # 仅当 ok=False 时存在
    }
    """
    # 1. 相对位置词黑名单 ---
    # LLM 有时会提取出 "附近" 作为参数，但这会导致 Geocode 返回无意义坐标（如城市中心）。
    # 定义这个黑名单，强制这些词触发 IP 定位逻辑。
    RELATIVE_LOCATIONS = {
        "附近", "这", "这里", "这儿", "周围", "周边",
        "我的位置", "当前位置", "所在位置", "nearby", "here"
    }

    # 2. 如果输入的是相对词，视为无效输入，清空它以便触发后续 IP 逻辑
    if user_input in RELATIVE_LOCATIONS:
        logger.info(f"[Location] Detected relative term '{user_input}', forcing IP location fallback.")
        user_input = ""

    tools = await load_mcp_map_tools()
    # 3. 如果有明确的起点位置，调用地理编码接口 (map_geocode)
    if user_input:
        try:
            logger.debug(f"[Location] Trying lat_lng location for: {user_input}")
            # 尝试使用起点名称进行精确定位
            target_tool = next(tool for tool in tools if tool.name == "map_geocode")
            tool_arguments = {
                "address": user_input,
            }

            geo_result = await target_tool.ainvoke(tool_arguments)

            # 3.2 MCP 返回的复杂结构
            text = geo_result[0]['text']
            text = json.loads(text)
            result = text['result']

            # 3.3  校验返回数据的完整性
            if isinstance(result, dict) and "lat" in result['location'] and "lng" in result['location']:
                lat = float(result['location']['lat'])
                lng = float(result['location']['lng'])
                logger.info(f"[Location] Geocode success: '{user_input}' → ({lat}, {lng})")
                return json.dumps({
                    "ok": True,
                    "lat": lat,
                    "lng": lng,
                    "source": "geocode"
                }, ensure_ascii=False)
            else:
                logger.warning(f"[Location] Geocode returned invalid result: {geo_result}")
        except Exception as e:
            # 3.4 如果 Geocode 报错，不抛出异常，而是吞掉错误继续向下走 IP 逻辑
            logger.warning(f"[Location] Geocode failed for '{user_input}': {e}")

    # 4. 尝试 IP 定位
    elif user_ip:
        try:
            logger.debug(f"[Location] Trying IP location for: {user_ip}")
            # 尝试使用用户 IP 进行模糊定位
            target_tool = next(tool for tool in tools if tool.name == "map_ip_location")
            tool_arguments = {
                "ip": user_ip,
            }
            ip_result = await target_tool.ainvoke(tool_arguments)

            # 4.2 解析 MCP 返回的 TextContent
            text = ip_result[0]['text']
            data = json.loads(text)

            # 4.3 检查状态
            if data.get("status") != 0:
                logger.warning(f"[Location] IP location API error: {data.get('message', 'unknown')}")
                raise ValueError("IP location API returned non-zero status")

            point = data.get("content", {}).get("point", {})
            x_str = point.get("x")
            y_str = point.get("y")

            if not x_str or not y_str:
                logger.warning(f"[Location] Missing x/y in IP location result: {data}")
                raise ValueError("Missing x/y coordinates")

            # 4.4 坐标转换
            # 百度 IP API 返回的是 墨卡托坐标 (Mercator)，后续的维修站查询和导航使用的是 经纬度坐标 (Lat/Lng)，必须转换。
            x = float(x_str)
            y = float(y_str)

            lng, lat = bd09mc_to_bd09(x, y)  # 注意顺序：返回 (lng, lat)

            logger.info(f"[Location] IP location success: {user_ip} → ({lat:.6f}, {lng:.6f})")
            return json.dumps({
                "ok": True,
                "lat": lat,
                "lng": lng,
                "source": "ip"
            }, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"[Location] IP location failed for {user_ip}: {e}")
    else:
        #  5. 兜底
        # 防止整个流程失败导致 Agent 崩溃，返回一个默认坐标（通常是北京天安门）
        fallback_lat, fallback_lng = 39.9042, 116.4074
        logger.info("[Location] Using fallback coordinates (Beijing)")

        return json.dumps({
            "ok": False,
            "error": "无法解析用户位置，使用默认坐标",
            "lat": fallback_lat,
            "lng": fallback_lng,
            "source": "fallback"
        }, ensure_ascii=False)


@tool
def find_nearest_stations(user_lat: float, user_lng: float, limit: int = 3):
    """
    根据给定的经纬度坐标，查询数据库中最近的维修站/服务站。

    Args:
        user_lat (float): 纬度 (BD09LL)
        user_lng (float): 经度 (BD09LL)
        limit (int): 返回结果数量限制，默认为 3

    Returns:
        str: JSON 格式的查询结果，包含最近的维修站列表。
    """
    pool = SQLiteConnectionPool(db_path=(str(DATA_DIR)) + '/kb_management.db')
    # ✨ 得益于你的上下文管理器，这里的调用变得极其清爽
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        sql = """
              SELECT id, \
                     service_station_name, \
                     address, \
                     phone, \
                     latitude, \
                     longitude, \
                     haversine_dist(latitude, longitude, ?, ?) AS distance_km
              FROM service_stations
              WHERE latitude IS NOT NULL \
                AND longitude IS NOT NULL
              ORDER BY distance_km ASC LIMIT ?; \
              """
        cursor.execute(sql, (user_lat, user_lng, limit))
        results = cursor.fetchall()

        # 转为标准的字典列表返回，方便后续转 JSON 扔给大模型
        return [dict(row) for row in results]



if __name__ == "__main__":
    print(asyncio.run(get_user_coordinates(user_input=None, user_ip="123,120,109,232")))
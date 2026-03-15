import math


def bd09mc_to_bd09(lng: float, lat: float) -> tuple[float, float]:
    """
    [工具函数] 百度墨卡托坐标 (BD09MC) 转 百度经纬度 (BD09)
    百度地图 IP 定位 API 返回的是墨卡托坐标，导航 API 需要经纬度，因此必须转换。
    来源：https://github.com/wandergis/coordTransform_py/blob/master/coordTransform_utils.py
    """
    x = lng
    y = lat

    # 1. 简单校验：如果坐标值过小，视为无效坐标（通常在中国境外或解析错误）
    if abs(y) < 1e-6 or abs(x) < 1e-6:
        return (0.0, 0.0)

    # 2. 核心算法：墨卡托平面坐标转球面经纬度
    lng = x / 20037508.34 * 180
    lat = y / 20037508.34 * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)

    return (lng, lat)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    使用 Haversine 公式计算两个经纬度点之间的球面距离
    :return: 距离，单位为千米 (km)
    """
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')  # 如果缺少坐标，放到最后面

    R = 6371.0  # 地球平均半径，单位公里

    # 将经纬度转换为弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # 经纬度差值
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Haversine 公式
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
"""
GPS 定位 + 离线地图模块
纯本地运行，零API、零联网

功能：
1. GPSModule — 获取经纬度（Android真实GPS / Windows模拟数据）
2. OfflineGeocoder — 离线地址逆解析（内置地名库）
3. OfflineMap — 生成静态离线地图图片
"""

import os
import math
import struct
import time
from datetime import datetime

# ==================== 内置离线地名库 ====================
# 格式: (名称, 纬度, 经度, 行政区划级别)
# 用于离线地址逆解析，零API、零联网
_BUILTIN_PLACES = [
    # === 直辖市 ===
    ('北京市',         39.9042,  116.4074, '直辖市'),
    ('上海市',         31.2304,  121.4737, '直辖市'),
    ('天津市',         39.3434,  117.3616, '直辖市'),
    ('重庆市',         29.4316,  106.9123, '直辖市'),

    # === 广东省 ===
    ('广州市',         23.1291,  113.2644, '省会'),
    ('深圳市',         22.5431,  114.0579, '城市'),
    ('东莞市',         23.0208,  113.7518, '城市'),
    ('佛山市',         23.0219,  113.1219, '城市'),
    ('珠海市',         22.2710,  113.5767, '城市'),
    ('中山市',         22.5470,  113.3926, '城市'),
    ('惠州市',         23.1117,  114.4158, '城市'),

    # === 浙江省 ===
    ('杭州市',         30.2741,  120.1551, '省会'),
    ('宁波市',         29.8683,  121.5440, '城市'),
    ('温州市',         27.9939,  120.6994, '城市'),
    ('义乌市',         29.3061,  120.0750, '城市'),

    # === 江苏省 ===
    ('南京市',         32.0603,  118.7969, '省会'),
    ('苏州市',         31.2990,  120.5853, '城市'),
    ('无锡市',         31.4912,  120.3119, '城市'),

    # === 四川省 ===
    ('成都市',         30.5728,  104.0668, '省会'),
    ('绵阳市',         31.4675,  104.6791, '城市'),

    # === 湖北省 ===
    ('武汉市',         30.5928,  114.3055, '省会'),

    # === 湖南省 ===
    ('长沙市',         28.2282,  112.9388, '省会'),

    # === 福建省 ===
    ('福州市',         26.0745,  119.2965, '省会'),
    ('厦门市',         24.4798,  118.0894, '城市'),

    # === 山东省 ===
    ('济南市',         36.6512,  116.9972, '省会'),
    ('青岛市',         36.0671,  120.3826, '城市'),

    # === 其他重要城市 ===
    ('西安市',         34.3416,  108.9398, '省会'),
    ('郑州市',         34.7466,  113.6253, '省会'),
    ('合肥市',         31.8206,  117.2272, '省会'),
    ('南昌市',         28.6829,  115.8582, '省会'),
    ('南宁市',         22.8170,  108.3665, '省会'),
    ('海口市',         20.0440,  110.3498, '省会'),
    ('贵阳市',         26.6470,  106.6302, '省会'),
    ('昆明市',         25.0389,  102.7183, '省会'),
    ('兰州市',         36.0642,  103.8343, '省会'),
    ('太原市',         37.8706,  112.5489, '省会'),
    ('石家庄市',       38.0428,  114.5149, '省会'),
    ('哈尔滨市',       45.8038,  126.5350, '省会'),
    ('长春市',         43.8161,  125.3235, '省会'),
    ('沈阳市',         41.8057,  123.4315, '省会'),
    ('呼和浩特市',     40.8422,  111.7499, '省会'),
    ('乌鲁木齐市',     43.8266,   87.6169, '省会'),
    ('拉萨市',         29.6525,   91.1719, '省会'),
    ('西宁市',         36.6171,  101.7782, '省会'),
    ('银川市',         38.4872,  106.2310, '省会'),

    # === 知名区县 ===
    ('浦东新区',       31.2213,  121.5440, '区'),
    ('朝阳区',         39.9219,  116.4435, '区'),
    ('海淀区',         39.9561,  116.3103, '区'),
    ('天河区',         23.1260,  113.3613, '区'),
    ('南山区',         22.5328,  113.9303, '区'),
    ('福田区',         22.5214,  114.0550, '区'),

    # === 常见乡镇街道（示例） ===
    ('人民路街道',     31.2304,  121.4737, '街道'),
    ('解放路街道',     30.5928,  114.3055, '街道'),
    ('建设大道',       30.5728,  104.0668, '道路'),
    ('中山路',         39.9042,  116.4074, '道路'),
    ('南京路',         31.2304,  121.4737, '道路'),
    ('王府井大街',     39.9124,  116.4103, '道路'),
    ('陆家嘴',         31.2402,  121.5066, '商圈'),
    ('中关村',         39.9825,  116.3110, '商圈'),
]


class GPSModule:
    """GPS定位模块
    跨平台：Android上用plyer获取真实GPS，Windows上用模拟数据
    """

    def __init__(self):
        self._latitude = None
        self._longitude = None
        self._altitude = 0.0
        self._accuracy = 0.0
        self._is_running = False
        self._simulated = False
        self._last_update = None

        # 检测平台
        self._platform = self._detect_platform()

    def _detect_platform(self):
        """检测运行平台"""
        try:
            from kivy.utils import platform
            return platform
        except ImportError:
            return 'win'

    def start_gps(self):
        """启动GPS定位

        在Android上启动真实的GPS监听。
        在Windows上使用模拟数据（开发调试用）。
        """
        if self._is_running:
            return True

        if self._platform == 'android':
            try:
                from plyer import gps
                gps.configure(on_location=self._on_location,
                              on_status=self._on_status)
                gps.start(minTime=1000, minDistance=1)
                self._is_running = True
                return True
            except Exception as e:
                print(f"[GPSModule] Android GPS启动失败: {e}")
                print("[GPSModule] 回退到模拟数据模式")
                self._simulated = True
                self._is_running = True
                return True
        else:
            # Windows开发环境：使用模拟数据
            print("[GPSModule] Windows开发模式：使用模拟GPS数据")
            self._simulated = True
            self._is_running = True
            # 默认模拟位置（广州市中心）
            self._latitude = 23.1291
            self._longitude = 113.2644
            self._accuracy = 100.0
            self._last_update = datetime.now()
            return True

    def stop_gps(self):
        """停止GPS定位"""
        if self._platform == 'android' and not self._simulated:
            try:
                from plyer import gps
                gps.stop()
            except Exception:
                pass
        self._is_running = False

    def _on_location(self, **kwargs):
        """Android GPS位置回调"""
        self._latitude = kwargs.get('lat', self._latitude)
        self._longitude = kwargs.get('lon', self._longitude)
        self._altitude = kwargs.get('altitude', 0.0)
        self._accuracy = kwargs.get('accuracy', 0.0)
        self._last_update = datetime.now()

    def _on_status(self, stype, status):
        """Android GPS状态回调"""
        pass

    def get_location(self):
        """获取当前位置

        返回:
            dict: {
                'success': True/False,
                'latitude': float,
                'longitude': float,
                'altitude': float,
                'accuracy': float (米),
                'is_simulated': bool,
                'timestamp': str,
                'error': str (失败时)
            }
        """
        result = {
            'success': False,
            'latitude': 0.0,
            'longitude': 0.0,
            'altitude': 0.0,
            'accuracy': 0.0,
            'is_simulated': self._simulated,
            'timestamp': '',
            'error': '',
        }

        if not self._is_running:
            # 自动启动
            if not self.start_gps():
                result['error'] = 'GPS启动失败'
                return result

        if self._simulated:
            # 模拟数据：返回默认位置
            result['success'] = True
            result['latitude'] = self._latitude
            result['longitude'] = self._longitude
            result['accuracy'] = self._accuracy
            result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result['is_simulated'] = True
            return result

        if self._platform == 'android':
            # Android：返回最后一次获取的真实位置
            if self._latitude is not None:
                result['success'] = True
                result['latitude'] = self._latitude
                result['longitude'] = self._longitude
                result['altitude'] = self._altitude
                result['accuracy'] = self._accuracy
                result['timestamp'] = (
                    self._last_update.strftime('%Y-%m-%d %H:%M:%S')
                    if self._last_update else ''
                )
            else:
                result['error'] = 'GPS定位中，请稍候...'
            return result

        result['error'] = '不支持的平台'
        return result

    def get_location_string(self):
        """获取格式化的位置字符串"""
        loc = self.get_location()
        if loc['success']:
            lat = loc['latitude']
            lng = loc['longitude']
            # 转换度为度分秒格式
            lat_dir = 'N' if lat >= 0 else 'S'
            lng_dir = 'E' if lng >= 0 else 'W'
            lat_abs = abs(lat)
            lng_abs = abs(lng)
            lat_deg = int(lat_abs)
            lat_min = (lat_abs - lat_deg) * 60
            lng_deg = int(lng_abs)
            lng_min = (lng_abs - lng_deg) * 60

            sim_tag = ' [模拟]' if loc['is_simulated'] else ''
            return (
                f'{lat_deg}°{lat_min:.2f}\'{lat_dir}  '
                f'{lng_deg}°{lng_min:.2f}\'{lng_dir}'
                f'{sim_tag}'
            )
        return f'定位失败: {loc["error"]}'

    def get_coordinates(self):
        """获取经纬度元组"""
        loc = self.get_location()
        if loc['success']:
            return (loc['latitude'], loc['longitude'])
        return (None, None)


class OfflineGeocoder:
    """离线地址逆解析
    使用内置地名库，不调用任何地图API
    """

    def __init__(self):
        self._places = _BUILTIN_PLACES

    def reverse_geocode(self, latitude, longitude):
        """经纬度→地址逆解析（纯离线）

        使用最近邻匹配，返回最近的地名

        参数:
            latitude: 纬度
            longitude: 经度

        返回:
            dict: {
                'success': True/False,
                'name': '匹配到的地名',
                'level': '行政区划级别',
                'distance_km': 距离（公里）,
                'all_matches': [(name, level, dist_km), ...],
                'error': str
            }
        """
        result = {
            'success': False,
            'name': '未知位置',
            'level': '',
            'distance_km': 0.0,
            'all_matches': [],
            'error': '',
        }

        if latitude is None or longitude is None:
            result['error'] = '无效的经纬度'
            return result

        # 计算所有地名的距离
        matches = []
        for name, lat, lng, level in self._places:
            dist = self._haversine(latitude, longitude, lat, lng)
            matches.append((name, level, dist, lat, lng))

        # 按距离排序
        matches.sort(key=lambda x: x[2])

        if not matches:
            result['error'] = '未找到匹配地名'
            return result

        # 取最近的地名
        best = matches[0]
        result['success'] = True
        result['name'] = best[0]
        result['level'] = best[1]
        result['distance_km'] = round(best[2], 2)
        result['all_matches'] = [
            (m[0], m[1], round(m[2], 2)) for m in matches[:10]
        ]

        return result

    def _haversine(self, lat1, lon1, lat2, lon2):
        """计算两点之间的球面距离（公里）

        使用Haversine公式，纯数学计算，零API
        """
        R = 6371.0  # 地球平均半径（公里）

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    def search_places(self, keyword, max_results=10):
        """搜索地名

        参数:
            keyword: 搜索关键词
            max_results: 最大返回数量

        返回:
            [(name, level, lat, lng), ...]
        """
        results = []
        keyword = keyword.lower()
        for name, lat, lng, level in self._places:
            if keyword in name.lower():
                results.append((name, level, lat, lng))
        return results[:max_results]


class OfflineMap:
    """离线静态地图生成器
    使用Pillow绘制坐标网格地图，标记当前位置
    不调用任何在线地图服务
    """

    # 地图样式配置
    MAP_COLORS = {
        'background': (240, 240, 240),    # 浅灰背景
        'grid':       (200, 200, 200),     # 网格线
        'land':       (230, 240, 230),     # 陆地色
        'water':      (200, 220, 240),     # 水域色
        'marker':     (220, 50, 50),       # 位置标记
        'marker_ring': (220, 50, 50, 80),  # 标记光环
        'text':       (50, 50, 50),        # 文字颜色
        'border':     (150, 150, 150),     # 边框
        'compass':    (80, 80, 80),        # 指北针
    }

    def __init__(self, map_dir=None):
        """初始化

        参数:
            map_dir: 地图图片保存目录（默认 data/maps）
        """
        if map_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            map_dir = os.path.join(base, 'data', 'maps')
        self.map_dir = map_dir
        os.makedirs(self.map_dir, exist_ok=True)

    def generate_map(self, latitude, longitude, zoom=14,
                     width=600, height=400, filename=None):
        """生成离线静态地图图片

        使用Pillow绘制坐标网格+位置标记

        参数:
            latitude: 中心纬度
            longitude: 中心经度
            zoom: 缩放级别 (1-18, 越大越精细)
            width: 图片宽度（像素）
            height: 图片高度（像素）
            filename: 输出文件名（不含路径）

        返回:
            dict: {
                'success': True/False,
                'filepath': str (图片完整路径),
                'error': str
            }
        """
        result = {
            'success': False,
            'filepath': '',
            'error': '',
        }

        try:
            from PIL import Image, ImageDraw, ImageFont

            # 创建画布
            img = Image.new('RGBA', (width, height),
                            self.MAP_COLORS['background'])
            draw = ImageDraw.Draw(img)

            # 计算地图范围
            # 每度经纬度对应的像素
            meters_per_deg_lat = 111320.0
            meters_per_deg_lon = 111320.0 * math.cos(
                math.radians(latitude)
            )

            # 根据zoom计算分辨率
            base_resolution = 156543.0  # zoom=1时的分辨率（米/像素）
            resolution = base_resolution / (2 ** zoom)

            # 地图覆盖范围（度）
            half_width_deg = (width / 2) * resolution / meters_per_deg_lon
            half_height_deg = (height / 2) * resolution / meters_per_deg_lat

            min_lat = latitude - half_height_deg
            max_lat = latitude + half_height_deg
            min_lng = longitude - half_width_deg
            max_lng = longitude + half_width_deg

            # ---- 1. 绘制网格 ----
            # 计算网格间距
            grid_spacing = self._calc_grid_spacing(zoom)

            # 经线（垂直）
            lng_start = math.floor(min_lng / grid_spacing) * grid_spacing
            lng_val = lng_start
            while lng_val <= max_lng:
                x = int((lng_val - min_lng) / (max_lng - min_lng) * width)
                draw.line([(x, 0), (x, height)],
                          fill=self.MAP_COLORS['grid'], width=1)
                # 标注经度
                if zoom >= 10:
                    label = f'{abs(lng_val):.2f}°{"E" if lng_val >= 0 else "W"}'
                    draw.text((x + 3, height - 14), label,
                              fill=self.MAP_COLORS['text'])
                lng_val += grid_spacing

            # 纬线（水平）
            lat_start = math.floor(min_lat / grid_spacing) * grid_spacing
            lat_val = lat_start
            while lat_val <= max_lat:
                y = int((max_lat - lat_val) / (max_lat - min_lat) * height)
                draw.line([(0, y), (width, y)],
                          fill=self.MAP_COLORS['grid'], width=1)
                # 标注纬度
                if zoom >= 10:
                    label = f'{abs(lat_val):.2f}°{"N" if lat_val >= 0 else "S"}'
                    draw.text((3, y - 12), label,
                              fill=self.MAP_COLORS['text'])
                lat_val += grid_spacing

            # ---- 2. 绘制指北针 ----
            compass_x, compass_y = width - 50, 50
            # 北箭头
            draw.polygon([
                (compass_x, compass_y - 20),
                (compass_x - 8, compass_y),
                (compass_x + 8, compass_y)
            ], fill=self.MAP_COLORS['compass'])
            draw.text((compass_x - 4, compass_y - 32), 'N',
                      fill=self.MAP_COLORS['compass'])

            # ---- 3. 绘制比例尺 ----
            scale_y = height - 30
            scale_x = 20
            scale_width = 100
            # 计算比例尺代表的距离
            scale_m = scale_width * resolution
            if scale_m > 1000:
                scale_label = f'{scale_m / 1000:.1f}km'
            else:
                scale_label = f'{scale_m:.0f}m'

            draw.rectangle([(scale_x, scale_y),
                           (scale_x + scale_width, scale_y + 4)],
                          fill=self.MAP_COLORS['border'])
            draw.rectangle([(scale_x, scale_y),
                           (scale_x + scale_width // 2, scale_y + 4)],
                          fill=self.MAP_COLORS['text'])
            draw.text((scale_x, scale_y - 14), scale_label,
                      fill=self.MAP_COLORS['text'])

            # ---- 4. 绘制当前位置标记 ----
            # 计算中心点在画布上的坐标
            cx = width // 2
            cy = height // 2

            # 外圈光环
            for r in range(30, 10, -5):
                alpha = int(80 * (1 - r / 30))
                ring_color = (220, 50, 50, alpha)
                draw.ellipse(
                    [(cx - r, cy - r), (cx + r, cy + r)],
                    outline=ring_color, width=2
                )

            # 标记点
            draw.ellipse(
                [(cx - 8, cy - 8), (cx + 8, cy + 8)],
                fill=self.MAP_COLORS['marker']
            )
            draw.ellipse(
                [(cx - 3, cy - 3), (cx + 3, cy + 3)],
                fill=(255, 255, 255)
            )

            # ---- 5. 绘制坐标信息 ----
            info_text = (
                f'中心: {latitude:.4f}°N, {longitude:.4f}°E\n'
                f'缩放: {zoom} | 分辨率: {resolution:.1f}m/px'
            )
            draw.text((10, 10), info_text,
                      fill=self.MAP_COLORS['text'])

            # ---- 6. 绘制边框 ----
            draw.rectangle([(0, 0), (width - 1, height - 1)],
                          outline=self.MAP_COLORS['border'], width=2)

            # ---- 保存图片 ----
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'map_{latitude:.3f}_{longitude:.3f}_{timestamp}.png'

            filepath = os.path.join(self.map_dir, filename)
            img.save(filepath, 'PNG')

            result['success'] = True
            result['filepath'] = filepath

        except ImportError:
            result['error'] = 'Pillow库不可用，无法生成地图'
        except Exception as e:
            result['error'] = f'地图生成失败: {str(e)}'

        return result

    def _calc_grid_spacing(self, zoom):
        """根据缩放级别计算网格间距（度）"""
        if zoom >= 16:
            return 0.001
        elif zoom >= 14:
            return 0.005
        elif zoom >= 12:
            return 0.01
        elif zoom >= 10:
            return 0.05
        elif zoom >= 8:
            return 0.1
        elif zoom >= 6:
            return 0.5
        else:
            return 1.0

    def get_last_map_path(self):
        """获取最新生成的地图图片路径"""
        if not os.path.exists(self.map_dir):
            return None
        files = [f for f in os.listdir(self.map_dir)
                 if f.startswith('map_') and f.endswith('.png')]
        if not files:
            return None
        files.sort(reverse=True)
        return os.path.join(self.map_dir, files[0])

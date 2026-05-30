"""
配置模块 - 颜色主题、字体、全局常量
零API、零联网，纯本地配置
"""

from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp

# ========== 应用信息 ==========
APP_NAME = "综合政务管理"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "纯本地离线政务管理APP"

# ========== 颜色方案 ==========
# 使用 get_color_from_hex 将十六进制颜色转为Kivy RGBA列表
COLORS = {
    # 主色调
    'primary':       get_color_from_hex('#2E7D32'),   # 深绿
    'primary_light': get_color_from_hex('#4CAF50'),   # 亮绿
    'primary_dark':  get_color_from_hex('#1B5E20'),   # 暗绿
    'secondary':     get_color_from_hex('#1565C0'),   # 深蓝

    # 基础色
    'background':    get_color_from_hex('#F5F5F5'),   # 背景灰
    'surface':       get_color_from_hex('#FFFFFF'),   # 卡片白
    'text_primary':  get_color_from_hex('#212121'),   # 主文字
    'text_secondary':get_color_from_hex('#757575'),   # 次要文字
    'divider':       get_color_from_hex('#E0E0E0'),   # 分割线
    'disabled':      get_color_from_hex('#BDBDBD'),   # 禁用色

    # Toast 状态色
    'success':       get_color_from_hex('#4CAF50'),   # 成功绿
    'error':         get_color_from_hex('#F44336'),   # 错误红
    'warning':       get_color_from_hex('#FF9800'),   # 警告橙
    'info':          get_color_from_hex('#2196F3'),   # 信息蓝

    # 导航栏
    'nav_active':    get_color_from_hex('#2E7D32'),   # 导航选中
    'nav_inactive':  get_color_from_hex('#9E9E9E'),   # 导航未选中
    'nav_bg':        get_color_from_hex('#FFFFFF'),   # 导航栏背景
    'nav_border':    get_color_from_hex('#E0E0E0'),   # 导航栏分隔线

    # 统计卡片色
    'card_total':    get_color_from_hex('#1565C0'),   # 总件数蓝
    'card_done':     get_color_from_hex('#2E7D32'),   # 已完成绿
    'card_processing': get_color_from_hex('#FF9800'), # 处理中橙
    'card_urgent':   get_color_from_hex('#F44336'),   # 紧急红
}

# ========== 字体大小 ==========
FONT_SIZES = {
    'xs':       sp(10),
    'small':    sp(12),
    'body':     sp(14),
    'medium':   sp(16),
    'large':    sp(18),
    'title':    sp(20),
    'header':   sp(24),
    'app_title':sp(28),
}

# ========== 底部导航栏Tab定义 ==========
# id: 对应Screen的name和switch_tab的标识
# label: 显示文字
# icon: 使用Unicode字符/Emoji作为图标（零外部资源）
NAV_TABS = [
    {'id': 'home',      'label': '首页',      'icon': '🏠'},
    {'id': 'hazard',    'label': '隐患上报',  'icon': '⚠️'},
    {'id': 'case',      'label': '案件采集',  'icon': '📋'},
    {'id': 'ad',        'label': '店招申请',  'icon': '📝'},
    {'id': 'law',       'label': '法条查询',  'icon': '⚖️'},
    {'id': 'complaint', 'label': '投诉管理',  'icon': '📢'},
]

# ========== 页面标题 ==========
PAGE_TITLES = {
    'home':      '首页仪表盘',
    'hazard':    '隐患上报',
    'case':      '案件采集',
    'ad':        '店招申请',
    'law':       '法条查询',
    'complaint': '投诉管理',
}

# ========== 布局常量 ==========
NAV_HEIGHT = dp(64)          # 底部导航栏高度
TOOLBAR_HEIGHT = dp(56)      # 顶部标题栏高度
CARD_PADDING = dp(16)        # 卡片内边距
SCREEN_PADDING = dp(12)      # 页面边距
CORNER_RADIUS = dp(8)        # 圆角大小

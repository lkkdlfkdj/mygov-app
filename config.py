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

# ========== 高级配色方案 ==========
# 深林绿(Teal-Green)为主色，暖金色为辅色，暖灰为背景
# 整体调性：沉稳、精致、政府公务级别
COLORS = {
    # 主色调
    'primary':          get_color_from_hex('#1A5C4A'),   # 深林绿
    'primary_light':    get_color_from_hex('#2D8A6E'),   # 亮绿
    'primary_dark':     get_color_from_hex('#0E3D2F'),   # 暗绿
    'accent':           get_color_from_hex('#C48A3C'),   # 暖金色（点缀、选中态）

    # 基础色
    'background':       get_color_from_hex('#F3F2F0'),   # 暖灰背景
    'surface':          get_color_from_hex('#FFFFFF'),   # 卡片白
    'surface_elevated': get_color_from_hex('#FAFAF8'),   # 轻微浮雕面
    'text_primary':     get_color_from_hex('#1E1D1B'),   # 近黑主文字
    'text_secondary':   get_color_from_hex('#7A7874'),   # 暖灰次要文字
    'text_tertiary':    get_color_from_hex('#A5A39E'),   # 辅助信息文字
    'divider':          get_color_from_hex('#E5E3DE'),   # 暖灰分割线
    'disabled':         get_color_from_hex('#C4C2BC'),   # 禁用色

    # Toast 状态色（降低饱和度，更柔和稳重）
    'success':          get_color_from_hex('#2B7A50'),
    'error':            get_color_from_hex('#C2423B'),
    'warning':          get_color_from_hex('#C4882B'),
    'info':             get_color_from_hex('#2B6B9E'),

    # 导航栏
    'nav_active':       get_color_from_hex('#1A5C4A'),
    'nav_inactive':     get_color_from_hex('#A5A39E'),
    'nav_bg':           get_color_from_hex('#FFFFFF'),
    'nav_border':       get_color_from_hex('#E8E6E2'),

    # 统计卡片色（降低饱和度，保持稳重）
    'card_total':       get_color_from_hex('#1B3A5C'),   # 深蓝
    'card_done':        get_color_from_hex('#1A5C4A'),   # 深绿
    'card_processing':  get_color_from_hex('#B8732E'),   # 暖橙
    'card_urgent':      get_color_from_hex('#B53B35'),   # 深红

    # 工具栏渐变辅助色
    'toolbar_start':    get_color_from_hex('#1A5C4A'),
    'toolbar_end':      get_color_from_hex('#145243'),
}

# ========== 字体大小体系 ==========
# 层级清晰：caption -> small -> body -> medium -> large -> title -> header
FONT_SIZES = {
    'caption':   sp(10),
    'small':     sp(12),
    'body':      sp(14),
    'medium':    sp(16),
    'large':     sp(18),
    'title':     sp(20),
    'header':    sp(24),
    'app_title': sp(28),
}

# ========== 间距体系 ==========
SPACING = {
    'xs':   dp(2),
    'sm':   dp(4),
    'md':   dp(8),
    'lg':   dp(12),
    'xl':   dp(16),
    'xxl':  dp(20),
    'section': dp(24),
}

# ========== 圆角体系 ==========
RADIUS = {
    'sm':   dp(4),
    'md':   dp(8),
    'lg':   dp(12),
    'card': dp(10),
    'pill': dp(20),
}

# ========== 阴影效果（Kivy canvas 模拟）==========
# 用 rgba 半透明色模拟层次阴影
SHADOWS = {
    'card':         [0, 0, 0, 0.06],
    'card_hover':   [0, 0, 0, 0.10],
    'toolbar':      [0, 0, 0, 0.08],
    'nav_bar':      [0, 0, 0, 0.10],
    'popup':        [0, 0, 0, 0.18],
}

# ========== 底部导航栏Tab定义 ==========
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
NAV_HEIGHT = dp(64)
TOOLBAR_HEIGHT = dp(56)
CARD_PADDING = dp(16)
SCREEN_PADDING = dp(12)
CORNER_RADIUS = dp(8)

"""
底部导航栏组件 NavBar
- 6个Tab：首页、隐患上报、案件采集、店招申请、法条查询、投诉管理
- Unicode图标 + 文字标签
- 选中高亮效果（绿色高亮，灰色未选中）
- 点击切换页面
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp

from config import COLORS, NAV_TABS


class TabButton(ButtonBehavior, BoxLayout):
    """单个底部导航Tab按钮
    组合 ButtonBehavior（点击响应）+ BoxLayout（垂直布局）
    结构：图标(Emoji) + 文字标签
    """

    tab_id = StringProperty('')
    """Tab唯一标识，对应NAV_TABS中的id"""

    is_active = BooleanProperty(False)
    """是否选中状态"""

    def __init__(self, tab_id, label_text, icon_text,
                 on_press_callback, **kwargs):
        super().__init__(
            orientation='vertical',
            padding=[0, dp(4), 0, dp(2)],
            spacing=dp(1),
            **kwargs
        )
        self.tab_id = tab_id
        self.size_hint = (1.0 / len(NAV_TABS), 1.0)
        self.callback = on_press_callback
        self._active = False

        # ---- 图标层 ----
        self.icon_label = Label(
            text=icon_text,
            font_size=sp(22),
            size_hint=(1.0, 0.55),
            halign='center',
            valign='middle',
            text_size=(self.width, None),
        )
        self.add_widget(self.icon_label)

        # ---- 文字层 ----
        self.text_label = Label(
            text=label_text,
            font_size=sp(10),
            size_hint=(1.0, 0.45),
            halign='center',
            valign='middle',
            shorten=True,
            shorten_from='right',
            text_size=(self.width, None),
        )
        self.add_widget(self.text_label)

        # 初始状态设为未选中
        self._apply_colors()

    def on_press(self):
        """ButtonBehavior 的点击回调"""
        if self.callback:
            self.callback(self.tab_id)

    def set_active(self, active):
        """设置选中状态并更新颜色"""
        self._active = active
        self._apply_colors()

    def _apply_colors(self):
        """根据选中状态更新文字颜色"""
        if self._active:
            c = COLORS['nav_active']
            self.text_label.bold = True
        else:
            c = COLORS['nav_inactive']
            self.text_label.bold = False
        self.icon_label.color = c
        self.text_label.color = c


class NavBar(BoxLayout):
    """底部导航栏容器
    水平排列6个TabButton，固定在屏幕底部
    """

    def __init__(self, on_tab_switch, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint=(1.0, None),
            height=dp(64),
            spacing=0,
            padding=[0, 0, 0, 0],
            **kwargs
        )
        self.on_tab_switch = on_tab_switch
        self.buttons = []

        # ---- 绘制背景和顶部分隔线 ----
        with self.canvas.before:
            # 顶部分隔线（1dp高，灰色）
            Color(*COLORS['nav_border'])
            self.border_line = Rectangle(
                pos=self.pos,
                size=(self.width, dp(1))
            )
            # 背景色
            Color(*COLORS['nav_bg'])
            self.bg_rect = Rectangle(
                pos=(self.x, self.y + dp(1)),
                size=(self.width, self.height - dp(1))
            )

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # ---- 创建Tab按钮 ----
        for tab in NAV_TABS:
            btn = TabButton(
                tab_id=tab['id'],
                label_text=tab['label'],
                icon_text=tab['icon'],
                on_press_callback=self._on_tab_pressed,
            )
            self.buttons.append(btn)
            self.add_widget(btn)

    def _update_canvas(self, *args):
        """当位置或尺寸变化时更新canvas绘制"""
        self.border_line.pos = self.pos
        self.border_line.size = (self.width, dp(1))
        self.bg_rect.pos = (self.x, self.y + dp(1))
        self.bg_rect.size = (self.width, self.height - dp(1))

    def _on_tab_pressed(self, tab_id):
        """Tab按钮点击后的统一处理"""
        self.set_active(tab_id)
        if self.on_tab_switch:
            self.on_tab_switch(tab_id)

    def set_active(self, tab_id):
        """设置当前选中的Tab"""
        for btn in self.buttons:
            btn.set_active(btn.tab_id == tab_id)

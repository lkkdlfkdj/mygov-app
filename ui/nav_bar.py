"""
底部导航栏组件 NavBar
- 6个Tab：首页、隐患上报、案件采集、店招申请、法条查询、投诉管理
- Unicode图标 + 文字标签
- 选中高亮：深林绿 + 顶部微光条
- 点击切换页面
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation

from config import COLORS, NAV_TABS, SHADOWS


class TabButton(ButtonBehavior, BoxLayout):
    """单个底部导航Tab按钮
    选中时：文字 bold + 主色 + 顶部小圆点指示器
    """

    tab_id = StringProperty('')
    is_active = BooleanProperty(False)

    def __init__(self, tab_id, label_text, icon_text,
                 on_press_callback, **kwargs):
        super().__init__(
            orientation='vertical',
            padding=[0, dp(6), 0, dp(2)],
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
        )
        self.add_widget(self.text_label)

        # ---- 选中指示器（顶部小圆点） ----
        with self.canvas.after:
            self.indicator_color = Color(*COLORS['primary'], a=0)
            self.indicator = RoundedRectangle(
                pos=(self.center_x - dp(3), self.y + self.height - dp(4)),
                size=(dp(6), dp(6)),
                radius=[dp(3)]*4,
            )

        self.bind(pos=self._update_indicator, size=self._update_indicator)
        self._apply_colors()

    def on_press(self):
        if self.callback:
            self.callback(self.tab_id)

    def set_active(self, active):
        self._active = active
        self._apply_colors()

    def _apply_colors(self):
        if self._active:
            c = COLORS['nav_active']
            self.text_label.bold = True
            self.icon_label.color = c
            self.text_label.color = c
            Animation.stop_all(self.indicator_color, 'a')
            Animation(a=1.0, duration=0.2, t='out_quad').start(self.indicator_color)
        else:
            c = COLORS['nav_inactive']
            self.text_label.bold = False
            self.icon_label.color = c
            self.text_label.color = c
            Animation.stop_all(self.indicator_color, 'a')
            Animation(a=0.0, duration=0.15).start(self.indicator_color)

    def _update_indicator(self, *args):
        self.indicator.pos = (self.center_x - dp(3),
                              self.y + self.height - dp(4))
        self.indicator.size = (dp(6), dp(6))


class NavBar(BoxLayout):
    """底部导航栏容器"""

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

        # ---- 绘制顶部阴影线 + 白色背景 ----
        with self.canvas.before:
            Color(*SHADOWS['nav_bar'])
            self.shadow_line = Rectangle(
                pos=self.pos,
                size=(self.width, dp(3))
            )
            Color(*COLORS['nav_bg'])
            self.bg_rect = Rectangle(
                pos=(self.x, self.y + dp(3)),
                size=(self.width, self.height - dp(3))
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
        self.shadow_line.pos = self.pos
        self.shadow_line.size = (self.width, dp(3))
        self.bg_rect.pos = (self.x, self.y + dp(3))
        self.bg_rect.size = (self.width, self.height - dp(3))

    def _on_tab_pressed(self, tab_id):
        self.set_active(tab_id)
        if self.on_tab_switch:
            self.on_tab_switch(tab_id)

    def set_active(self, tab_id):
        for btn in self.buttons:
            btn.set_active(btn.tab_id == tab_id)

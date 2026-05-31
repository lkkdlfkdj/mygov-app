"""
全局通知组件 Toast
- 四种类型：success（绿）、error（红）、warning（黄）、info（蓝）
- 居中弹出，2秒自动消失
- 全APP通用调用方式：App.get_running_app().show_toast(message, type)
"""

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.metrics import dp, sp

from config import COLORS, SHADOWS

TOAST_COLORS = {
    'success': COLORS['success'],
    'error':   COLORS['error'],
    'warning': COLORS['warning'],
    'info':    COLORS['info'],
}


class ToastWidget(Widget):
    """浮动Toast通知组件"""

    _instance = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width = Window.width * 0.88
        self.height = dp(48)
        self.x = (Window.width - self.width) / 2
        self.y = Window.height * 0.85
        self.opacity = 0.0

        with self.canvas:
            self._bg_color = Color(*COLORS['info'], group='toast_bg')
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(6), dp(6), dp(6), dp(6)],
                group='toast_bg',
            )

        self.label = Label(
            text='',
            font_size=sp(14),
            color=[1, 1, 1, 1],
            halign='center',
            valign='middle',
            size_hint=(1, 1),
            pos=self.pos,
            size=self.size,
            shorten=True,
            text_size=(self.width - dp(24), self.height),
        )
        self.add_widget(self.label)

        Window.bind(size=self._on_window_resize)
        self.bind(pos=self._refresh_gfx, size=self._refresh_gfx)

    def _on_window_resize(self, instance, value):
        self.width = Window.width * 0.88
        self.x = (Window.width - self.width) / 2
        self.y = Window.height * 0.85

    def _refresh_gfx(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.label.pos = self.pos
        self.label.size = self.size
        self.label.text_size = (self.width - dp(24), self.height)

    def show(self, message, toast_type='info', duration=2.0):
        self.label.text = message

        color = TOAST_COLORS.get(toast_type, COLORS['info'])
        self._bg_color.rgba = (color[0], color[1], color[2], 0.95)

        Animation.cancel_all(self)
        Clock.unschedule(self._do_hide)

        self.opacity = 0.0

        anim_in = Animation(opacity=1.0, duration=0.2, t='out_cubic')
        Clock.schedule_once(lambda dt: self._do_hide(), duration)
        anim_in.start(self)

    def _do_hide(self):
        anim_out = Animation(opacity=0.0, duration=0.2, t='in_cubic')
        anim_out.start(self)

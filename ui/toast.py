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

from config import COLORS

# Toast类型与颜色的映射
TOAST_COLORS = {
    'success': COLORS['success'],
    'error':   COLORS['error'],
    'warning': COLORS['warning'],
    'info':    COLORS['info'],
}


class ToastWidget(Widget):
    """浮动Toast通知组件
    全局唯一实例，添加到Window最上层
    """

    _instance = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 固定大小和位置（屏幕中间偏上）
        self.size_hint = (None, None)
        self.width = Window.width * 0.88
        self.height = dp(52)
        self.x = (Window.width - self.width) / 2
        self.y = Window.height * 0.85
        self.opacity = 0.0

        # ---- 绘制圆角背景 ----
        self._bg_color = Color(*COLORS['info'], group='toast_bg')
        with self.canvas:
            self._bg_color = Color(*COLORS['info'], group='toast_bg')
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8), dp(8), dp(8), dp(8)],
                group='toast_bg',
            )

        # ---- 文字标签 ----
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
            shorten_from='right',
            text_size=(self.width - dp(20), self.height),
        )
        self.add_widget(self.label)

        # 监听Window尺寸变化
        Window.bind(size=self._on_window_resize)

        # 绑定自身位置/尺寸更新
        self.bind(pos=self._refresh_gfx, size=self._refresh_gfx)

    def _on_window_resize(self, instance, value):
        """窗口大小变化时重新定位"""
        self.width = Window.width * 0.88
        self.x = (Window.width - self.width) / 2
        self.y = Window.height * 0.85

    def _refresh_gfx(self, *args):
        """刷新图形绘制"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.label.pos = self.pos
        self.label.size = self.size
        self.label.text_size = (self.width - dp(20), self.height)

    def show(self, message, toast_type='info', duration=2.0):
        """显示Toast通知

        参数:
            message: 显示的文字消息
            toast_type: 类型 - 'success'/'error'/'warning'/'info'
            duration: 显示持续时间（秒），默认2秒
        """
        # 更新文字
        self.label.text = message

        # 更新背景颜色
        color = TOAST_COLORS.get(toast_type, COLORS['info'])
        self._bg_color.rgba = (color[0], color[1], color[2], 0.92)

        # 取消之前的动画和定时器
        Animation.cancel_all(self)
        Clock.unschedule(self._do_hide)

        # 重置透明度
        self.opacity = 0.0

        # 淡入动画
        anim_in = Animation(opacity=1.0, duration=0.25,
                            t='out_quad')
        # 定时后淡出
        Clock.schedule_once(
            lambda dt: self._do_hide(),
            duration
        )
        anim_in.start(self)

    def _do_hide(self):
        """执行淡出动画"""
        anim_out = Animation(opacity=0.0, duration=0.25,
                             t='in_quad')
        anim_out.start(self)

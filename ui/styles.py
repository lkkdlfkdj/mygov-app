"""
统一样式工具模块
提供可复用的样式方法，确保全APP UI 一致性
"""

from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.animation import Animation

from config import COLORS, FONT_SIZES, SPACING, RADIUS, SHADOWS


def draw_rounded_bg(widget, color=COLORS['surface'], radius=RADIUS['card']):
    """给任意 widget 添加圆角背景"""
    with widget.canvas.before:
        Color(*color)
        RoundedRectangle(
            pos=widget.pos,
            size=widget.size,
            radius=[radius]*4,
        )

    def update(*args):
        widget.canvas.before.clear()
        with widget.canvas.before:
            Color(*color)
            RoundedRectangle(
                pos=widget.pos,
                size=widget.size,
                radius=[radius]*4,
            )

    widget.bind(pos=update, size=update)
    return update


def draw_shadow(widget, shadow_rgba=SHADOWS['card'], offset_y=dp(2), radius=RADIUS['card']):
    """在 widget canvas.before 中绘制阴影矩形（在圆角背景之前）"""
    shadow_color = list(shadow_rgba)

    def update(*args):
        widget.canvas.before.clear()
        Color(*shadow_color)
        RoundedRectangle(
            pos=(widget.x, widget.y - offset_y),
            size=(widget.width, widget.height + offset_y),
            radius=[radius]*4,
        )

    widget.bind(pos=update, size=update)
    return update


def card_box(**kwargs):
    """创建一个带圆角+浅阴影的卡片容器"""
    box = BoxLayout(**kwargs)
    draw_rounded_bg(box, COLORS['surface'])
    draw_shadow(box)
    return box


def section_title(text, **kwargs):
    """统一的段落标题 Label"""
    return Label(
        text=text,
        font_size=FONT_SIZES['medium'],
        color=COLORS['text_primary'],
        bold=True,
        size_hint=(1, None),
        height=dp(36),
        halign='left',
        valign='middle',
        text_size=(dp(400), None),
        **kwargs
    )


def field_label(text, **kwargs):
    """统一的字段名 Label"""
    return Label(
        text=text,
        font_size=FONT_SIZES['body'],
        color=COLORS['text_secondary'],
        size_hint=(1, None),
        height=dp(20),
        halign='left',
        valign='middle',
        **kwargs
    )


def value_label(**kwargs):
    """统一的字段值 Label"""
    return Label(
        font_size=FONT_SIZES['body'],
        color=COLORS['text_primary'],
        size_hint=(1, None),
        height=dp(28),
        halign='left',
        valign='top',
        **kwargs
    )


def primary_btn(text, on_press=None, **kwargs):
    """统一的主操作按钮"""
    kwargs.setdefault('size_hint', (1, None))
    kwargs.setdefault('height', dp(44))
    btn = Button(
        text=text,
        font_size=FONT_SIZES['body'],
        background_color=COLORS['primary'],
        background_normal='',
        color=[1, 1, 1, 1],
        **kwargs
    )

    def on_down(inst):
        Animation.stop_all(inst, 'opacity')
        Animation(opacity=0.8, duration=0.08, t='out_quad').start(inst)

    def on_up(inst):
        Animation.stop_all(inst, 'opacity')
        Animation(opacity=1.0, duration=0.1).start(inst)

    btn.bind(on_press=on_down)
    btn.bind(on_release=on_up)
    if on_press:
        btn.bind(on_press=on_press)
    return btn
    return btn


def secondary_btn(text, on_press=None, **kwargs):
    """次要按钮：描边风格"""
    kwargs.setdefault('size_hint', (1, None))
    kwargs.setdefault('height', dp(44))
    btn = Button(
        text=text,
        font_size=FONT_SIZES['body'],
        background_color=[1, 1, 1, 0],
        background_normal='',
        color=COLORS['primary'],
        **kwargs
    )
    if on_press:
        btn.bind(on_press=on_press)
    return btn


def create_field_row(label_text, value_widget):
    """字段行：标签在上，值在下"""
    row = BoxLayout(
        orientation='vertical',
        size_hint=(1, None),
        spacing=SPACING['xs'],
    )
    row.add_widget(field_label(label_text))
    row.add_widget(value_widget)
    return row


def toolbar_bg(toolbar_widget):
    """给 toolbar widget 添加渐变感背景（实色 + 底部阴影线）"""
    with toolbar_widget.canvas.before:
        Color(*COLORS['toolbar_start'])
        Rectangle(pos=toolbar_widget.pos, size=toolbar_widget.size)

    toolbar_widget.bind(pos=lambda i, v: _redraw_toolbar(i),
                        size=lambda i, v: _redraw_toolbar(i))


def _redraw_toolbar(toolbar):
    toolbar.canvas.before.clear()
    with toolbar.canvas.before:
        Color(*COLORS['toolbar_start'])
        Rectangle(pos=toolbar.pos, size=toolbar.size)

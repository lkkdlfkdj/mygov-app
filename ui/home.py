"""
首页仪表盘页面 HomeScreen
- 统计卡片：总投诉件数、已完成、处理中、紧急
- 最近投诉列表，点击弹窗查看详情
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT, SPACING, RADIUS, SHADOWS
from ui.styles import toolbar_bg, section_title


class StatCard(BoxLayout):
    """高级统计卡片：大数字 + 柔色底 + 圆角"""

    def __init__(self, title, value, card_color, **kwargs):
        super().__init__(
            orientation='vertical',
            size_hint=(0.5, None),
            height=dp(100),
            padding=[dp(14), dp(12), dp(14), dp(10)],
            spacing=dp(2),
            **kwargs
        )
        self.card_color = card_color

        with self.canvas.before:
            Color(*card_color)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10), dp(10), dp(10), dp(10)]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.value_label = Label(
            text=str(value),
            font_size=sp(30),
            color=[1, 1, 1, 1],
            bold=True,
            size_hint=(1, 0.58),
            halign='center',
            valign='middle',
        )
        self.add_widget(self.value_label)

        self.title_label = Label(
            text=title,
            font_size=sp(12),
            color=[1, 1, 1, 0.85],
            size_hint=(1, 0.42),
            halign='center',
            valign='middle',
        )
        self.add_widget(self.title_label)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class HomeScreen(Screen):
    """首页仪表盘"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        root = BoxLayout(orientation='vertical')

        # ---- 顶部标题栏 ----
        toolbar = BoxLayout(
            size_hint=(1, None),
            height=TOOLBAR_HEIGHT,
            padding=[dp(16), 0],
        )
        toolbar_bg(toolbar)

        title_label = Label(
            text=PAGE_TITLES['home'],
            font_size=FONT_SIZES['title'],
            color=[1, 1, 1, 1],
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 1),
        )
        toolbar.add_widget(title_label)

        self.count_label = Label(
            text='',
            font_size=sp(12),
            color=[1, 1, 1, 0.75],
            size_hint=(0.3, 1),
            halign='right',
            valign='middle',
        )
        toolbar.add_widget(self.count_label)
        root.add_widget(toolbar)

        # ---- 可滚动内容区 ----
        scroll = ScrollView()
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(12)],
            spacing=dp(14),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        # ---- 统计卡片网格 ----
        card_grid = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(210),
        )

        self.card_total = StatCard('总投诉件数', '0', COLORS['card_total'])
        self.card_done = StatCard('已完成', '0', COLORS['card_done'])
        self.card_processing = StatCard('处理中', '0', COLORS['card_processing'])
        self.card_urgent = StatCard('紧急(≤3天)', '0', COLORS['card_urgent'])

        card_grid.add_widget(self.card_total)
        card_grid.add_widget(self.card_done)
        card_grid.add_widget(self.card_processing)
        card_grid.add_widget(self.card_urgent)
        content.add_widget(card_grid)

        # ---- 最近投诉标题 ----
        sec_title = section_title('最近投诉')
        content.add_widget(sec_title)

        # ---- 最近投诉列表 ----
        self.recent_list = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=dp(8),
        )
        content.add_widget(self.recent_list)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

        Clock.schedule_once(lambda dt: self._load_data(), 0.2)

    def on_enter(self):
        self._load_data()

    def _load_data(self):
        from core.storage import Storage
        storage = Storage()

        stats = storage.get_complaint_stats()
        self.card_total.value_label.text = str(stats['total'])
        self.card_done.value_label.text = str(stats['done'])
        self.card_processing.value_label.text = str(stats['processing'])
        self.card_urgent.value_label.text = str(stats['urgent'])

        total = stats['total']
        hazards = len(storage.get_all_hazards())
        cases = len(storage.get_all_cases())
        laws = len(storage.get_all_laws())
        ads = len(storage.get_all_ads())
        all_count = total + hazards + cases + laws + ads
        self.count_label.text = f'共{all_count}条'

        complaints = storage.get_all_complaints()
        recent = complaints[:3]

        self.recent_list.clear_widgets()

        if not recent:
            placeholder = self._create_recent_item('暂无投诉数据', '—')
            self.recent_list.add_widget(placeholder)
            return

        for c in recent:
            item = self._create_recent_item(
                c.get('title', '无标题'),
                c.get('status', '待处理'),
                complaint=c,
            )
            self.recent_list.add_widget(item)

    def _create_recent_item(self, title, status, complaint=None):
        item = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(14), dp(8), dp(14), dp(8)],
            spacing=dp(10),
        )

        with item.canvas.before:
            Color(*SHADOWS['card'])
            RoundedRectangle(
                pos=(item.x, item.y),
                size=(item.size[0], item.size[1] + dp(2)),
                radius=[RADIUS['md']]*4,
            )
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=item.pos,
                size=item.size,
                radius=[RADIUS['md']]*4,
            )
        item.bind(pos=self._refresh_item_bg, size=self._refresh_item_bg)

        title_lbl = Label(
            text=title,
            font_size=sp(14),
            color=COLORS['text_primary'],
            size_hint=(0.68, 1),
            halign='left',
            valign='middle',
            bold=True,
            shorten=True,
        )

        status_lbl = Label(
            text=status,
            font_size=sp(12),
            color=COLORS['text_secondary'],
            size_hint=(0.32, 1),
            halign='right',
            valign='middle',
        )

        if complaint:
            item.bind(on_touch_down=lambda inst, touch, c=complaint: (
                self._show_detail_popup(c) if inst.collide_point(*touch.pos) else None
            ))

        item.add_widget(title_lbl)
        item.add_widget(status_lbl)
        return item

    def _show_detail_popup(self, complaint):
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(10),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        fields = [
            ('标题', complaint.get('title', '')),
            ('投诉人', complaint.get('complainant', '')),
            ('电话', complaint.get('phone', '')),
            ('地址', complaint.get('address', '')),
            ('状态', complaint.get('status', '')),
            ('紧急程度', complaint.get('urgency', '')),
            ('内容', complaint.get('content', '')),
            ('回复', complaint.get('reply', '暂无')),
            ('提交时间', complaint.get('created_at', '')),
        ]

        for label, value in fields:
            row = BoxLayout(
                orientation='vertical',
                size_hint=(1, None),
                spacing=dp(2),
            )
            name_lbl = Label(
                text=label,
                font_size=sp(12),
                color=COLORS['primary'],
                bold=True,
                size_hint=(1, None),
                height=dp(18),
                halign='left',
                valign='middle',
            )
            val_lbl = Label(
                text=str(value) if value else '无',
                font_size=sp(13),
                color=COLORS['text_primary'],
                size_hint=(1, None),
                height=dp(22) if len(str(value)) < 30 else dp(38),
                halign='left',
                valign='top',
                text_size=(dp(280), None),
            )
            row.add_widget(name_lbl)
            row.add_widget(val_lbl)
            content.add_widget(row)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(content)

        close_btn = Button(
            text='关闭',
            size_hint=(1, None), height=dp(44),
            background_color=COLORS['primary'],
            background_normal='', color=[1, 1, 1, 1],
        )

        wrapper = BoxLayout(orientation='vertical')
        wrapper.add_widget(scroll)
        wrapper.add_widget(close_btn)

        popup = Popup(
            title='投诉详情',
            content=wrapper,
            size_hint=(0.88, 0.78),
            auto_dismiss=True,
            separator_color=COLORS['primary'],
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _refresh_item_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*SHADOWS['card'])
            RoundedRectangle(
                pos=(instance.x, instance.y),
                size=(instance.size[0], instance.size[1] + dp(2)),
                radius=[RADIUS['md']]*4,
            )
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[RADIUS['md']]*4,
            )

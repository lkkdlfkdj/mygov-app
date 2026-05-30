"""
首页仪表盘页面 HomeScreen
- 统计卡片：总投诉件数、已完成、处理中、紧急（剩余≤3天）
- 最近投诉列表：显示最近3条，点击弹窗查看详情
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT


class StatCard(BoxLayout):
    """统计卡片组件"""

    def __init__(self, title, value, card_color, **kwargs):
        super().__init__(
            orientation='vertical',
            size_hint=(0.5, None),
            height=dp(90),
            padding=[dp(12), dp(10)],
            spacing=dp(4),
            **kwargs
        )
        self.card_color = card_color

        with self.canvas.before:
            Color(*card_color)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8), dp(8), dp(8), dp(8)]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.value_label = Label(
            text=str(value),
            font_size=sp(28),
            color=[1, 1, 1, 1],
            bold=True,
            size_hint=(1, 0.6),
            halign='center',
            valign='middle',
        )
        self.add_widget(self.value_label)

        self.title_label = Label(
            text=title,
            font_size=sp(12),
            color=[1, 1, 1, 0.9],
            size_hint=(1, 0.4),
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
        with toolbar.canvas.before:
            Color(*COLORS['primary'])
            Rectangle(pos=toolbar.pos, size=toolbar.size)
        toolbar.bind(pos=self._update_toolbar_bg,
                     size=self._update_toolbar_bg)

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
            color=[1, 1, 1, 0.8],
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
            spacing=dp(12),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        # ---- 统计卡片网格 ----
        card_grid = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(190),
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
        section_title = Label(
            text='最近投诉',
            font_size=FONT_SIZES['medium'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(36),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(24), None),
        )
        content.add_widget(section_title)

        # ---- 最近投诉列表 ----
        self.recent_list = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=dp(6),
        )
        content.add_widget(self.recent_list)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

        # 延迟加载真实数据
        Clock.schedule_once(lambda dt: self._load_data(), 0.2)

    def on_enter(self):
        """每次进入页面时刷新数据"""
        self._load_data()

    def _update_toolbar_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['primary'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _load_data(self):
        """从SQLite加载真实统计数据"""
        from core.storage import Storage
        storage = Storage()

        # 统计数据
        stats = storage.get_complaint_stats()
        self.card_total.value_label.text = str(stats['total'])
        self.card_done.value_label.text = str(stats['done'])
        self.card_processing.value_label.text = str(stats['processing'])
        self.card_urgent.value_label.text = str(stats['urgent'])

        # 总数据量
        total = stats['total']
        hazards = len(storage.get_all_hazards())
        cases = len(storage.get_all_cases())
        laws = len(storage.get_all_laws())
        ads = len(storage.get_all_ads())
        all_count = total + hazards + cases + laws + ads
        self.count_label.text = f'共{all_count}条'

        # 最近投诉列表（最近3条）
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
        """创建一条最近投诉列表项"""
        item = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            padding=[dp(12), dp(8)],
            spacing=dp(8),
        )
        with item.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=item.pos,
                size=item.size,
                radius=[dp(4), dp(4), dp(4), dp(4)]
            )
        item.bind(pos=self._refresh_item_bg,
                  size=self._refresh_item_bg)

        title_lbl = Label(
            text=title,
            font_size=sp(13),
            color=COLORS['text_primary'],
            size_hint=(0.7, 1),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.6, None),
            shorten=True,
        )
        status_lbl = Label(
            text=status,
            font_size=sp(12),
            color=COLORS['text_secondary'],
            size_hint=(0.3, 1),
            halign='right',
            valign='middle',
        )

        # 点击查看详情
        if complaint:
            item.bind(on_touch_down=lambda inst, touch, c=complaint: (
                self._show_detail_popup(c) if inst.collide_point(*touch.pos) else None
            ))

        item.add_widget(title_lbl)
        item.add_widget(status_lbl)
        return item

    def _show_detail_popup(self, complaint):
        """显示投诉详情弹窗"""
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(8),
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
                font_size=sp(12), color=COLORS['primary'], bold=True,
                size_hint=(1, None), height=dp(18),
                halign='left', valign='middle',
            )
            val_lbl = Label(
                text=str(value) if value else '无',
                font_size=sp(12), color=COLORS['text_primary'],
                size_hint=(1, None),
                height=dp(24) if len(str(value)) < 30 else dp(40),
                halign='left', valign='top',
                text_size=(self.width * 0.7, None),
            )
            row.add_widget(name_lbl)
            row.add_widget(val_lbl)
            content.add_widget(row)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(content)

        close_btn = Button(
            text='关闭',
            size_hint=(1, None), height=dp(40),
            background_color=COLORS['primary'],
            background_normal='', color=[1, 1, 1, 1],
        )

        popup = Popup(
            title='投诉详情',
            content=scroll,
            size_hint=(0.85, 0.75),
            auto_dismiss=True,
        )
        close_btn.bind(on_press=popup.dismiss)
        wrapper = BoxLayout(orientation='vertical')
        wrapper.add_widget(scroll)
        wrapper.add_widget(close_btn)
        popup.content = wrapper
        popup.open()

    def _refresh_item_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[dp(4), dp(4), dp(4), dp(4)]
            )


from kivy.graphics import Rectangle

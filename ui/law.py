"""
法条查询页面 LawQuery
- 内置20类法条（本地内置）
- 分类筛选：全部、市容条例、扬尘防治、城乡规划、渣土许可
- 全文搜索
- 手风琴折叠面板
- 每条包含：违法行为、禁止法条、处罚法条、处罚标准
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT, SPACING, RADIUS, SHADOWS
from ui.styles import toolbar_bg, primary_btn, secondary_btn

# ========== 内置法条数据 ==========
# 结构：id, 类别, 标题, 违法行为, 禁止法条, 处罚法条, 处罚标准
BUILT_IN_LAWS = [
    {
        'id': 1,
        'category': '市容条例',
        'title': '擅自占道经营',
        'violation': '未经批准在城市道路、公共场所从事摆摊设点、兜售物品等经营活动',
        'prohibition': '《城市市容和环境卫生管理条例》第十四条',
        'penalty_law': '《城市市容和环境卫生管理条例》第三十六条',
        'penalty_standard': '责令改正，可处以100元以上1000元以下罚款',
    },
    {
        'id': 2,
        'category': '市容条例',
        'title': '乱张贴涂写',
        'violation': '在城市建筑物、设施以及树木上涂写、刻画或者未经批准张挂、张贴宣传品',
        'prohibition': '《城市市容和环境卫生管理条例》第十七条',
        'penalty_law': '《城市市容和环境卫生管理条例》第三十四条',
        'penalty_standard': '责令改正，可处以50元以上500元以下罚款',
    },
    {
        'id': 3,
        'category': '市容条例',
        'title': '临街建筑不洁',
        'violation': '临街建筑物、构筑物容貌不整洁或者设施破损未及时修复',
        'prohibition': '《城市市容和环境卫生管理条例》第九条',
        'penalty_law': '《城市市容和环境卫生管理条例》第三十六条',
        'penalty_standard': '责令限期改正；逾期不改的，可处以200元以上2000元以下罚款',
    },
    {
        'id': 4,
        'category': '扬尘防治',
        'title': '施工未设围挡',
        'violation': '工程施工未设置硬质围挡，或者未采取覆盖、分段作业、择时施工、洒水抑尘等有效防尘措施',
        'prohibition': '《中华人民共和国大气污染防治法》第六十九条',
        'penalty_law': '《中华人民共和国大气污染防治法》第一百一十五条',
        'penalty_standard': '责令改正，处1万元以上10万元以下罚款；拒不改正的，责令停工整治',
    },
    {
        'id': 5,
        'category': '扬尘防治',
        'title': '裸露地面未覆盖',
        'violation': '城镇地区裸露地面未进行绿化、透水铺装或者遮盖',
        'prohibition': '《中华人民共和国大气污染防治法》第七十二条',
        'penalty_law': '《中华人民共和国大气污染防治法》第一百一十七条',
        'penalty_standard': '责令改正，处1万元以上10万元以下罚款',
    },
    {
        'id': 6,
        'category': '扬尘防治',
        'title': '运输车辆未密闭',
        'violation': '运输煤炭、垃圾、渣土、砂石、土方、灰浆等散装、流体物料的车辆，未采取密闭或者其他措施防止物料遗撒',
        'prohibition': '《中华人民共和国大气污染防治法》第七十条',
        'penalty_law': '《中华人民共和国大气污染防治法》第一百一十六条',
        'penalty_standard': '责令改正，处2000元以上2万元以下罚款；拒不改正的，车辆不得上道路行驶',
    },
    {
        'id': 7,
        'category': '城乡规划',
        'title': '未取得规划许可建设',
        'violation': '未取得建设工程规划许可证或者未按照建设工程规划许可证的规定进行建设',
        'prohibition': '《中华人民共和国城乡规划法》第四十条',
        'penalty_law': '《中华人民共和国城乡规划法》第六十四条',
        'penalty_standard': '责令停止建设；尚可采取改正措施的，限期改正，处建设工程造价5%以上10%以下罚款；无法改正的，限期拆除',
    },
    {
        'id': 8,
        'category': '城乡规划',
        'title': '临时建筑逾期未拆',
        'violation': '临时建设工程超过批准期限不拆除',
        'prohibition': '《中华人民共和国城乡规划法》第四十四条',
        'penalty_law': '《中华人民共和国城乡规划法》第六十六条',
        'penalty_standard': '责令限期拆除，可以并处临时建设工程造价一倍以下罚款',
    },
    {
        'id': 9,
        'category': '渣土许可',
        'title': '无证运输建筑垃圾',
        'violation': '未经核准擅自处置建筑垃圾或者处置超出核准范围的建筑垃圾',
        'prohibition': '《城市建筑垃圾管理规定》第七条',
        'penalty_law': '《城市建筑垃圾管理规定》第二十五条',
        'penalty_standard': '责令限期改正，给予警告，对施工单位处1万元以上10万元以下罚款，对运输单位处5000元以上3万元以下罚款',
    },
    {
        'id': 10,
        'category': '渣土许可',
        'title': '随意倾倒建筑垃圾',
        'violation': '随意倾倒、抛撒或者堆放建筑垃圾',
        'prohibition': '《城市建筑垃圾管理规定》第十五条',
        'penalty_law': '《城市建筑垃圾管理规定》第二十六条',
        'penalty_standard': '责令限期改正，给予警告，对单位处5000元以上5万元以下罚款，对个人处200元以下罚款',
    },
    {
        'id': 11,
        'category': '市容条例',
        'title': '违规设置户外广告',
        'violation': '未经批准擅自设置户外广告设施或者超出批准内容设置',
        'prohibition': '《城市市容和环境卫生管理条例》第十一条',
        'penalty_law': '《城市市容和环境卫生管理条例》第三十六条',
        'penalty_standard': '责令限期拆除，可处以500元以上5000元以下罚款',
    },
    {
        'id': 12,
        'category': '市容条例',
        'title': '店外经营',
        'violation': '临街经营者超出店铺门窗店外经营、作业或者展示商品',
        'prohibition': '《城市市容和环境卫生管理条例》第十四条',
        'penalty_law': '《城市市容和环境卫生管理条例》第三十六条',
        'penalty_standard': '责令改正，可处以100元以上1000元以下罚款',
    },
    {
        'id': 13,
        'category': '扬尘防治',
        'title': '搅拌站未采取抑尘措施',
        'violation': '混凝土搅拌站未采取密闭、围挡、洒水、覆盖等扬尘防治措施',
        'prohibition': '《中华人民共和国大气污染防治法》第七十二条',
        'penalty_law': '《中华人民共和国大气污染防治法》第一百一十七条',
        'penalty_standard': '责令改正，处1万元以上10万元以下罚款',
    },
    {
        'id': 14,
        'category': '城乡规划',
        'title': '违法建设',
        'violation': '未经批准进行临时建设或者未按照批准内容进行临时建设',
        'prohibition': '《中华人民共和国城乡规划法》第四十四条',
        'penalty_law': '《中华人民共和国城乡规划法》第六十六条',
        'penalty_standard': '责令限期拆除，可以并处临时建设工程造价一倍以下罚款',
    },
    {
        'id': 15,
        'category': '渣土许可',
        'title': '建筑垃圾混入生活垃圾',
        'violation': '将建筑垃圾混入生活垃圾或者将危险废物混入建筑垃圾',
        'prohibition': '《城市建筑垃圾管理规定》第九条',
        'penalty_law': '《城市建筑垃圾管理规定》第二十条',
        'penalty_standard': '责令限期改正，给予警告，对单位处3000元以下罚款，对个人处200元以下罚款',
    },
    {
        'id': 16,
        'category': '市容条例',
        'title': '乱倒污水',
        'violation': '随意倾倒生活、餐饮污水或者乱扔废弃物',
        'prohibition': '《城市市容和环境卫生管理条例》第二十八条',
        'penalty_law': '《城市市容和环境卫生管理条例》第三十四条',
        'penalty_standard': '责令改正，可处以20元以上200元以下罚款',
    },
    {
        'id': 17,
        'category': '扬尘防治',
        'title': '拆除工程未采取抑尘措施',
        'violation': '拆除房屋或者其他建筑物时未采取喷淋、洒水等抑尘措施',
        'prohibition': '《中华人民共和国大气污染防治法》第六十九条',
        'penalty_law': '《中华人民共和国大气污染防治法》第一百一十五条',
        'penalty_standard': '责令改正，处1万元以上10万元以下罚款',
    },
    {
        'id': 18,
        'category': '城乡规划',
        'title': '擅自改变规划用途',
        'violation': '未经批准擅自改变建筑物使用性质、规划用途',
        'prohibition': '《中华人民共和国城乡规划法》第四十三条',
        'penalty_law': '《中华人民共和国城乡规划法》第六十四条',
        'penalty_standard': '责令限期改正，处建设工程造价5%以上10%以下罚款',
    },
    {
        'id': 19,
        'category': '渣土许可',
        'title': '未设置车辆冲洗设施',
        'violation': '建筑垃圾处置场所未设置车辆冲洗设施，导致车辆带泥上路',
        'prohibition': '《城市建筑垃圾管理规定》第十四条',
        'penalty_law': '《城市建筑垃圾管理规定》第二十二条',
        'penalty_standard': '责令限期改正，给予警告，可处以5000元以上2万元以下罚款',
    },
    {
        'id': 20,
        'category': '扬尘防治',
        'title': '物料堆放未覆盖',
        'violation': '建筑土方、工程渣土、建筑垃圾未及时清运，或者未采用密闭式防尘网遮盖',
        'prohibition': '《中华人民共和国大气污染防治法》第六十九条',
        'penalty_law': '《中华人民共和国大气污染防治法》第一百一十五条',
        'penalty_standard': '责令改正，处1万元以上10万元以下罚款',
    },
]


class LawCard(BoxLayout):
    """法律法规单项卡片"""

    def __init__(self, law_data, **kwargs):
        super().__init__(
            orientation='vertical',
            size_hint=(1, None),
            spacing=0,
            **kwargs
        )
        self.law_data = law_data
        self._expanded = False

        # 标题按钮
        self.header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(12), dp(8)],
            spacing=dp(8),
        )
        with self.header.canvas.before:
            Color(*COLORS['surface'])
            self.header_bg = RoundedRectangle(
                pos=self.header.pos,
                size=self.header.size,
                radius=[dp(6), dp(6), 0, 0],
            )
        self.header.bind(pos=self._refresh_header_bg,
                         size=self._refresh_header_bg)

        # 展开指示器
        self.indicator = Label(
            text='▶',
            font_size=sp(14),
            size_hint=(0.08, 1),
            halign='center',
            valign='middle',
            color=COLORS['primary'],
        )
        self.header.add_widget(self.indicator)

        # 类别标签
        cat_lbl = Label(
            text=f'[{law_data["category"]}]',
            font_size=sp(11),
            size_hint=(0.22, 1),
            halign='left',
            valign='middle',
            color=COLORS['primary'],
            bold=True,
        )
        self.header.add_widget(cat_lbl)

        # 标题
        title_lbl = Label(
            text=law_data['title'],
            font_size=sp(13),
            size_hint=(0.7, 1),
            halign='left',
            valign='middle',
            color=COLORS['text_primary'],
            shorten=True,
        )
        self.header.add_widget(title_lbl)

        self.header.bind(on_touch_down=self._on_header_touch)
        self.add_widget(self.header)

        # 详情内容（默认隐藏）
        self.detail = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            padding=[dp(12), dp(10)],
            spacing=dp(6),
            opacity=0,
            disabled=True,
        )
        with self.detail.canvas.before:
            Color(*COLORS['background'])
            self.detail_bg = RoundedRectangle(
                pos=self.detail.pos,
                size=self.detail.size,
                radius=[0, 0, dp(6), dp(6)],
            )
        self.detail.bind(pos=self._refresh_detail_bg,
                         size=self._refresh_detail_bg)

        # 添加详情字段
        fields = [
            ('违法行为', law_data['violation']),
            ('禁止法条', law_data['prohibition']),
            ('处罚法条', law_data['penalty_law']),
            ('处罚标准', law_data['penalty_standard']),
        ]
        for field_name, field_value in fields:
            field_box = BoxLayout(
                orientation='vertical',
                size_hint=(1, None),
                spacing=dp(2),
            )
            name_lbl = Label(
                text=field_name,
                font_size=sp(11),
                color=COLORS['primary'],
                bold=True,
                size_hint=(1, None),
                height=dp(18),
                halign='left',
                valign='middle',
                text_size=(self.width - dp(24), None),
            )
            val_lbl = Label(
                text=field_value,
                font_size=sp(12),
                color=COLORS['text_primary'],
                size_hint=(1, None),
                height=dp(36),
                halign='left',
                valign='top',
                text_size=(self.width - dp(24), None),
            )
            field_box.add_widget(name_lbl)
            field_box.add_widget(val_lbl)
            self.detail.add_widget(field_box)

        # 计算详情高度
        self.detail.height = len(fields) * dp(60) + dp(20)

        self.add_widget(self.detail)

        # 整体高度
        self.height = dp(50)

    def _refresh_header_bg(self, instance, value):
        self.header_bg.pos = instance.pos
        self.header_bg.size = instance.size

    def _refresh_detail_bg(self, instance, value):
        self.detail_bg.pos = instance.pos
        self.detail_bg.size = instance.size

    def _on_header_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if touch.grab_current == instance:
                return
            self.toggle()

    def toggle(self):
        """切换展开/折叠"""
        self._expanded = not self._expanded
        if self._expanded:
            self.indicator.text = '▼'
            self.detail.opacity = 1
            self.detail.disabled = False
            self.height = dp(50) + self.detail.height
        else:
            self.indicator.text = '▶'
            self.detail.opacity = 0
            self.detail.disabled = True
            self.height = dp(50)


class LawScreen(Screen):
    """法条查询页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'law'
        self._all_laws = BUILT_IN_LAWS
        self._current_category = '全部'
        self._search_text = ''

        # ---- 主布局 ----
        root = BoxLayout(orientation='vertical')

        # ---- 顶部标题栏 ----
        toolbar = BoxLayout(
            size_hint=(1, None),
            height=TOOLBAR_HEIGHT,
            padding=[dp(16), 0],
        )
        toolbar_bg(toolbar)

        title_label = Label(
            text=PAGE_TITLES['law'],
            font_size=FONT_SIZES['title'],
            color=[1, 1, 1, 1],
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 1),
        )
        toolbar.add_widget(title_label)

        # 法条计数
        count_label = Label(
            text=f'共{len(self._all_laws)}条',
            font_size=sp(12),
            color=[1, 1, 1, 0.8],
            size_hint=(0.3, 1),
            halign='right',
            valign='middle',
        )
        toolbar.add_widget(count_label)
        root.add_widget(toolbar)

        # ---- 搜索栏 ----
        search_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            padding=[dp(12), dp(6)],
            spacing=dp(8),
        )
        with search_bar.canvas.before:
            Color(*COLORS['surface'])
            Rectangle(pos=search_bar.pos, size=search_bar.size)
        search_bar.bind(pos=self._refresh_search_bg,
                        size=self._refresh_search_bg)

        self.search_input = TextInput(
            hint_text='搜索法条...',
            font_size=FONT_SIZES['body'],
            size_hint=(0.8, 1),
            multiline=False,
            padding=[dp(8), dp(4)],
        )
        self.search_input.bind(text=self._on_search_text)
        search_bar.add_widget(self.search_input)

        search_btn = Button(
            text='搜索',
            font_size=FONT_SIZES['body'],
            size_hint=(0.2, 1),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        search_btn.bind(on_press=self._do_search)
        search_bar.add_widget(search_btn)
        root.add_widget(search_bar)

        # ---- 分类筛选 ----
        categories = ['全部', '市容条例', '扬尘防治', '城乡规划', '渣土许可']
        filter_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(42),
            spacing=dp(4),
            padding=[dp(8), dp(4)],
        )
        with filter_bar.canvas.before:
            Color(*COLORS['background'])
            Rectangle(pos=filter_bar.pos, size=filter_bar.size)
        filter_bar.bind(pos=self._refresh_filter_bg,
                        size=self._refresh_filter_bg)

        self.filter_buttons = {}
        for cat in categories:
            btn = ToggleButton(
                text=cat,
                font_size=sp(11),
                size_hint=(1.0 / len(categories), 1),
                background_color=COLORS['primary'],
                background_normal='',
                color=[1, 1, 1, 1],
                group='law_filter',
                state='down' if cat == '全部' else 'normal',
            )
            btn.bind(on_press=self._on_filter)
            self.filter_buttons[cat] = btn
            filter_bar.add_widget(btn)
        root.add_widget(filter_bar)

        # ---- 法条列表 ----
        scroll = ScrollView()
        self.list_content = BoxLayout(
            orientation='vertical',
            padding=[dp(8), dp(8)],
            spacing=dp(4),
            size_hint=(1, None),
        )
        self.list_content.bind(
            minimum_height=self.list_content.setter('height')
        )
        scroll.add_widget(self.list_content)
        root.add_widget(scroll)

        self.add_widget(root)

        # 初始化显示所有法条
        Clock.schedule_once(lambda dt: self._render_list(), 0.1)

    def _refresh_search_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['surface'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _refresh_filter_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['background'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _on_search_text(self, instance, value):
        """实时搜索"""
        self._search_text = value.strip()
        self._render_list()

    def _do_search(self, instance):
        """搜索按钮点击"""
        self._render_list()

    def _on_filter(self, instance):
        """分类筛选"""
        self._current_category = instance.text
        self._render_list()

    def _render_list(self):
        """根据筛选条件和搜索词渲染法条列表"""
        self.list_content.clear_widgets()

        filtered = self._all_laws

        # 分类筛选
        if self._current_category != '全部':
            filtered = [law for law in filtered
                        if law['category'] == self._current_category]

        # 全文搜索
        if self._search_text:
            keyword = self._search_text.lower()
            filtered = [
                law for law in filtered
                if keyword in law['title'].lower()
                or keyword in law['violation'].lower()
                or keyword in law['category'].lower()
            ]

        if not filtered:
            no_data = Label(
                text='未找到匹配的法条',
                font_size=FONT_SIZES['body'],
                color=COLORS['text_secondary'],
                size_hint=(1, None),
                height=dp(80),
                halign='center',
                valign='middle',
            )
            self.list_content.add_widget(no_data)
            return

        for law in filtered:
            item = LawCard(law_data=law)
            self.list_content.add_widget(item)

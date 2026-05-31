"""
店招申请页面 AdvertisementScreen
- 5步流程展示：提报申请、材料审核、现场查勘、审批发证、安装验收
- 查勘任务状态：上传图片→待完成、再次上传→已完成
- 施工要求 + 查勘表（本地内置）
- 新增申请、上传查勘照片，数据保存到SQLite
"""

import os
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT, SPACING, RADIUS, SHADOWS
from ui.styles import toolbar_bg, primary_btn, secondary_btn

# ========== 5步流程数据 ==========
STEPS = [
    {'num': '1', 'title': '提报申请',
     'desc': '申请人提交店招设置申请材料\n'
             '包括：申请表、营业执照、\n'
             '产权证明、设计效果图'},
    {'num': '2', 'title': '材料审核',
     'desc': '审核申请材料完整性与合规性\n'
             '材料不齐全的一次性告知补正'},
    {'num': '3', 'title': '现场查勘',
     'desc': '执法人员现场查勘\n'
             '核实设置位置、尺寸、样式\n'
             '是否符合规划要求'},
    {'num': '4', 'title': '审批发证',
     'desc': '审核通过后发放\n'
             '《户外广告设置许可证》\n'
             '有效期一般为2年'},
    {'num': '5', 'title': '安装验收',
     'desc': '安装完成后现场验收\n'
             '核实是否按审批方案施工\n'
             '验收合格归档'},
]

# ========== 施工要求 ==========
CONSTRUCTION_REQUIREMENTS = [
    '1. 店招设置应牢固、安全，符合建筑荷载要求',
    '2. 不得遮挡建筑物门窗，影响采光通风',
    '3. 不得影响消防安全和疏散通道',
    '4. 应使用符合国家标准的材料',
    '5. 夜间应有照明设施（不得扰民）',
    '6. 不得破坏建筑物原有结构',
    '7. 施工期间应设置安全围挡',
]

# ========== 查勘表 ==========
SURVEY_ITEMS = [
    {'item': '设置位置', 'standard': '与审批位置一致'},
    {'item': '设置尺寸', 'standard': '长≤5m，宽≤1.5m，厚度≤0.3m'},
    {'item': '安全检测', 'standard': '结构稳固，焊接牢固'},
    {'item': '外观要求', 'standard': '整洁美观，无破损'},
    {'item': '用电安全', 'standard': '线路规范，防水防漏电'},
    {'item': '消防要求', 'standard': '不遮挡消防设施'},
]


class StepCard(BoxLayout):
    """流程步骤卡片"""

    def __init__(self, step_data, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(100),
            padding=[dp(12), dp(10)],
            spacing=dp(12),
            **kwargs
        )
        with self.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8), dp(8), dp(8), dp(8)]
            )
        self.bind(pos=self._refresh_bg, size=self._refresh_bg)

        num_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.15, 1),
        )
        num_label = Label(
            text=step_data['num'],
            font_size=sp(28),
            color=COLORS['primary'],
            bold=True,
            halign='center',
            valign='middle',
        )
        num_box.add_widget(num_label)
        self.add_widget(num_box)

        content = BoxLayout(
            orientation='vertical',
            size_hint=(0.85, 1),
            spacing=dp(2),
        )
        title_lbl = Label(
            text=step_data['title'],
            font_size=FONT_SIZES['medium'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, 0.35),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.8, None),
        )
        desc_lbl = Label(
            text=step_data['desc'],
            font_size=FONT_SIZES['small'],
            color=COLORS['text_secondary'],
            size_hint=(1, 0.65),
            halign='left',
            valign='top',
            text_size=(self.width * 0.8, None),
        )
        content.add_widget(title_lbl)
        content.add_widget(desc_lbl)
        self.add_widget(content)

    def _refresh_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8), dp(8), dp(8), dp(8)]
            )


class AdScreen(Screen):
    """店招申请页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'ad'

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
            text=PAGE_TITLES['ad'],
            font_size=FONT_SIZES['title'],
            color=[1, 1, 1, 1],
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 1),
        )
        toolbar.add_widget(title_label)
        root.add_widget(toolbar)

        # ---- 可滚动内容区 ----
        scroll = ScrollView()
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(14),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        # ---- 5步流程 ----
        steps_title = Label(
            text='📋 店招申请流程',
            font_size=FONT_SIZES['large'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(36),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(steps_title)

        for step in STEPS:
            card = StepCard(step_data=step)
            content.add_widget(card)

        # ---- 新增申请按钮 ----
        add_btn = Button(
            text='＋ 新增店招申请',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        add_btn.bind(on_press=self._show_add_popup)
        content.add_widget(add_btn)

        # ---- 申请列表 ----
        list_title = Label(
            text='📋 申请列表',
            font_size=FONT_SIZES['medium'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(32),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(list_title)

        self.list_content = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=dp(6),
        )
        content.add_widget(self.list_content)

        # ---- 查勘任务状态 ----
        survey_title = Label(
            text='🔍 查勘任务状态',
            font_size=FONT_SIZES['large'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(36),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(survey_title)

        # 查勘状态卡片
        survey_card = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(90),
            padding=[dp(12), dp(10)],
            spacing=dp(6),
        )
        with survey_card.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=survey_card.pos,
                size=survey_card.size,
                radius=[dp(8), dp(8), dp(8), dp(8)]
            )
        survey_card.bind(pos=self._refresh_survey_card,
                         size=self._refresh_survey_card)

        self.survey_status = Label(
            text='当前状态：待查勘  ⏳',
            font_size=FONT_SIZES['body'],
            color=COLORS['warning'],
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        survey_card.add_widget(self.survey_status)

        survey_hint = Label(
            text='上传查勘照片后状态更新为"已完成"',
            font_size=sp(12),
            color=COLORS['text_secondary'],
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        survey_card.add_widget(survey_hint)
        content.add_widget(survey_card)

        # 上传查勘照片按钮
        upload_btn = Button(
            text='📷 上传查勘照片',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['primary_light'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        upload_btn.bind(on_press=self._on_upload)
        content.add_widget(upload_btn)

        # ---- 施工要求 ----
        const_title = Label(
            text='🔧 施工要求',
            font_size=FONT_SIZES['large'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(36),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(const_title)

        for req in CONSTRUCTION_REQUIREMENTS:
            req_lbl = Label(
                text=req,
                font_size=FONT_SIZES['small'],
                color=COLORS['text_primary'],
                size_hint=(1, None),
                height=dp(28),
                halign='left',
                valign='middle',
                text_size=(self.width - dp(32), None),
            )
            content.add_widget(req_lbl)

        # ---- 查勘表 ----
        survey_table_title = Label(
            text='📋 现场查勘表',
            font_size=FONT_SIZES['large'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(36),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(survey_table_title)

        for item in SURVEY_ITEMS:
            table_item = BoxLayout(
                orientation='horizontal',
                size_hint=(1, None),
                height=dp(40),
                padding=[dp(8), dp(4)],
                spacing=dp(8),
            )
            with table_item.canvas.before:
                Color(*COLORS['surface'])
                RoundedRectangle(
                    pos=table_item.pos,
                    size=table_item.size,
                    radius=[dp(4), dp(4), dp(4), dp(4)]
                )
            table_item.bind(pos=self._refresh_table_item,
                            size=self._refresh_table_item)

            item_name = Label(
                text=item['item'],
                font_size=FONT_SIZES['body'],
                color=COLORS['primary'],
                bold=True,
                size_hint=(0.3, 1),
                halign='left',
                valign='middle',
            )
            item_std = Label(
                text=item['standard'],
                font_size=FONT_SIZES['small'],
                color=COLORS['text_primary'],
                size_hint=(0.7, 1),
                halign='left',
                valign='middle',
            )
            table_item.add_widget(item_name)
            table_item.add_widget(item_std)
            content.add_widget(table_item)

        # 底部间距
        content.add_widget(BoxLayout(
            size_hint=(1, None), height=dp(20)
        ))

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

        # 延迟加载列表
        Clock.schedule_once(lambda dt: self._refresh_list(), 0.2)

    def on_enter(self):
        """进入页面时刷新列表"""
        self._refresh_list()

    # ==================== 申请列表 ====================

    def _refresh_list(self):
        """从SQLite读取申请列表"""
        from core.storage import Storage
        storage = Storage()
        ads = storage.get_all_ads()

        self.list_content.clear_widgets()

        if not ads:
            empty_lbl = Label(
                text='暂无申请',
                font_size=sp(12),
                color=COLORS['text_secondary'],
                size_hint=(1, None),
                height=dp(40),
                halign='center',
                valign='middle',
            )
            self.list_content.add_widget(empty_lbl)
            return

        for a in ads[:5]:
            item = self._create_ad_item(a)
            self.list_content.add_widget(item)

        if len(ads) > 5:
            more_lbl = Label(
                text=f'... 还有 {len(ads)-5} 条',
                font_size=sp(11),
                color=COLORS['text_secondary'],
                size_hint=(1, None),
                height=dp(24),
                halign='left',
                valign='middle',
            )
            self.list_content.add_widget(more_lbl)

    def _create_ad_item(self, ad):
        """创建一条申请列表项"""
        item = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(10), dp(6)],
            spacing=dp(6),
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

        info_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.7, 1),
        )
        shop_lbl = Label(
            text=ad.get('shop_name', '无店名'),
            font_size=sp(13),
            color=COLORS['text_primary'],
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.55, None),
            bold=True,
            shorten=True,
        )
        meta_lbl = Label(
            text=f"{ad.get('applicant', '')} | {ad.get('created_at', '')}",
            font_size=sp(10),
            color=COLORS['text_secondary'],
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.55, None),
            shorten=True,
        )
        info_box.add_widget(shop_lbl)
        info_box.add_widget(meta_lbl)

        status = ad.get('survey_status', '待查勘')
        status_color = COLORS['warning'] if status == '待查勘' else COLORS['success']
        status_lbl = Label(
            text=status,
            font_size=sp(11),
            color=status_color,
            size_hint=(0.3, 1),
            halign='center',
            valign='middle',
            bold=True,
        )

        item.add_widget(info_box)
        item.add_widget(status_lbl)
        return item

    def _refresh_item_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[dp(4), dp(4), dp(4), dp(4)]
            )

    # ==================== 新增申请 ====================

    def _show_add_popup(self, instance):
        """显示新增申请弹窗"""
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(8),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        fields = [
            ('申请人', 'applicant'),
            ('店铺名称', 'shop_name'),
            ('地址', 'address'),
        ]
        inputs = {}
        for label_text, field_name in fields:
            row = BoxLayout(
                orientation='vertical',
                size_hint=(1, None),
                spacing=dp(2),
            )
            lbl = Label(
                text=label_text,
                font_size=sp(12),
                color=COLORS['text_primary'],
                size_hint=(1, None),
                height=dp(18),
                halign='left',
                valign='middle',
                bold=True,
            )
            inp = TextInput(
                text='',
                hint_text=f'请输入{label_text}',
                font_size=sp(13),
                size_hint=(1, None),
                height=dp(36),
                multiline=False,
            )
            row.add_widget(lbl)
            row.add_widget(inp)
            content.add_widget(row)
            inputs[field_name] = inp

        # 提交
        submit_btn = Button(
            text='✓ 提交申请',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
            bold=True,
        )

        popup = Popup(
            title='新增店招申请',
            title_color=COLORS['text_primary'],
            title_size=sp(14),
            content=content,
            size_hint=(0.88, 0.55),
            auto_dismiss=False,
        )

        submit_btn.bind(
            on_press=lambda btn: self._submit_ad(inputs, popup)
        )
        content.add_widget(submit_btn)

        close_btn = Button(
            text='取消',
            font_size=sp(13),
            size_hint=(1, None),
            height=dp(38),
            background_color=COLORS['divider'],
            background_normal='',
            color=COLORS['text_primary'],
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)

        popup.open()

    def _submit_ad(self, inputs, popup):
        """提交店招申请到SQLite"""
        applicant = inputs['applicant'].text.strip()
        shop_name = inputs['shop_name'].text.strip()

        if not applicant or not shop_name:
            app = self._get_app()
            if app:
                app.show_toast('请填写申请人和店铺名称', 'warning')
            return

        from core.storage import Storage
        storage = Storage()
        ad_id = storage.add_ad({
            'applicant': applicant,
            'shop_name': shop_name,
            'address': inputs['address'].text.strip(),
        })

        popup.dismiss()
        app = self._get_app()
        if ad_id:
            if app:
                app.show_toast(f'店招申请已提交（编号{ad_id}）', 'success')
            self._refresh_list()
        else:
            if app:
                app.show_toast('提交失败', 'error')

    # ==================== 查勘照片上传 ====================

    def _on_upload(self, instance):
        """上传查勘照片"""
        # 先获取最旧的待查勘申请
        from core.storage import Storage
        storage = Storage()
        ads = storage.get_all_ads()
        pending = [a for a in ads if a.get('survey_status') == '待查勘']

        if not pending:
            app = self._get_app()
            if app:
                app.show_toast('暂无待查勘的申请', 'info')
            return

        # 选择照片
        fc_content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(
            path='C:\\',
            filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'],
        )
        fc_content.add_widget(filechooser)

        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(8),
            padding=[dp(8), dp(4)],
        )
        select_btn = Button(
            text='选择上传',
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        cancel_btn = Button(
            text='取消',
            background_color=COLORS['divider'],
            background_normal='',
            color=COLORS['text_primary'],
        )
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        fc_content.add_widget(btn_row)

        file_popup = Popup(
            title='选择查勘照片',
            content=fc_content,
            size_hint=(0.92, 0.85),
            auto_dismiss=False,
        )

        def on_select(instance):
            if filechooser.selection and len(filechooser.selection) > 0:
                photo_paths = filechooser.selection[:6]
                # 更新第一个待查勘的申请
                target = pending[0]
                target_id = target['id']
                storage.update_ad_survey(target_id, photo_paths, '已完成')
                self.survey_status.text = '当前状态：查勘已完成 ✅'
                self.survey_status.color = COLORS['success']

                app = self._get_app()
                if app:
                    app.show_toast(
                        f'已上传 {len(photo_paths)} 张查勘照片，'
                        f'申请（编号{target_id}）状态已更新',
                        'success'
                    )
                self._refresh_list()
            file_popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=file_popup.dismiss)
        file_popup.open()

    # ==================== UI辅助 ====================

    def _refresh_survey_card(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[dp(8), dp(8), dp(8), dp(8)]
            )

    def _refresh_table_item(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[dp(4), dp(4), dp(4), dp(4)]
            )

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

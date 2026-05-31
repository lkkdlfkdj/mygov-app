"""
案件采集页面 CaseScreen
- 双Tab页：扣单管理、责令整改
- 输入编号范围（例001-050）
- 上传图片→OCR识别数字→自动匹配编号→关联归档
- 详情查看、删除、导出Excel
"""

import os
from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT, SPACING, RADIUS, SHADOWS
from ui.styles import toolbar_bg, primary_btn, secondary_btn
from core.yolo_ocr import OCREngine
from core.export import export_data, EXPORT_FORMATS


class CaseScreen(Screen):
    """案件采集页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'case'
        self._current_tab = 'deduction'  # 'deduction' 或 'rectify'
        self.ocr_engine = OCREngine()
        self._ocr_image_path = ''

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
            text=PAGE_TITLES['case'],
            font_size=FONT_SIZES['title'],
            color=[1, 1, 1, 1],
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 1),
        )
        toolbar.add_widget(title_label)
        root.add_widget(toolbar)

        # ---- 双Tab切换 ----
        tab_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=0,
        )
        with tab_bar.canvas.before:
            Color(*COLORS['background'])
            Rectangle(pos=tab_bar.pos, size=tab_bar.size)
        tab_bar.bind(pos=self._refresh_tab_bar_bg,
                     size=self._refresh_tab_bar_bg)

        self.tab_deduction = ToggleButton(
            text='扣单管理',
            font_size=FONT_SIZES['body'],
            size_hint=(0.5, 1),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
            state='down',
            group='case_tabs',
        )
        self.tab_deduction.bind(on_press=self._switch_to_deduction)

        self.tab_rectify = ToggleButton(
            text='责令整改',
            font_size=FONT_SIZES['body'],
            size_hint=(0.5, 1),
            background_color=COLORS['primary_light'],
            background_normal='',
            color=[1, 1, 1, 1],
            group='case_tabs',
        )
        self.tab_rectify.bind(on_press=self._switch_to_rectify)

        tab_bar.add_widget(self.tab_deduction)
        tab_bar.add_widget(self.tab_rectify)
        root.add_widget(tab_bar)

        # ---- 内容区 ----
        scroll = ScrollView()
        self.content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(14),
            size_hint=(1, None),
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

        self.add_widget(root)

        # 初始化显示扣单管理内容
        Clock.schedule_once(lambda dt: self._show_deduction_content(), 0.1)

    def _refresh_tab_bar_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['background'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _switch_to_deduction(self, instance):
        if self._current_tab != 'deduction':
            self._current_tab = 'deduction'
            self.tab_deduction.background_color = COLORS['primary']
            self.tab_rectify.background_color = COLORS['primary_light']
            self._show_deduction_content()

    def _switch_to_rectify(self, instance):
        if self._current_tab != 'rectify':
            self._current_tab = 'rectify'
            self.tab_rectify.background_color = COLORS['primary']
            self.tab_deduction.background_color = COLORS['primary_light']
            self._show_rectify_content()

    def _show_deduction_content(self):
        """显示扣单管理内容 - 含OCR编号识别"""
        self.content.clear_widgets()

        # 编号范围
        self._add_section_title('📄 扣单编号范围')
        range_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
        )
        self.start_input = TextInput(
            text='001',
            font_size=FONT_SIZES['body'],
            size_hint=(0.4, 1),
            multiline=False,
        )
        self.end_input = TextInput(
            text='050',
            font_size=FONT_SIZES['body'],
            size_hint=(0.4, 1),
            multiline=False,
        )
        sep = Label(
            text='—',
            font_size=sp(18),
            size_hint=(0.2, 1),
            halign='center',
            valign='middle',
        )
        range_box.add_widget(self.start_input)
        range_box.add_widget(sep)
        range_box.add_widget(self.end_input)
        self.content.add_widget(range_box)

        # ---- 图片选择 + OCR识别 ----
        ocr_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
        )
        self.ocr_path_label = TextInput(
            text='',
            hint_text='选择扣单图片...',
            font_size=sp(12),
            size_hint=(0.55, 1),
            multiline=False,
            readonly=False,
        )
        select_btn = Button(
            text='选择图片',
            font_size=sp(12),
            size_hint=(0.2, 1),
            background_color=COLORS['primary_light'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        select_btn.bind(on_press=lambda btn: self._select_case_image())
        ocr_btn = Button(
            text='OCR识别',
            font_size=sp(12),
            size_hint=(0.25, 1),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        ocr_btn.bind(on_press=self._on_ocr)
        ocr_row.add_widget(self.ocr_path_label)
        ocr_row.add_widget(select_btn)
        ocr_row.add_widget(ocr_btn)
        self.content.add_widget(ocr_row)

        # OCR状态提示
        backend_text = self.ocr_engine.get_status_text()
        self.ocr_status = Label(
            text=backend_text + '\n选择扣单图片后点击OCR识别编号',
            font_size=sp(11),
            color=COLORS['text_secondary'],
            size_hint=(1, None),
            height=dp(40),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        self.content.add_widget(self.ocr_status)

        # 识别结果显示
        self.ocr_result_label = Label(
            text='',
            font_size=sp(13),
            color=COLORS['primary'],
            size_hint=(1, None),
            height=dp(24),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
            bold=True,
        )
        self.content.add_widget(self.ocr_result_label)

        # 手动归档按钮
        archive_btn = Button(
            text='📦 归档到编号范围',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        archive_btn.bind(on_press=self._on_archive)
        self.content.add_widget(archive_btn)

        # 已归档扣单列表
        self._add_section_title('已归档扣单')
        self._build_archived_list('deduction')

        # 导出按钮
        export_btn = Button(
            text='📤 导出Excel',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        export_btn.bind(on_press=self._on_export)
        self.content.add_widget(export_btn)

    def _show_rectify_content(self):
        """显示责令整改完整表单"""
        self.content.clear_widgets()
        self._rectify_photo_paths = []

        # ============ 当事人信息 ============
        self._add_section_title('👤 当事人信息')
        fields = [
            ('当事人姓名', 'party_name', False),
            ('联系电话', 'party_phone', False),
            ('联系地址', 'party_address', False),
        ]
        self._rectify_inputs = {}
        for label_text, field_name, is_multiline in fields:
            row = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=dp(2))
            lbl = Label(
                text=label_text, font_size=sp(12), color=COLORS['primary'],
                size_hint=(1, None), height=dp(18),
                halign='left', valign='middle', bold=True,
            )
            inp = TextInput(
                text='', hint_text=f'请输入{label_text}',
                font_size=sp(13), size_hint=(1, None), height=dp(36),
                multiline=False,
            )
            row.add_widget(lbl)
            row.add_widget(inp)
            self.content.add_widget(row)
            self._rectify_inputs[field_name] = inp

        # ============ 违法事实 ============
        self._add_section_title('⚠️ 违法事实')
        self._rectify_inputs['violation_fact'] = TextInput(
            text='', hint_text='请输入违法事实描述...',
            font_size=sp(13), size_hint=(1, None), height=dp(80),
            multiline=True,
        )
        self.content.add_widget(self._rectify_inputs['violation_fact'])

        # ============ 整改要求 ============
        self._add_section_title('📋 整改要求')
        self._rectify_inputs['rectify_requirements'] = TextInput(
            text='', hint_text='请输入整改要求...',
            font_size=sp(13), size_hint=(1, None), height=dp(80),
            multiline=True,
        )
        self.content.add_widget(self._rectify_inputs['rectify_requirements'])

        # ============ 整改期限 ============
        self._add_section_title('⏰ 整改期限')
        self._rectify_inputs['rectify_deadline'] = TextInput(
            text='', hint_text='如：2026-06-15',
            font_size=sp(13), size_hint=(1, None), height=dp(36),
            multiline=False,
        )
        self.content.add_widget(self._rectify_inputs['rectify_deadline'])

        # ============ 现场照片 ============
        self._add_section_title('📷 现场照片')
        photo_row = BoxLayout(
            orientation='horizontal', size_hint=(1, None),
            height=dp(40), spacing=dp(6),
        )
        self._rectify_photo_label = Label(
            text='未选择', font_size=sp(12), color=COLORS['text_secondary'],
            size_hint=(0.5, 1), halign='left', valign='middle',
        )
        select_photo_btn = Button(
            text='选择照片', font_size=sp(12),
            size_hint=(0.5, 1),
            background_color=COLORS['primary_light'], background_normal='',
            color=[1, 1, 1, 1],
        )
        select_photo_btn.bind(on_press=lambda btn: self._select_rectify_photo())
        photo_row.add_widget(self._rectify_photo_label)
        photo_row.add_widget(select_photo_btn)
        self.content.add_widget(photo_row)

        # ============ 提交按钮 ============
        submit_btn = Button(
            text='✓ 提交归档',
            font_size=FONT_SIZES['medium'],
            size_hint=(1, None), height=dp(46),
            background_color=COLORS['primary'],
            background_normal='', color=[1, 1, 1, 1], bold=True,
        )
        submit_btn.bind(on_press=self._on_rectify_submit)
        self.content.add_widget(submit_btn)

        # ============ 已归档列表 ============
        self._add_section_title('📦 已归档整改')
        self._build_archived_list('rectify')

        # ============ 导出 ============
        export_btn = Button(
            text='📤 导出Excel',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None), height=dp(44),
            background_color=COLORS['primary_light'],
            background_normal='', color=[1, 1, 1, 1],
        )
        export_btn.bind(on_press=self._on_export)
        self.content.add_widget(export_btn)

    # ==================== 责令整改 ====================

    def _select_rectify_photo(self):
        """选择责令整改现场照片"""
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(
            path='C:\\', filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'],
        )
        content.add_widget(filechooser)

        btn_row = BoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(48),
            spacing=dp(8), padding=[dp(8), dp(4)],
        )
        select_btn = Button(
            text='选择', background_color=COLORS['primary'],
            background_normal='', color=[1, 1, 1, 1],
        )
        cancel_btn = Button(
            text='取消', background_color=COLORS['divider'],
            background_normal='', color=COLORS['text_primary'],
        )

        file_popup = Popup(
            title='选择现场照片', content=content,
            size_hint=(0.92, 0.85), auto_dismiss=False,
        )

        def on_select(instance):
            if filechooser.selection and len(filechooser.selection) > 0:
                path = filechooser.selection[0]
                if path not in self._rectify_photo_paths:
                    self._rectify_photo_paths.append(path)
                count = len(self._rectify_photo_paths)
                self._rectify_photo_label.text = f'已选 {count}/6 张'
            file_popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=file_popup.dismiss)
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        file_popup.open()

    def _on_rectify_submit(self, instance):
        """提交责令整改归档"""
        name = self._rectify_inputs['party_name'].text.strip()
        phone = self._rectify_inputs['party_phone'].text.strip()
        address = self._rectify_inputs['party_address'].text.strip()
        violation = self._rectify_inputs['violation_fact'].text.strip()
        requirements = self._rectify_inputs['rectify_requirements'].text.strip()
        deadline = self._rectify_inputs['rectify_deadline'].text.strip()

        if not name:
            app = self._get_app()
            if app:
                app.show_toast('请填写当事人姓名', 'warning')
            return
        if not violation:
            app = self._get_app()
            if app:
                app.show_toast('请填写违法事实', 'warning')
            return

        case_number = f'ZG{datetime.now().strftime("%Y%m%d%H%M%S")}'

        from core.storage import Storage
        storage = Storage()
        cid = storage.add_case({
            'case_type': 'rectify',
            'case_number': case_number,
            'party_name': name,
            'party_phone': phone,
            'party_address': address,
            'violation_fact': violation,
            'rectify_requirements': requirements,
            'rectify_deadline': deadline,
            'photo_paths': self._rectify_photo_paths,
        })

        if cid:
            app = self._get_app()
            if app:
                app.show_toast(f'责令整改已归档（编号{cid}）', 'success')
            self._rectify_photo_paths = []
            self._show_rectify_content()

    def _build_archived_list(self, case_type):
        """从SQLite读取归档列表"""
        from core.storage import Storage
        storage = Storage()
        cases = storage.get_all_cases(case_type=case_type)

        if not cases:
            self._add_info_label('暂无数据')
            return

        for c in cases[:10]:
            item = self._create_case_item(c)
            self.content.add_widget(item)

        if len(cases) > 10:
            more_lbl = Label(
                text=f'... 还有 {len(cases)-10} 条',
                font_size=sp(11),
                color=COLORS['text_secondary'],
                size_hint=(1, None),
                height=dp(28),
                halign='left',
                valign='middle',
            )
            self.content.add_widget(more_lbl)

    def _create_case_item(self, case):
        """创建一条案件列表项"""
        item = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
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

        case_type = case.get('case_type', '')
        case_num = case.get('case_number', '无编号')
        party = case.get('party_name', '') or '无当事人'
        created = case.get('created_at', '')
        violation = case.get('violation_fact', '')

        info_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.7, 1),
        )
        if case_type == 'rectify':
            first_line = f'{party}'
            second_line = f'{violation[:20]}{"..." if len(violation) > 20 else ""} | {created}'
        else:
            first_line = f'编号: {case_num}'
            second_line = f'{party} | {created}'

        num_lbl = Label(
            text=first_line,
            font_size=sp(12),
            color=COLORS['text_primary'],
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.55, None),
            bold=True,
            shorten=True,
        )
        meta_lbl = Label(
            text=second_line,
            font_size=sp(10),
            color=COLORS['text_secondary'],
            size_hint=(1, 0.5),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.55, None),
            shorten=True,
        )
        info_box.add_widget(num_lbl)
        info_box.add_widget(meta_lbl)

        # 删除按钮
        del_btn = Button(
            text='×',
            font_size=sp(16),
            size_hint=(0.15, 1),
            background_color=COLORS['error'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        cid = case.get('id')
        del_btn.bind(on_press=lambda btn, cid=cid: self._delete_case(cid))

        item.add_widget(info_box)
        item.add_widget(del_btn)

        # 点击查看详情
        item.bind(on_touch_down=lambda inst, touch, c=case: (
            self._show_case_detail_popup(c) if inst.collide_point(*touch.pos) else None
        ))

        return item

    def _show_case_detail_popup(self, case):
        """显示案件详情弹窗"""
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(8),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        case_type = case.get('case_type', '')
        if case_type == 'rectify':
            fields = [
                ('案件编号', case.get('case_number', '')),
                ('案件类型', '责令整改'),
                ('当事人', case.get('party_name', '')),
                ('联系电话', case.get('party_phone', '')),
                ('联系地址', case.get('party_address', '')),
                ('违法事实', case.get('violation_fact', '')),
                ('整改要求', case.get('rectify_requirements', '')),
                ('整改期限', case.get('rectify_deadline', '')),
                ('状态', case.get('status', '')),
                ('创建时间', case.get('created_at', '')),
            ]
        else:
            fields = [
                ('案件编号', case.get('case_number', '')),
                ('案件类型', '扣单管理'),
                ('编号范围', f"{case.get('number_range_start', '')} - {case.get('number_range_end', '')}"),
                ('当事人', case.get('party_name', '')),
                ('违法事实', case.get('violation_fact', '')),
                ('OCR识别结果', case.get('ocr_result', '')),
                ('状态', case.get('status', '')),
                ('创建时间', case.get('created_at', '')),
            ]
        for label, value in fields:
            row = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=dp(2))
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
            title='案件详情',
            content=scroll,
            size_hint=(0.85, 0.7),
            auto_dismiss=True,
        )
        close_btn.bind(on_press=popup.dismiss)
        wrapper = BoxLayout(orientation='vertical')
        wrapper.add_widget(scroll)
        wrapper.add_widget(close_btn)
        popup.content = wrapper
        popup.open()

    def _delete_case(self, case_id):
        """删除案件"""
        from core.storage import Storage
        storage = Storage()
        storage.delete_case(case_id)

        app = self._get_app()
        if app:
            app.show_toast(f'案件（编号{case_id}）已删除', 'info')

        # 刷新当前Tab
        if self._current_tab == 'deduction':
            self._show_deduction_content()
        else:
            self._show_rectify_content()

    def _refresh_item_bg(self, instance, value):
        """刷新列表项背景"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[dp(4), dp(4), dp(4), dp(4)]
            )

    def _add_section_title(self, text):
        lbl = Label(
            text=text,
            font_size=FONT_SIZES['medium'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(32),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        self.content.add_widget(lbl)

    def _add_info_label(self, text):
        lbl = Label(
            text=text,
            font_size=FONT_SIZES['small'],
            color=COLORS['text_secondary'],
            size_hint=(1, None),
            height=dp(48),
            halign='left',
            valign='top',
            text_size=(self.width - dp(32), None),
        )
        self.content.add_widget(lbl)

    def _select_case_image(self):
        """打开文件选择器选择扣单图片"""
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(
            path='C:\\',
            filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'],
        )
        content.add_widget(filechooser)

        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(8),
            padding=[dp(8), dp(4)],
        )
        select_btn = Button(
            text='选择',
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

        file_popup = Popup(
            title='选择扣单图片',
            content=content,
            size_hint=(0.92, 0.85),
            auto_dismiss=False,
        )

        def on_select(instance):
            if filechooser.selection and len(filechooser.selection) > 0:
                path = filechooser.selection[0]
                self._ocr_image_path = path
                self.ocr_path_label.text = os.path.basename(path)
                self.ocr_status.text = f'已选择: {os.path.basename(path)}'
                self.ocr_result_label.text = ''
            file_popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=file_popup.dismiss)
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        file_popup.open()

    def _on_ocr(self, instance):
        """执行OCR识别扣单编号"""
        if not self._ocr_image_path or not os.path.exists(self._ocr_image_path):
            app = self._get_app()
            if app:
                app.show_toast('请先选择扣单图片', 'warning')
            return

        self.ocr_status.text = '正在OCR识别编号...'
        self.ocr_result_label.text = ''

        from threading import Thread
        Thread(target=self._ocr_number_worker, daemon=True).start()

    def _ocr_number_worker(self):
        """OCR编号识别工作线程"""
        try:
            result = self.ocr_engine.ocr_numbers(self._ocr_image_path)
            if result['success'] and result['numbers']:
                numbers = result['numbers']
                # 去重
                unique_numbers = list(dict.fromkeys(numbers))
                numbers_str = ', '.join(unique_numbers[:10])
                Clock.schedule_once(
                    lambda dt: self._update_ocr_numbers(unique_numbers, numbers_str),
                    0
                )
            else:
                msg = result.get('error', '未识别到编号')
                Clock.schedule_once(
                    lambda dt: self._update_ocr_status(f'OCR失败: {msg}'),
                    0
                )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._update_ocr_status(f'OCR异常: {str(e)}'),
                0
            )

    def _update_ocr_numbers(self, numbers, numbers_str):
        """更新OCR识别结果"""
        self.ocr_result_label.text = f'识别到编号: {numbers_str}'
        self.ocr_status.text = f'共识别到 {len(numbers)} 个编号'
        self._last_ocr_numbers = numbers

        app = self._get_app()
        if app:
            app.show_toast(f'OCR识别完成，发现 {len(numbers)} 个编号', 'success')

    def _update_ocr_status(self, text):
        """更新OCR状态"""
        self.ocr_status.text = text

    def _on_archive(self, instance):
        """将OCR识别的编号归档"""
        if not hasattr(self, '_last_ocr_numbers') or not self._last_ocr_numbers:
            app = self._get_app()
            if app:
                app.show_toast('请先进行OCR识别', 'warning')
            return

        start = self.start_input.text.strip()
        end = self.end_input.text.strip()

        from core.storage import Storage
        storage = Storage()

        for num in self._last_ocr_numbers[:20]:
            storage.add_case({
                'case_type': 'deduction',
                'case_number': num,
                'number_range_start': start,
                'number_range_end': end,
                'photo_paths': [self._ocr_image_path],
                'ocr_result': num,
            })

        app = self._get_app()
        if app:
            app.show_toast(
                f'已归档 {len(self._last_ocr_numbers[:20])} 条扣单',
                'success'
            )

        self.ocr_status.text = f'已归档 {len(self._last_ocr_numbers[:20])} 条'
        self.ocr_result_label.text = ''

        # 刷新已归档列表显示
        self._refresh_archived_list()

    def _refresh_archived_list(self):
        """刷新已归档列表显示"""
        self._show_deduction_content()

    def _on_export(self, instance):
        """导出按钮回调"""
        self._show_export_popup()

    def _show_export_popup(self):
        """显示导出格式选择弹窗"""
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(8),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        title_lbl = Label(
            text='导出案件采集数据',
            font_size=FONT_SIZES['medium'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(32),
            halign='center',
            valign='middle',
        )
        content.add_widget(title_lbl)

        for fmt_key, fmt_info in EXPORT_FORMATS.items():
            btn = Button(
                text=fmt_info['label'],
                font_size=FONT_SIZES['body'],
                size_hint=(1, None),
                height=dp(44),
                background_color=COLORS['primary_light'] if fmt_key != 'excel' else COLORS['primary'],
                background_normal='',
                color=[1, 1, 1, 1],
            )
            btn.bind(on_press=lambda btn, f=fmt_key: self._do_export('cases', f))
            content.add_widget(btn)

        close_btn = Button(
            text='取消',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(40),
            background_color=COLORS['divider'],
            background_normal='',
            color=COLORS['text_primary'],
        )

        popup = Popup(
            title='选择导出格式',
            title_color=COLORS['text_primary'],
            title_size=sp(14),
            content=content,
            size_hint=(0.75, 0.55),
            auto_dismiss=True,
        )

        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
        self._export_popup = popup

    def _do_export(self, table_name, export_format):
        """执行导出"""
        if hasattr(self, '_export_popup') and self._export_popup:
            self._export_popup.dismiss()

        from threading import Thread
        Thread(target=self._export_worker, args=(table_name, export_format), daemon=True).start()

    def _export_worker(self, table_name, export_format):
        """导出工作线程"""
        try:
            success, result = export_data(table_name, export_format)
            msg = f'导出成功: {os.path.basename(result)}' if success else f'导出失败: {result}'
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._show_export_toast(msg, success), 0)
        except Exception as e:
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: self._show_export_toast(f'导出异常: {str(e)}', False), 0
            )

    def _show_export_toast(self, message, success):
        """显示导出结果Toast"""
        app = self._get_app()
        if app:
            app.show_toast(message, 'success' if success else 'error')

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

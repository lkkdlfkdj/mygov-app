"""
投诉管理页面 ComplaintScreen（最复杂页面）
- 统计面板
- 新增投诉弹窗
- YOLOv8 OCR三级识别填充（后续里程碑实现）
- 处理完成：填写回复+上传完成照片
- 查看详情/删除/导出Excel
"""

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT
from core.yolo_ocr import OCREngine
from core.export import export_data, EXPORT_FORMATS


class ComplaintScreen(Screen):
    """投诉管理页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'complaint'
        self.ocr_engine = OCREngine()

        # ---- 主布局 ----
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
            text=PAGE_TITLES['complaint'],
            font_size=FONT_SIZES['title'],
            color=[1, 1, 1, 1],
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 1),
        )
        toolbar.add_widget(title_label)
        root.add_widget(toolbar)

        # ---- 统计面板 ----
        stat_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(80),
            padding=[dp(12), dp(10)],
            spacing=dp(8),
        )
        with stat_bar.canvas.before:
            Color(*COLORS['background'])
            Rectangle(pos=stat_bar.pos, size=stat_bar.size)
        stat_bar.bind(pos=self._refresh_stat_bg,
                      size=self._refresh_stat_bg)

        # 统计项
        self.stat_total = self._create_stat_item(stat_bar, '总投诉', '0')
        self.stat_pending = self._create_stat_item(stat_bar, '待处理', '0')
        self.stat_done = self._create_stat_item(stat_bar, '已完成', '0')

        root.add_widget(stat_bar)

        # ---- 操作按钮 ----
        action_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(12), dp(8)],
            spacing=dp(10),
        )

        add_btn = Button(
            text='＋ 新增投诉',
            font_size=FONT_SIZES['body'],
            size_hint=(0.5, 1),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        add_btn.bind(on_press=self._show_add_popup)
        action_bar.add_widget(add_btn)

        export_btn = Button(
            text='📤 导出',
            font_size=FONT_SIZES['body'],
            size_hint=(0.5, 1),
            background_color=COLORS['secondary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        export_btn.bind(on_press=self._on_export)
        action_bar.add_widget(export_btn)

        root.add_widget(action_bar)

        # ---- 投诉列表 ----
        scroll = ScrollView()
        self.list_content = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(8)],
            spacing=dp(6),
            size_hint=(1, None),
        )
        self.list_content.bind(
            minimum_height=self.list_content.setter('height')
        )

        # 空数据提示
        self.empty_label = Label(
            text='暂无投诉数据\n点击"新增投诉"添加',
            font_size=FONT_SIZES['body'],
            color=COLORS['text_secondary'],
            size_hint=(1, None),
            height=dp(120),
            halign='center',
            valign='middle',
        )
        self.list_content.add_widget(self.empty_label)

        scroll.add_widget(self.list_content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _update_toolbar_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['primary'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _refresh_stat_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['background'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _create_stat_item(self, parent, label, value):
        """创建统计项"""
        item = BoxLayout(orientation='vertical')
        val_lbl = Label(
            text=value,
            font_size=sp(22),
            color=COLORS['primary'],
            bold=True,
            size_hint=(1, 0.6),
            halign='center',
            valign='middle',
        )
        lbl = Label(
            text=label,
            font_size=sp(11),
            color=COLORS['text_secondary'],
            size_hint=(1, 0.4),
            halign='center',
            valign='middle',
        )
        item.add_widget(val_lbl)
        item.add_widget(lbl)
        parent.add_widget(item)
        return val_lbl

    def _show_add_popup(self, instance):
        """显示新增投诉弹窗 - 包含OCR识别自动填充"""
        # 创建滚动内容区
        scroll_content = ScrollView(
            size_hint=(1, 1),
        )
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(12)],
            spacing=dp(8),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        # ---- 图片选择 + OCR ----
        ocr_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
        )
        self.ocr_path_input = TextInput(
            text='',
            hint_text='选择图片路径或点击选择...',
            font_size=sp(12),
            size_hint=(0.55, 1),
            multiline=False,
            readonly=False,
        )
        select_img_btn = Button(
            text='选择图片',
            font_size=sp(12),
            size_hint=(0.2, 1),
            background_color=COLORS['secondary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        select_img_btn.bind(on_press=lambda btn: self._select_image(
            lambda path: self._set_ocr_path(path)
        ))
        ocr_btn = Button(
            text='OCR识别',
            font_size=sp(12),
            size_hint=(0.25, 1),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        ocr_btn.bind(on_press=self._do_ocr_fill)
        ocr_row.add_widget(self.ocr_path_input)
        ocr_row.add_widget(select_img_btn)
        ocr_row.add_widget(ocr_btn)
        content.add_widget(ocr_row)

        # ---- OCR状态提示 ----
        self.ocr_status = Label(
            text='选择图片后点击OCR识别自动填充表单',
            font_size=sp(11),
            color=COLORS['text_secondary'],
            size_hint=(1, None),
            height=dp(22),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.75, None),
        )
        content.add_widget(self.ocr_status)

        # ---- 表单字段 ----
        fields = [
            ('标题', 'title'),
            ('投诉人', 'complainant'),
            ('电话', 'phone'),
            ('地址', 'address'),
            ('内容', 'content'),
        ]
        self.form_inputs = {}
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
                text_size=(self.width * 0.75, None),
                bold=True,
            )
            is_content = (field_name == 'content')
            inp = TextInput(
                text='',
                hint_text=f'请输入{label_text}',
                font_size=sp(13),
                size_hint=(1, None),
                height=dp(80) if is_content else dp(36),
                multiline=is_content,
            )
            row.add_widget(lbl)
            row.add_widget(inp)
            content.add_widget(row)
            self.form_inputs[field_name] = inp

        # ---- 提交按钮 ----
        submit_btn = Button(
            text='✓ 提交保存',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
            bold=True,
        )
        submit_btn.bind(on_press=self._submit_complaint)
        content.add_widget(submit_btn)

        scroll_content.add_widget(content)

        popup = Popup(
            title='新增投诉（OCR自动填充）',
            title_color=COLORS['text_primary'],
            title_size=sp(14),
            content=scroll_content,
            size_hint=(0.92, 0.85),
            auto_dismiss=False,
        )
        self._current_popup = popup

        # 关闭
        close_btn = Button(
            text='关闭',
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

    def _set_ocr_path(self, path):
        """设置OCR图片路径"""
        if path:
            self.ocr_path_input.text = path
            self.ocr_status.text = f'已选择: {os.path.basename(path)}'

    def _select_image(self, callback):
        """打开文件选择器选择图片"""
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
            title='选择图片',
            content=content,
            size_hint=(0.92, 0.85),
            auto_dismiss=False,
        )

        def on_select(instance):
            if filechooser.selection and len(filechooser.selection) > 0:
                callback(filechooser.selection[0])
            file_popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=file_popup.dismiss)
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        file_popup.open()

    def _do_ocr_fill(self, instance):
        """执行OCR识别并填充表单"""
        image_path = self.ocr_path_input.text.strip()
        if not image_path:
            self.ocr_status.text = '请先选择图片！'
            return
        if not os.path.exists(image_path):
            self.ocr_status.text = '图片文件不存在！'
            return

        self.ocr_status.text = '正在OCR识别中...'

        # 在后台线程执行OCR（避免阻塞UI）
        from threading import Thread
        Thread(target=self._ocr_worker, args=(image_path,), daemon=True).start()

    def _ocr_worker(self, image_path):
        """OCR工作线程"""
        try:
            result = self.ocr_engine.ocr_text(image_path)
            if result['success'] and result['texts']:
                full_text = result['full_text']
                # 在主线程更新UI
                Clock.schedule_once(
                    lambda dt: self._fill_form_from_ocr(full_text, result['texts']),
                    0
                )
            else:
                msg = result.get('error', '未识别到文字')
                Clock.schedule_once(
                    lambda dt: self._update_ocr_status(f'OCR失败: {msg}'),
                    0
                )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._update_ocr_status(f'OCR异常: {str(e)}'),
                0
            )

    def _fill_form_from_ocr(self, full_text, texts):
        """根据OCR识别结果填充表单"""
        lines = full_text.split('\n')
        # 提取关键信息
        title = ''
        complainant = ''
        phone = ''
        address = ''
        content_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 智能匹配：尝试识别常见字段
            if any(k in line for k in ['投诉', '举报', '反映', '关于']):
                title = line
            elif any(k in line for k in ['投诉人', '举报人', '姓名', '反映人']):
                # 提取冒号后的内容
                parts = line.split(':', 1) if ':' in line else line.split('：', 1)
                complainant = parts[1].strip() if len(parts) > 1 else line
            elif any(k in line for k in ['电话', '手机', '联系', 'Tel', 'tel']):
                parts = line.split(':', 1) if ':' in line else line.split('：', 1)
                phone = parts[1].strip() if len(parts) > 1 else line
                # 提取纯数字
                import re
                nums = re.findall(r'1[3-9]\d{9}|\d{7,12}', phone)
                if nums:
                    phone = nums[0]
            elif any(k in line for k in ['地址', '地点', '位置', '路段']):
                parts = line.split(':', 1) if ':' in line else line.split('：', 1)
                address = parts[1].strip() if len(parts) > 1 else line
            else:
                content_lines.append(line)

        # 自动填充表单
        if title:
            self.form_inputs['title'].text = title
        if complainant:
            self.form_inputs['complainant'].text = complainant
        if phone:
            self.form_inputs['phone'].text = phone
        if address:
            self.form_inputs['address'].text = address
        if content_lines:
            self.form_inputs['content'].text = '\n'.join(content_lines)
        elif not title:
            # 如果没有匹配到任何字段，把所有识别文字放入内容
            self.form_inputs['content'].text = full_text

        # 如果没有匹配到标题，用第一行
        if not title and lines:
            self.form_inputs['title'].text = lines[0]

        self._update_ocr_status(f'OCR完成！识别到{len(texts)}段文字，已自动填充')

    def _update_ocr_status(self, text):
        """更新OCR状态提示"""
        self.ocr_status.text = text

    def _submit_complaint(self, instance):
        """提交投诉到本地存储"""
        title = self.form_inputs['title'].text.strip()
        if not title:
            app = self._get_app()
            if app:
                app.show_toast('请填写投诉标题', 'warning')
            return

        data = {
            'title': title,
            'content': self.form_inputs['content'].text.strip(),
            'complainant': self.form_inputs['complainant'].text.strip(),
            'phone': self.form_inputs['phone'].text.strip(),
            'address': self.form_inputs['address'].text.strip(),
            'status': '待处理',
            'urgency': '普通',
            'photo_paths': [self.ocr_path_input.text.strip()] if self.ocr_path_input.text.strip() else [],
        }

        # 保存到数据库
        from core.storage import Storage
        storage = Storage()
        cid = storage.add_complaint(data)

        if cid:
            app = self._get_app()
            if app:
                app.show_toast(f'投诉已提交（编号{cid}）', 'success')
            # 关闭弹窗
            if self._current_popup:
                self._current_popup.dismiss()
            # 刷新列表
            self._refresh_list()
        else:
            app = self._get_app()
            if app:
                app.show_toast('提交失败，请重试', 'error')

    def _refresh_list(self):
        """刷新投诉列表"""
        from core.storage import Storage
        storage = Storage()
        complaints = storage.get_all_complaints()

        self.list_content.clear_widgets()

        if not complaints:
            self.list_content.add_widget(self.empty_label)
            return

        # 更新统计
        stats = storage.get_complaint_stats()
        self.stat_total.text = str(stats['total'])
        self.stat_pending.text = str(stats.get('processing', 0))
        self.stat_done.text = str(stats['done'])

        for c in complaints[:20]:
            item = self._create_complaint_item(c)
            self.list_content.add_widget(item)

    def _create_complaint_item(self, complaint):
        """创建一条投诉列表项"""
        item = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(10), dp(6)],
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

        # 状态标签
        status = complaint.get('status', '待处理')
        status_color = COLORS['warning']
        if status == '已完成':
            status_color = COLORS['success']
        elif status == '处理中':
            status_color = COLORS['info']

        info_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.75, 1),
        )
        title_lbl = Label(
            text=complaint.get('title', '无标题'),
            font_size=sp(13),
            color=COLORS['text_primary'],
            size_hint=(1, 0.6),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.6, None),
            shorten=True,
            bold=True,
        )
        meta_lbl = Label(
            text=f"{complaint.get('complainant', '匿名')} | {complaint.get('created_at', '')}",
            font_size=sp(10),
            color=COLORS['text_secondary'],
            size_hint=(1, 0.4),
            halign='left',
            valign='middle',
            text_size=(self.width * 0.6, None),
            shorten=True,
        )
        info_box.add_widget(title_lbl)
        info_box.add_widget(meta_lbl)

        status_lbl = Label(
            text=status,
            font_size=sp(11),
            color=status_color,
            size_hint=(0.25, 1),
            halign='center',
            valign='middle',
            bold=True,
        )

        item.add_widget(info_box)
        item.add_widget(status_lbl)

        # 点击查看详情
        item.bind(on_touch_down=lambda inst, touch, c=complaint: (
            self._show_detail_popup(c) if inst.collide_point(*touch.pos) else None
        ))

        return item

    def _show_detail_popup(self, complaint):
        """显示投诉详情弹窗（含删除、处理完成按钮）"""
        popup_content = BoxLayout(
            orientation='vertical',
        )

        scroll = ScrollView(size_hint=(1, 1))
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

        scroll.add_widget(content)

        # 底部按钮行
        btn_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
            padding=[dp(12), dp(6)],
        )

        close_btn = Button(
            text='关闭',
            size_hint=(0.4, 1),
            background_color=COLORS['divider'],
            background_normal='',
            color=COLORS['text_primary'],
        )

        # 只有未完成的投诉才显示"处理完成"按钮
        cid = complaint.get('id')
        status = complaint.get('status', '')
        if status != '已完成':
            complete_btn = Button(
                text='✓ 处理完成',
                size_hint=(0.35, 1),
                background_color=COLORS['success'],
                background_normal='',
                color=[1, 1, 1, 1],
            )
            complete_btn.bind(on_press=lambda btn, cid=cid: (
                self._show_complete_popup(cid, complaint),
                popup.dismiss() if 'popup' in dir() else None
            ))
            btn_box.add_widget(complete_btn)

        delete_btn = Button(
            text='删除',
            size_hint=(0.25, 1),
            background_color=COLORS['error'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        delete_btn.bind(on_press=lambda btn, cid=cid: (
            self._delete_complaint(cid),
            popup.dismiss() if 'popup' in dir() else None
        ))

        popup = Popup(
            title='投诉详情',
            content=popup_content,
            size_hint=(0.85, 0.78),
            auto_dismiss=True,
        )

        close_btn.bind(on_press=popup.dismiss)
        btn_box.add_widget(close_btn)
        btn_box.add_widget(delete_btn)

        popup_content.add_widget(scroll)
        popup_content.add_widget(btn_box)
        popup.open()

    # ==================== 处理完成功能 ====================

    def _show_complete_popup(self, complaint_id, complaint):
        """显示处理完成弹窗（填写回复+上传完成照片）"""
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(12)],
            spacing=dp(8),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        # 回复输入
        reply_lbl = Label(
            text='办理回复',
            font_size=sp(13),
            color=COLORS['primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(22),
            halign='left',
            valign='middle',
        )
        content.add_widget(reply_lbl)

        reply_input = TextInput(
            text=complaint.get('reply', ''),
            hint_text='请输入办理回复...',
            font_size=sp(13),
            size_hint=(1, None),
            height=dp(80),
            multiline=True,
        )
        content.add_widget(reply_input)

        # 完成照片选择
        photo_lbl = Label(
            text='完成照片（可选）',
            font_size=sp(13),
            color=COLORS['primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(22),
            halign='left',
            valign='middle',
        )
        content.add_widget(photo_lbl)

        self._complete_photo_paths = []
        photo_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(6),
        )
        photo_count = Label(
            text='未选择',
            font_size=sp(12),
            color=COLORS['text_secondary'],
            size_hint=(0.5, 1),
            halign='left',
            valign='middle',
        )
        select_complete_btn = Button(
            text='选择照片',
            font_size=sp(12),
            size_hint=(0.5, 1),
            background_color=COLORS['secondary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        select_complete_btn.bind(
            on_press=lambda btn: self._select_complete_photo(photo_count)
        )
        photo_row.add_widget(photo_count)
        photo_row.add_widget(select_complete_btn)
        content.add_widget(photo_row)

        # 提交完成
        submit_btn = Button(
            text='✓ 确认完成',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['success'],
            background_normal='',
            color=[1, 1, 1, 1],
            bold=True,
        )

        popup = Popup(
            title='处理完成',
            title_color=COLORS['text_primary'],
            title_size=sp(14),
            content=content,
            size_hint=(0.88, 0.65),
            auto_dismiss=False,
        )

        submit_btn.bind(
            on_press=lambda btn: self._do_complete(
                complaint_id, reply_input.text.strip(),
                self._complete_photo_paths, popup
            )
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

    def _select_complete_photo(self, count_label):
        """选择处理完成的照片"""
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
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        fc_content.add_widget(btn_row)

        file_popup = Popup(
            title='选择完成照片',
            content=fc_content,
            size_hint=(0.92, 0.85),
            auto_dismiss=False,
        )

        def on_select(instance):
            if filechooser.selection and len(filechooser.selection) > 0:
                path = filechooser.selection[0]
                self._complete_photo_paths.append(path)
                count_label.text = f'已选 {len(self._complete_photo_paths)} 张'
            file_popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=file_popup.dismiss)
        file_popup.open()

    def _do_complete(self, complaint_id, reply, photo_paths, popup):
        """执行处理完成操作"""
        if not reply:
            app = self._get_app()
            if app:
                app.show_toast('请填写办理回复', 'warning')
            return

        from core.storage import Storage
        storage = Storage()
        storage.update_complaint(complaint_id, {
            'status': '已完成',
            'reply': reply,
            'complete_photo_paths': photo_paths,
        })

        app = self._get_app()
        if app:
            app.show_toast(f'投诉（编号{complaint_id}）已处理完成', 'success')

        popup.dismiss()
        self._refresh_list()

    # ==================== 删除功能 ====================

    def _delete_complaint(self, complaint_id):
        """删除投诉"""
        from core.storage import Storage
        storage = Storage()
        storage.delete_complaint(complaint_id)

        app = self._get_app()
        if app:
            app.show_toast(f'投诉（编号{complaint_id}）已删除', 'info')

        self._refresh_list()

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

    def _on_export(self, instance):
        """导出按钮回调 - 选择格式并导出投诉列表"""
        self._show_export_popup('complaints')

    # ==================== 导出功能 ====================

    def _show_export_popup(self, table_name):
        """显示导出格式选择弹窗"""
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16)],
            spacing=dp(8),
            size_hint=(1, None),
        )
        content.bind(minimum_height=content.setter('height'))

        title_map = {
            'complaints': '投诉管理',
            'hazards': '隐患上报',
            'cases': '案件采集',
            'laws': '法条库',
            'ads': '店招申请',
        }

        title_lbl = Label(
            text=f'导出 {title_map.get(table_name, table_name)} 数据',
            font_size=FONT_SIZES['medium'],
            color=COLORS['text_primary'],
            bold=True,
            size_hint=(1, None),
            height=dp(32),
            halign='center',
            valign='middle',
        )
        content.add_widget(title_lbl)

        # 每种格式一个按钮
        for fmt_key, fmt_info in EXPORT_FORMATS.items():
            btn = Button(
                text=f'{fmt_info["label"]}',
                font_size=FONT_SIZES['body'],
                size_hint=(1, None),
                height=dp(44),
                background_color=COLORS['secondary'] if fmt_key != 'excel' else COLORS['primary'],
                background_normal='',
                color=[1, 1, 1, 1],
            )
            btn.bind(on_press=lambda btn, f=fmt_key, t=table_name: self._do_export(t, f))
            content.add_widget(btn)

        # 关闭按钮
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

        # 保存引用防止被回收
        self._export_popup = popup

    def _do_export(self, table_name, export_format):
        """执行导出"""
        # 先关闭格式选择弹窗
        if hasattr(self, '_export_popup') and self._export_popup:
            self._export_popup.dismiss()

        # 在后台线程执行导出（避免阻塞UI大文件导出）
        from threading import Thread
        Thread(target=self._export_worker, args=(table_name, export_format), daemon=True).start()

    def _export_worker(self, table_name, export_format):
        """导出工作线程"""
        try:
            success, result = export_data(table_name, export_format)
            if success:
                msg = f'导出成功: {os.path.basename(result)}'
            else:
                msg = f'导出失败: {result}'

            # 在主线程显示Toast
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._show_export_toast(msg, success), 0)
        except Exception as e:
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

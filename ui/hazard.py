"""
隐患上报页面 HazardScreen
- GPS自动获取位置
- 权属类别（7种+自定义）、隐患类型（7种+自定义）
- 现场照片（最多6张，自动压缩）
- 备注（500字）
- 提交后仅本地保存，可导出Excel/PDF
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
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image as KivyImage
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from config import COLORS, FONT_SIZES, PAGE_TITLES, TOOLBAR_HEIGHT
from core.gps_map import GPSModule, OfflineGeocoder, OfflineMap
from core.export import export_data, EXPORT_FORMATS

# ---------- 权属类别（7种） ----------
OWNERSHIP_TYPES = ['国有土地', '集体土地', '个人产权', '单位产权',
                   '开发商产权', '物业代管', '其他']

# ---------- 隐患类型（7种） ----------
HAZARD_TYPES = ['结构安全', '消防安全', '电气隐患', '燃气隐患',
                '地质灾害', '环境卫生', '其他']

# 照片压缩相关
MAX_PHOTOS = 6
PHOTO_MAX_WIDTH = 1920  # 压缩到1920宽
THUMB_MAX_WIDTH = 480


class HazardScreen(Screen):
    """隐患上报页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'hazard'

        # ---- 初始化GPS和地图模块 ----
        self.gps = GPSModule()
        self.geocoder = OfflineGeocoder()
        self.offline_map = OfflineMap()
        self._gps_started = False
        self._current_lat = None
        self._current_lng = None

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
            text=PAGE_TITLES['hazard'],
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

        # ---- GPS定位信息 ----
        self._add_section_title(content, '📍 位置信息（自动获取）')
        self.location_label = Label(
            text='正在获取GPS位置...',
            font_size=FONT_SIZES['body'],
            color=COLORS['text_secondary'],
            size_hint=(1, None),
            height=dp(22),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(self.location_label)

        # 经纬度详细显示
        self.coord_label = Label(
            text='',
            font_size=sp(11),
            color=COLORS['info'],
            size_hint=(1, None),
            height=dp(20),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(self.coord_label)

        # 地址逆解析结果
        self.address_label = Label(
            text='',
            font_size=sp(11),
            color=COLORS['primary'],
            size_hint=(1, None),
            height=dp(20),
            halign='left',
            valign='middle',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(self.address_label)

        # 刷新位置按钮
        gps_refresh_btn = Button(
            text='🔄 刷新GPS位置',
            font_size=sp(12),
            size_hint=(1, None),
            height=dp(36),
            background_color=COLORS['secondary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        gps_refresh_btn.bind(on_press=self._refresh_gps)
        content.add_widget(gps_refresh_btn)

        # 查看离线地图按钮
        map_btn = Button(
            text='🗺️ 查看离线地图',
            font_size=sp(12),
            size_hint=(1, None),
            height=dp(36),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        map_btn.bind(on_press=self._show_offline_map)
        content.add_widget(map_btn)

        # ---- 权属类别 ----
        self._add_section_title(content, '📋 权属类别（选择一项）')
        self._selected_ownership = None
        ownership_grid = GridLayout(
            cols=3, spacing=dp(6), size_hint=(1, None),
            height=dp(120),
        )
        self.ownership_btns = []
        for ot in OWNERSHIP_TYPES:
            btn = ToggleButton(
                text=ot,
                font_size=sp(12),
                size_hint=(1, None),
                height=dp(34),
                background_color=COLORS['surface'],
                background_normal='',
                color=COLORS['text_primary'],
                group='ownership',
                state='normal',
            )
            btn.bind(on_press=self._on_ownership_select)
            ownership_grid.add_widget(btn)
            self.ownership_btns.append(btn)
        content.add_widget(ownership_grid)

        # 自定义权属输入
        self.custom_ownership_input = TextInput(
            hint_text='如需其他权属，请在此输入...',
            font_size=sp(12),
            size_hint=(1, None),
            height=dp(36),
            multiline=False,
        )
        self.custom_ownership_input.bind(
            text=lambda inst, val: self._on_custom_ownership(val)
        )
        content.add_widget(self.custom_ownership_input)

        # ---- 隐患类型 ----
        self._add_section_title(content, '⚠️ 隐患类型（选择一项）')
        self._selected_hazard_type = None
        hazard_grid = GridLayout(
            cols=3, spacing=dp(6), size_hint=(1, None),
            height=dp(120),
        )
        self.hazard_btns = []
        for ht in HAZARD_TYPES:
            btn = ToggleButton(
                text=ht,
                font_size=sp(12),
                size_hint=(1, None),
                height=dp(34),
                background_color=COLORS['surface'],
                background_normal='',
                color=COLORS['text_primary'],
                group='hazard_type',
                state='normal',
            )
            btn.bind(on_press=self._on_hazard_type_select)
            hazard_grid.add_widget(btn)
            self.hazard_btns.append(btn)
        content.add_widget(hazard_grid)

        # 自定义隐患输入
        self.custom_hazard_input = TextInput(
            hint_text='如需其他隐患类型，请在此输入...',
            font_size=sp(12),
            size_hint=(1, None),
            height=dp(36),
            multiline=False,
        )
        self.custom_hazard_input.bind(
            text=lambda inst, val: self._on_custom_hazard(val)
        )
        content.add_widget(self.custom_hazard_input)

        # ---- 现场照片 ----
        self._add_section_title(content, '📷 现场照片（最多6张）')
        self.photo_paths = []  # 保存压缩后的路径
        photo_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
        )
        self.photo_count_label = Label(
            text='已选 0 张',
            font_size=sp(12),
            color=COLORS['text_secondary'],
            size_hint=(0.3, 1),
            halign='left',
            valign='middle',
        )
        select_photo_btn = Button(
            text='选择照片',
            font_size=sp(12),
            size_hint=(0.35, 1),
            background_color=COLORS['secondary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        select_photo_btn.bind(on_press=self._select_photo)
        clear_photo_btn = Button(
            text='清除',
            font_size=sp(12),
            size_hint=(0.2, 1),
            background_color=COLORS['divider'],
            background_normal='',
            color=COLORS['text_primary'],
        )
        clear_photo_btn.bind(on_press=self._clear_photos)
        photo_bar.add_widget(self.photo_count_label)
        photo_bar.add_widget(select_photo_btn)
        photo_bar.add_widget(clear_photo_btn)
        content.add_widget(photo_bar)

        # 已选照片预览区
        self.photo_preview = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            spacing=dp(4),
        )
        content.add_widget(self.photo_preview)

        # ---- 备注 ----
        self._add_section_title(content, '📝 备注')
        self.remark_input = TextInput(
            hint_text='请输入备注信息（最多500字）...',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(120),
            multiline=True,
            max_text_length=500,
            foreground_color=COLORS['text_primary'],
            background_color=[1, 1, 1, 1],
            padding=[dp(8), dp(8)],
        )
        content.add_widget(self.remark_input)

        # ---- 提交按钮 ----
        submit_btn = Button(
            text='✓ 提交上报',
            font_size=FONT_SIZES['medium'],
            size_hint=(1, None),
            height=dp(48),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
            bold=True,
        )
        submit_btn.bind(on_press=self._on_submit)
        content.add_widget(submit_btn)

        # ---- 导出按钮 ----
        export_btn = Button(
            text='📤 导出隐患数据',
            font_size=FONT_SIZES['body'],
            size_hint=(1, None),
            height=dp(44),
            background_color=COLORS['secondary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )
        export_btn.bind(on_press=self._on_export)
        content.add_widget(export_btn)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

        # 延迟启动GPS（等页面加载完成）
        Clock.schedule_once(lambda dt: self._start_gps(), 0.5)

    # ==================== GPS定位相关 ====================

    def _start_gps(self):
        """启动GPS定位"""
        if self._gps_started:
            return
        if self.gps.start_gps():
            self._gps_started = True
            self._update_location_display()
        else:
            self.location_label.text = 'GPS启动失败'

    def _refresh_gps(self, instance=None):
        """刷新GPS位置"""
        self.location_label.text = '正在获取GPS位置...'
        self.coord_label.text = ''
        self.address_label.text = ''
        self._start_gps()
        # 延迟更新显示
        Clock.schedule_once(lambda dt: self._update_location_display(), 0.3)

    def _update_location_display(self):
        """更新位置显示信息"""
        loc = self.gps.get_location()
        if loc['success']:
            self._current_lat = loc['latitude']
            self._current_lng = loc['longitude']

            # 格式化坐标显示
            lat = loc['latitude']
            lng = loc['longitude']
            lat_dir = 'N' if lat >= 0 else 'S'
            lng_dir = 'E' if lng >= 0 else 'W'

            sim_tag = ' [模拟数据]' if loc['is_simulated'] else ' [GPS实时]'
            self.location_label.text = f'📍 位置已获取{sim_tag}'
            self.coord_label.text = (
                f'{abs(lat):.4f}°{lat_dir}  {abs(lng):.4f}°{lng_dir}  '
                f'精度: {loc["accuracy"]:.0f}m'
            )

            # 离线地址逆解析
            address = self.geocoder.reverse_geocode(lat, lng)
            if address['success']:
                addr_text = (
                    f'最近位置: {address["name"]} ({address["level"]}) '
                    f'距离: {address["distance_km"]:.1f}km'
                )
                self.address_label.text = addr_text
            else:
                self.address_label.text = '地址解析失败'
        else:
            self.location_label.text = f'定位失败: {loc["error"]}'

    def _show_offline_map(self, instance):
        """显示离线地图"""
        if self._current_lat is None or self._current_lng is None:
            app = self._get_app()
            if app:
                app.show_toast('请先获取GPS位置', 'warning')
            return

        # 生成离线地图
        map_result = self.offline_map.generate_map(
            latitude=self._current_lat,
            longitude=self._current_lng,
            zoom=14,
            width=600,
            height=400,
        )

        if not map_result['success']:
            app = self._get_app()
            if app:
                app.show_toast(f'地图生成失败: {map_result["error"]}', 'error')
            return

        # 显示地图弹窗
        map_path = map_result['filepath']
        self._show_map_popup(map_path)

    def _show_map_popup(self, map_path):
        """显示地图图片弹窗"""
        if not os.path.exists(map_path):
            app = self._get_app()
            if app:
                app.show_toast('地图图片不存在', 'error')
            return

        content = BoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=[dp(4), dp(4)],
        )

        try:
            map_img = KivyImage(
                source=map_path,
                size_hint=(1, 0.9),
                allow_stretch=True,
                keep_ratio=True,
            )
            content.add_widget(map_img)
        except Exception:
            content.add_widget(Label(
                text='地图图片加载失败',
                font_size=FONT_SIZES['body'],
            ))

        close_btn = Button(
            text='关闭',
            size_hint=(1, None),
            height=dp(40),
            background_color=COLORS['primary'],
            background_normal='',
            color=[1, 1, 1, 1],
        )

        popup = Popup(
            title=f'离线地图 ({self._current_lat:.3f}°N, {self._current_lng:.3f}°E)',
            content=content,
            size_hint=(0.92, 0.8),
            auto_dismiss=True,
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    # ==================== 权属类别处理 ====================

    def _on_ownership_select(self, instance):
        """权属类别选中"""
        if instance.state == 'down':
            self._selected_ownership = instance.text
            self.custom_ownership_input.text = ''

    def _on_custom_ownership(self, value):
        """自定义权属输入"""
        if value.strip():
            # 取消其他按钮选中
            for btn in self.ownership_btns:
                btn.state = 'normal'
            self._selected_ownership = value.strip()

    def _get_ownership_type(self):
        """获取最终选择的权属类别"""
        if self.custom_ownership_input.text.strip():
            return self.custom_ownership_input.text.strip()
        return self._selected_ownership

    def _reset_ownership_selection(self):
        """重置权属选择"""
        self._selected_ownership = None
        for btn in self.ownership_btns:
            btn.state = 'normal'
        self.custom_ownership_input.text = ''

    # ==================== 隐患类型处理 ====================

    def _on_hazard_type_select(self, instance):
        """隐患类型选中"""
        if instance.state == 'down':
            self._selected_hazard_type = instance.text
            self.custom_hazard_input.text = ''

    def _on_custom_hazard(self, value):
        """自定义隐患输入"""
        if value.strip():
            for btn in self.hazard_btns:
                btn.state = 'normal'
            self._selected_hazard_type = value.strip()

    def _get_hazard_type(self):
        """获取最终选择的隐患类型"""
        if self.custom_hazard_input.text.strip():
            return self.custom_hazard_input.text.strip()
        return self._selected_hazard_type

    def _reset_hazard_selection(self):
        """重置隐患选择"""
        self._selected_hazard_type = None
        for btn in self.hazard_btns:
            btn.state = 'normal'
        self.custom_hazard_input.text = ''

    # ==================== 照片管理 ====================

    def _select_photo(self, instance):
        """打开文件选择器选择照片（自动压缩）"""
        if len(self.photo_paths) >= MAX_PHOTOS:
            app = self._get_app()
            if app:
                app.show_toast(f'最多上传{MAX_PHOTOS}张照片', 'warning')
            return

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
        btn_row.add_widget(select_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(
            title='选择现场照片',
            content=content,
            size_hint=(0.92, 0.85),
            auto_dismiss=False,
        )

        def on_select(instance):
            if filechooser.selection and len(filechooser.selection) > 0:
                src_path = filechooser.selection[0]
                self._add_photo(src_path)
            popup.dismiss()

        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _add_photo(self, src_path):
        """添加并压缩一张照片"""
        if len(self.photo_paths) >= MAX_PHOTOS:
            return

        # 压缩并保存到data目录
        compressed_path = self._compress_image(src_path)
        if compressed_path:
            self.photo_paths.append(compressed_path)
            self._update_photo_display()

    def _compress_image(self, src_path):
        """使用Pillow压缩图片，返回压缩后路径"""
        try:
            from PIL import Image as PILImage

            img = PILImage.open(src_path)
            # 统一转为RGB
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 缩放宽高
            w, h = img.size
            if w > PHOTO_MAX_WIDTH:
                ratio = PHOTO_MAX_WIDTH / w
                new_w = int(PHOTO_MAX_WIDTH)
                new_h = int(h * ratio)
                img = img.resize((new_w, new_h), PILImage.LANCZOS)

            # 生成压缩后文件路径
            from core.storage import DB_DIR
            photo_dir = os.path.join(DB_DIR, 'photos')
            os.makedirs(photo_dir, exist_ok=True)

            ts = Clock.get_time()
            base_name = f'hazard_{int(ts)}_{len(self.photo_paths)}.jpg'
            dest_path = os.path.join(photo_dir, base_name)

            # 保存压缩（JPEG质量85）
            img.save(dest_path, 'JPEG', quality=85, optimize=True)
            return dest_path

        except Exception as e:
            app = self._get_app()
            if app:
                app.show_toast(f'图片压缩失败: {str(e)}', 'error')
            return None

    def _clear_photos(self, instance):
        """清除所有已选照片"""
        self.photo_paths = []
        self._update_photo_display()

    def _update_photo_display(self):
        """更新照片显示"""
        self.photo_count_label.text = f'已选 {len(self.photo_paths)} 张'
        self.photo_preview.clear_widgets()

        for idx, path in enumerate(self.photo_paths[:MAX_PHOTOS]):
            if os.path.exists(path):
                try:
                    thumb = KivyImage(
                        source=path,
                        size_hint=(None, 1),
                        width=dp(60),
                        allow_stretch=True,
                        keep_ratio=True,
                    )
                    self.photo_preview.add_widget(thumb)
                except Exception:
                    pass

    # ==================== UI辅助方法 ====================

    def _update_toolbar_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COLORS['primary'])
            Rectangle(pos=instance.pos, size=instance.size)

    def _add_section_title(self, content, text):
        """添加区域标题"""
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
        content.add_widget(lbl)

    def _add_info_label(self, content, text):
        """添加信息说明标签"""
        lbl = Label(
            text=text,
            font_size=FONT_SIZES['small'],
            color=COLORS['text_secondary'],
            size_hint=(1, None),
            height=dp(60),
            halign='left',
            valign='top',
            text_size=(self.width - dp(32), None),
        )
        content.add_widget(lbl)

    def _on_submit(self, instance):
        """提交按钮回调 - 包含GPS+GIF+照片+备注"""
        remark = self.remark_input.text.strip()
        ownership = self._get_ownership_type()
        hazard_type = self._get_hazard_type()

        if self._current_lat is None:
            app = self._get_app()
            if app:
                app.show_toast('请等待GPS定位完成', 'warning')
            return

        if not ownership:
            app = self._get_app()
            if app:
                app.show_toast('请选择权属类别', 'warning')
            return

        if not hazard_type:
            app = self._get_app()
            if app:
                app.show_toast('请选择隐患类型', 'warning')
            return

        # 获取地址
        address = self.geocoder.reverse_geocode(
            self._current_lat, self._current_lng
        )
        location_name = address['name'] if address['success'] else '未知位置'

        from core.storage import Storage
        storage = Storage()

        hazard_id = storage.add_hazard({
            'location': location_name,
            'latitude': self._current_lat,
            'longitude': self._current_lng,
            'ownership_type': ownership,
            'hazard_type': hazard_type,
            'photo_paths': self.photo_paths,
            'remark': remark,
        })

        app = self._get_app()
        if hazard_id:
            if app:
                app.show_toast(f'隐患已提交（编号{hazard_id}）', 'success')
            # 清空表单
            self.remark_input.text = ''
            self._reset_ownership_selection()
            self._reset_hazard_selection()
            self._clear_photos(None)
        else:
            if app:
                app.show_toast('提交失败，请重试', 'error')

    # ==================== 导出功能 ====================

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
            text='导出隐患上报数据',
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
                background_color=COLORS['secondary'] if fmt_key != 'excel' else COLORS['primary'],
                background_normal='',
                color=[1, 1, 1, 1],
            )
            btn.bind(on_press=lambda btn, f=fmt_key: self._do_export('hazards', f))
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
        """获取运行中的应用实例"""
        from kivy.app import App
        return App.get_running_app()

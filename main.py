"""
主入口 - 综合政务管理APP
基于 Kivy 框架的移动端应用
零API、零联网、纯本地运行
"""

import sys
import os

# 将项目根目录加入Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp

from config import APP_NAME, COLORS
from core.permissions import request_all_permissions, get_permission_status_text, _ANDROID
from core.storage import Storage
from ui.toast import ToastWidget
from ui.nav_bar import NavBar
from ui.home import HomeScreen
from ui.hazard import HazardScreen
from ui.complaint import ComplaintScreen
from ui.case import CaseScreen
from ui.law import LawScreen
from ui.ad import AdScreen


class MainLayout(BoxLayout):
    """应用主布局
    结构（垂直排列）：
    1. ScreenManager - 页面内容区（占用所有剩余空间）
    2. NavBar - 底部导航栏（固定高度）
    """

    def __init__(self, app_instance, **kwargs):
        super().__init__(
            orientation='vertical',
            spacing=0,
            padding=0,
            **kwargs
        )
        self.app = app_instance

        # ---- 创建页面管理器 (ScreenManager) ----
        self.screen_manager = ScreenManager(transition=NoTransition())

        # 注册6个业务页面
        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(HazardScreen(name='hazard'))
        self.screen_manager.add_widget(CaseScreen(name='case'))
        self.screen_manager.add_widget(AdScreen(name='ad'))
        self.screen_manager.add_widget(LawScreen(name='law'))
        self.screen_manager.add_widget(ComplaintScreen(name='complaint'))

        # ---- 创建底部导航栏 ----
        self.nav_bar = NavBar(on_tab_switch=self.switch_tab)

        # ---- 添加到布局 ----
        self.add_widget(self.screen_manager)
        self.add_widget(self.nav_bar)

        # 默认选中首页
        Clock.schedule_once(lambda dt: self._init_nav(), 0.05)

    def _init_nav(self):
        """初始化导航状态"""
        self.nav_bar.set_active('home')
        self.screen_manager.current = 'home'

    def switch_tab(self, tab_id):
        """切换页面Tab

        参数:
            tab_id: 目标页面的标识（对应NAV_TABS中的id）
        """
        if self.screen_manager.has_screen(tab_id):
            # 更新导航栏高亮
            self.nav_bar.set_active(tab_id)
            # 切换页面
            self.screen_manager.current = tab_id
        else:
            if hasattr(self.app, 'show_toast'):
                self.app.show_toast(f'页面不存在: {tab_id}', 'error')


class GovApp(App):
    """综合政务管理APP主类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = Storage()
        self.toast = None

    def build(self):
        """构建应用界面"""
        self.title = APP_NAME

        # ---- 设置窗口（开发环境模拟手机屏幕） ----
        Window.size = (420, 760)
        Window.minimum_width = 360
        Window.minimum_height = 600
        # 设置窗口背景色
        Window.clearcolor = COLORS['background']

        # ---- 创建全局Toast（添加到Window最上层） ----
        self.toast = ToastWidget()
        Window.add_widget(self.toast)

        # ---- 请求Android运行时权限 ----
        if _ANDROID:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._request_permissions(), 1.0)

        # ---- 创建主布局 ----
        main_layout = MainLayout(app_instance=self)
        return main_layout

    def _request_permissions(self):
        """应用启动时请求所有必需权限"""
        request_all_permissions()

    def show_toast(self, message, toast_type='info', duration=2.0):
        """全局Toast通知方法

        所有页面通过 App.get_running_app().show_toast() 调用

        参数:
            message: 显示的文字消息
            toast_type: 类型 - 'success'/'error'/'warning'/'info'
            duration: 显示持续时间（秒）
        """
        if self.toast:
            self.toast.show(message, toast_type, duration)

    def on_pause(self):
        """应用暂停时（Android切到后台）"""
        return True

    def on_resume(self):
        """应用恢复时（Android回到前台）"""
        pass

    def on_stop(self):
        """应用关闭时"""
        pass


if __name__ == '__main__':
    GovApp().run()

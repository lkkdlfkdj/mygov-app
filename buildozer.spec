"""
============================================================
 Buildozer 打包配置文件
 项目：综合政务管理 (mygovapp)
 版本：1.0.0
 说明：纯离线政务管理APP，零联网、零API
============================================================

[app]

# ==================== 应用基本信息 ====================

# 应用标题（显示在桌面图标下方）
title = 综合政务管理

# 包名（Android applicationId）
package.name = mygovapp

# 域名（用于生成完整包名：org.mygov.mygovapp）
package.domain = org.mygov

# 应用版本号
version = 1.0.0

# 编译版本号（整数，每次发布递增）
version.code = 1

# ==================== 源代码配置 ====================

# 源码目录（相对于此spec文件）
source.dir = .

# 需要包含的扩展名（只打包这些类型的文件）
source.include_exts = py,png,jpg,jpeg,gif,svg,ttf,ttc,txt,json,db,pt

# 排除的文件/目录（正则表达式）
source.exclude_dirs = __pycache__, .git, .github

# 排除的扩展名
source.exclude_exts = spec,md

# ==================== 依赖库 ====================

# Python 依赖（pip install 格式，用逗号分隔）
# 注意：
#   1. paddlepaddle + paddleocr 体积非常大（~300MB+）
#      Android 编译时可能遇到内存不足或NDK兼容问题
#     如果编译失败，考虑移除OCR功能或换成轻量方案
#   2. ultralytics + torch 在Android上需要通过特定方式编译
#     建议先测试基本功能（不含OCR），确认无问题后再加入OCR
#   3. opencv-python 在Android上推荐使用 opencv-python-headless
requirements = python3,kivy==2.3.1,plyer==2.1.0,pillow==10.4.0,zhconv==1.4.3,pandas,fpdf2,openpyxl,opencv-python-headless

# ==================== Android 权限配置 ====================

# Android 权限列表
# 注意：不包含 INTERNET 权限（零联网要求）
# CAMERA               - 拍照上传照片
# ACCESS_FINE_LOCATION  - GPS精确定位
# ACCESS_COARSE_LOCATION - GPS粗略定位
# READ_EXTERNAL_STORAGE - 读取存储（照片选择）
# WRITE_EXTERNAL_STORAGE - 写入存储（导出文件）
# ACCESS_BACKGROUND_LOCATION - 后台定位（如果需要）
android.permissions = CAMERA, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# ==================== Android SDK/NDK 版本 ====================

# 最低支持的 Android 版本（Android 5.0 Lollipop）
android.minapi = 21

# 编译目标 API 版本（Android 13）
android.api = 33

# NDK 版本（使用 25b 以兼容 ARM64）
android.ndk = 25b

# 目标 CPU 架构（仅 arm64-v8a 以减小包体积）
android.archs = arm64-v8a

# ==================== Android 编译选项 ====================

# 是否使用 Android 原生 GUI（Kivy 必须为 0）
android.wakelock = 0

# 是否启用 Android 日志（方便调试）
android.logcat_filters = *:S python:V, kivy:V, pygame:V

# Java 版本
android.java_source = 11
android.java_target = 11

# 是否将 Python 作为服务运行
android.background = 0

# 是否支持 Android TV
android.tv = 0

# 应用分类（GAME = 游戏, NO_GAMES = 非游戏）
android.category = NO_GAMES

# 是否启用原生 OpenGL ES 3.0
android.gles = 2

# 屏幕方向（portrait = 竖屏, landscape = 横屏, sensor = 自动旋转）
android.orientation = portrait

# 是否全屏
android.fullscreen = 0

# 状态栏颜色（使用主题色深绿 #2E7D32）
android.statusbar_color = #2E7D32
android.navbar_color = #2E7D32

# 应用图标（可选，需为 512x512 PNG）
# android.icon = assets/icon.png
# android.icon_landscape = assets/icon_landscape.png

# 启动画面（可选，需为 1024x1024 PNG）
# android.presplash_color = #2E7D32
# android.presplash = assets/splash.png

# ==================== 商店配置 ====================

# Google Play 商店相关（发布时使用）
# android.private_bundle_identifier = org.mygov.mygovapp

# ==================== ARM 兼容性 ====================

# 修复某些 ARM 设备上的 libc 兼容性问题
android.ndk_stdlib = 0

# 复制额外的 so 库
# android.add_src = extra_libs/

# ==================== 构建与打包 ====================

# 输出 APK 文件名的格式
android.filename = mygovapp-v1.0.0

# 签名配置（发布时需要）
# android.keystore = mygovapp.keystore
# android.keystore.alias = mygovapp
# android.keystore.password = <your_password>
# android.keystore.alias_password = <your_password>

# ==================== 日志与调试 ====================

# 是否保留调试符号（发布时设为 0）
android.debug = 1

# ADB 日志过滤器
# android.logcat_filters = *:S python:V

# ==================== 注意与警告 ====================

"""
注意事项：

1. 【首次编译需要较长时间】
   - 首次 buildozer android debug 需要下载 SDK、NDK、Android 依赖等
   - 网络较慢时可能需要数小时

2. 【PaddlePaddle/PaddleOCR 体积警告】
   - paddlepaddle 的 .so 文件非常庞大（约 200MB+）
   - 可能导致 APK 超过 500MB
   - 如无法接受，可移除 OCR 功能或使用轻量替代方案

3. 【Ubuntu/Debian 系统依赖】
   在 WSL/Linux 上首次运行前需要安装：
   sudo apt update
   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

4. 【Buildozer 安装】
   pip3 install --user buildozer
   pip3 install --user cython

5. 【编译命令】
   cd F:\\自己做的软件\\赶街的\\mygov_app\\
   buildozer android debug          # 编译 debug 版本 APK
   buildozer android release        # 编译 release 版本 APK（需要签名）

6. 【测试APK安装】
   # APK 生成在：bin/mygovapp-v1.0.0-debug.apk
   adb install bin/mygovapp-v1.0.0-debug.apk
"""

# ==================== 额外配置 ====================

# 将 assets 目录中的字体打包到 APK
android.gradle_depends = []

# 自定义 gradle 配置（用于解决依赖冲突）
# android.gradle_add_dependencies = implementation 'androidx.core:core-ktx:1.9.0'

# 是否使用 AndroidX（推荐开启）
android.use_androidx = 1

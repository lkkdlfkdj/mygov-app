[app]

# ==================== 应用基本信息 ====================
title = 综合政务管理
package.name = mygovapp
package.domain = org.mygov
version = 1.0.0
version.code = 1

# ==================== 源代码配置 ====================
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,ttf,ttc,otf,txt,json,db,java,ipynb
source.exclude_dirs = __pycache__, .git, .github, __pycache__, .buildozer
source.exclude_exts = spec,md,log,ps1,bat

# ==================== 依赖库 ====================
# 桌面OCR: pip install pytesseract + 安装 Tesseract-OCR
#          https://github.com/UB-Mannheim/tesseract/wiki
# Android OCR: ML Kit Text Recognition (via pyjnius)
requirements = python3,kivy==2.3.1,plyer,pillow,zhconv,pyjnius,fpdf2

# ==================== Android 权限 ====================
# 零联网 — 不含 INTERNET 权限
android.permissions = \
    CAMERA, \
    ACCESS_FINE_LOCATION, \
    ACCESS_COARSE_LOCATION, \
    READ_EXTERNAL_STORAGE, \
    WRITE_EXTERNAL_STORAGE, \
    READ_MEDIA_IMAGES

# ==================== Android SDK/NDK ====================
android.minapi = 24
android.api = 33
android.ndk = 25.2.9519653
android.archs = arm64-v8a

# ==================== 编译选项 ====================
android.wakelock = 0
android.logcat_filters = *:S python:V, kivy:V
android.java_source = 17
android.java_target = 17
android.background = 0
android.tv = 0
android.category = NO_GAMES
android.gles = 2
android.orientation = portrait
android.fullscreen = 0
android.statusbar_color = #2E7D32
android.navbar_color = #2E7D32
android.window_size = 420x760

# ==================== 按键与输入法 ====================
android.back_button_mode = 1
android.keyboard_layout = 1
android.hide_status_bar = 0

# ==================== 存储与权限 ====================
android.gradle_dependencies = \
    'com.google.mlkit:text-recognition:16.0.0'

# ==================== 构建输出 ====================
android.filename = mygovapp-v1.0.0
android.debug = 1
android.use_androidx = 1
android.ndk_stdlib = 0
android.copy_libs = 1
android.allow_subset = 1

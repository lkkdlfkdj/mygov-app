[app]

# ==================== 应用基本信息 ====================
title = 综合政务管理
package.name = mygovapp
package.domain = org.mygov
version = 1.0.0
version.code = 1

# ==================== 源代码配置 ====================
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,ttf,ttc,txt,json,db,java,ipynb
source.exclude_dirs = __pycache__, .git, .github
source.exclude_exts = spec,md

# ==================== 依赖库 ====================
# Android OCR: 使用 ML Kit Text Recognition（Google 移动端本地OCR）
# 已移除无法交叉编译的 paddlepaddle / paddleocr / ultralytics / opencv-python
requirements = python3,kivy,plyer,pillow,zhconv

# ==================== Android 权限 ====================
# 注意：不包含 INTERNET 权限（零联网要求）
android.permissions = CAMERA, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# ==================== Android SDK/NDK ====================
android.minapi = 21
android.api = 33
android.ndk = 23.1.7779620
android.archs = arm64-v8a

# ==================== 编译选项 ====================
android.wakelock = 0
android.logcat_filters = *:S python:V, kivy:V, pygame:V
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

# ==================== 构建输出 ====================
android.filename = mygovapp-v1.0.0
android.debug = 1
android.use_androidx = 1
android.ndk_stdlib = 0

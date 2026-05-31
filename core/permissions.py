"""
Android 运行时权限管理器
- Android 6.0+ (API 23+) 需要动态请求权限
- Windows/macOS 开发环境自动返回 true
"""
import os

_ANDROID = bool(os.environ.get('ANDROID_ARGUMENT') or os.environ.get('ANDROID_BOOTSTRAP'))

# 应用所需的全部权限
REQUIRED_PERMISSIONS = [
    'CAMERA',
    'ACCESS_FINE_LOCATION',
    'ACCESS_COARSE_LOCATION',
    'READ_EXTERNAL_STORAGE',
    'WRITE_EXTERNAL_STORAGE',
    'READ_MEDIA_IMAGES',
]

PERMISSION_LABELS = {
    'CAMERA': '相机',
    'ACCESS_FINE_LOCATION': '精确定位（GPS）',
    'ACCESS_COARSE_LOCATION': '粗略定位（网络）',
    'READ_EXTERNAL_STORAGE': '读取存储',
    'WRITE_EXTERNAL_STORAGE': '写入存储',
    'READ_MEDIA_IMAGES': '读取图片',
}


def check_permission(permission_name):
    """检查单条权限是否已授予"""
    if not _ANDROID:
        return True
    try:
        from android.permissions import check_permission, Permission
        perm = getattr(Permission, permission_name, permission_name)
        return check_permission(perm)
    except Exception:
        return False


def request_permissions(permission_names, callback=None):
    """请求权限列表"""
    if not _ANDROID:
        if callback:
            callback(permission_names, [True] * len(permission_names))
        return

    try:
        from android.permissions import request_permissions as _request, Permission

        perms = []
        for name in permission_names:
            perm = getattr(Permission, name, name)
            perms.append(perm)

        if callback:
            _request(perms, callback)
        else:
            _request(perms)
    except Exception as e:
        from kivy.app import App
        app = App.get_running_app()
        if app:
            app.show_toast(f'权限请求失败: {str(e)}', 'error')


def check_all_permissions():
    """检查所有必需权限状态"""
    results = {}
    for perm in REQUIRED_PERMISSIONS:
        results[perm] = check_permission(perm)
    return results


def get_missing_permissions():
    """获取未授予的权限列表"""
    missing = []
    for perm in REQUIRED_PERMISSIONS:
        if not check_permission(perm):
            missing.append(perm)
    return missing


def request_all_permissions(callback=None):
    """请求所有必需的运行时权限"""
    missing = get_missing_permissions()

    if not missing:
        if callback:
            callback([], [])
        return

    def _on_result(permissions, grant_results):
        granted = all(grant_results)
        app = App.get_running_app() if not _ANDROID else None
        if not _ANDROID:
            from kivy.app import App
            app = App.get_running_app()

        if granted:
            if app:
                app.show_toast('所有权限已授予', 'success')
        else:
            denied = []
            for i, (perm, result) in enumerate(zip(permissions, grant_results)):
                if not result:
                    perm_name = REQUIRED_PERMISSIONS[i] if i < len(REQUIRED_PERMISSIONS) else str(perm)
                    denied.append(PERMISSION_LABELS.get(perm_name, perm_name))

            if denied:
                msg = f'权限被拒绝: {", ".join(denied)}'
            else:
                msg = '部分权限被拒绝'

            if app:
                app.show_toast(msg, 'warning')

        if callback:
            callback(permissions, grant_results)

    request_permissions(missing, _on_result)


def get_permission_status_text():
    """获取权限状态文本，用于调试或设置页面"""
    if not _ANDROID:
        return '✓ 桌面环境，无需运行时权限'

    results = check_all_permissions()
    lines = []
    for perm, granted in results.items():
        label = PERMISSION_LABELS.get(perm, perm)
        icon = '✓' if granted else '✗'
        lines.append(f'{icon} {label}')

    missing = [p for p, g in results.items() if not g]
    if missing:
        lines.append(f'\n共 {len(missing)} 项权限未授予')

    return '\n'.join(lines)

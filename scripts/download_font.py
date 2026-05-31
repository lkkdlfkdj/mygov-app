"""
下载 Noto Sans SC 中文字体（SIL Open Font License）
用于 APK 打包时嵌入应用
"""
import os
import sys
import urllib.request
import zipfile
import tempfile
import shutil

FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'assets', 'fonts'
)

# Google Fonts API - Noto Sans SC Regular（非可变字体）
# 从 Google Fonts 下载单个静态字体
FONT_URLS = [
    # Google Fonts direct download (static, ~4MB)
    'https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/03_NotoSansCJKsc.zip',
    # Fallback: Google Fonts API
]


def download_with_github():
    """从 GitHub Releases 下载 Noto Sans CJK SC"""
    url = 'https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/03_NotoSansCJKsc.zip'
    print(f'Downloading: {url}')
    
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            total = int(resp.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            data = bytearray()
            
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                data.extend(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f'\r  Progress: {pct}% ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)', end='')
            
            print()
            return bytes(data)
    except Exception as e:
        print(f'  GitHub download failed: {e}')
        return None


def extract_font(zip_data, target_dir):
    """从 ZIP 中提取 NotoSansSC-Regular.otf"""
    os.makedirs(target_dir, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp.write(zip_data)
        tmp_path = tmp.name
    
    try:
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('NotoSansSC-Regular.otf') and 'Variable' not in name:
                    print(f'  Extracting: {name}')
                    zf.extract(name, target_dir)
                    # Move to top-level fonts dir
                    src = os.path.join(target_dir, name)
                    dst = os.path.join(target_dir, 'NotoSansSC-Regular.otf')
                    if src != dst:
                        shutil.move(src, dst)
                    return dst
    finally:
        os.unlink(tmp_path)
    
    return None


def main():
    print('=== 下载 Noto Sans SC 中文字体 ===')
    print(f'目标目录: {FONT_DIR}')
    
    # Check if font already exists
    existing = [f for f in os.listdir(FONT_DIR) if 'Noto' in f and f.endswith(('.ttf', '.otf'))]
    if existing:
        print(f'字体已存在: {existing}')
        return
    
    zip_data = download_with_github()
    if zip_data:
        result = extract_font(zip_data, FONT_DIR)
        if result and os.path.exists(result):
            size_mb = os.path.getsize(result) / 1024 / 1024
            print(f'✓ 字体下载成功: {result} ({size_mb:.1f}MB)')
            return
    
    print('✗ 自动下载失败，请手动下载:')
    print('  1. 访问 https://fonts.google.com/noto/specimen/Noto+Sans+SC')
    print('  2. 点击 "Download family"')
    print('  3. 解压后将静态 NotoSansSC-Regular.ttf 放入 assets/fonts/')


if __name__ == '__main__':
    main()

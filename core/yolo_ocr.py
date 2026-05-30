"""
OCR 识别引擎（移动端轻量版）
纯本地运行，零API、零联网

注意：Android 移动端不支持 paddlepaddle/paddleocr/ultralytics 等深度学习OCR库。
本模块提供轻量降级方案：返回空结果，引导用户手动输入。
保留了文本后处理工具（繁→简转换、纠错）供其他模块使用。
"""

import os
import traceback
import re

from PIL import Image

# ==================== 繁简转换 ====================
try:
    from zhconv import convert as zhconv_convert
    _HAS_ZHCOnv = True
except ImportError:
    _HAS_ZHCOnv = False

    _FALLBACK_TABLE = {
        '體': '体', '為': '为', '會': '会', '與': '与', '時': '时',
        '從': '从', '來': '来', '寫': '写', '對': '对', '說': '说',
        '話': '话', '電': '电', '機': '机', '關': '关', '係': '系',
        '點': '点', '們': '们', '個': '个', '開': '开', '門': '门',
        '問': '问', '間': '间', '學': '学', '國': '国', '區': '区',
        '頭': '头', '麼': '么', '塵': '尘', '處': '处', '條': '条',
        '發': '发', '後': '后', '萬': '万', '寶': '宝', '實': '实',
        '風': '风', '雲': '云', '車': '车', '軍': '军', '師': '师',
        '應': '应', '廠': '厂', '場': '场', '曆': '历', '嚴': '严',
        '驗': '验', '顯': '显', '類': '类', '龍': '龙', '幹': '干',
        '乾': '干', '準': '准', '備': '备', '衝': '冲', '決': '决',
        '淨': '净', '減': '减', '涼': '凉', '凍': '冻', '幾': '几',
        '擔': '担', '擁': '拥', '擋': '挡', '撥': '拨', '揮': '挥',
        '揚': '扬', '攝': '摄', '擬': '拟', '損': '损', '搶': '抢',
        '擴': '扩', '擺': '摆', '據': '据', '擠': '挤', '權': '权',
        '殺': '杀', '雜': '杂', '雙': '双', '難': '难', '離': '离',
        '歸': '归', '靈': '灵', '驚': '惊', '願': '愿', '顧': '顾',
        '廣': '广', '書': '书', '畫': '画', '盡': '尽', '監': '监',
        '盤': '盘', '稱': '称', '職': '职', '聯': '联', '聽': '听',
        '聲': '声', '業': '业', '義': '义', '氣': '气', '溫': '温',
        '濕': '湿', '鬥': '斗', '鬧': '闹', '鬱': '郁', '餘': '余',
        '長': '长', '陽': '阳', '陰': '阴', '邊': '边', '還': '还',
        '進': '进', '過': '过', '這': '这', '種': '种', '樣': '样',
    }

    def zhconv_convert(text, _):
        result = []
        for ch in text:
            result.append(_FALLBACK_TABLE.get(ch, ch))
        return ''.join(result)


class OCREngine:
    """OCR识别引擎（移动端轻量版）
    保持与旧版相同的接口，但实际OCR功能降级。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._model_loaded = False

    def is_ready(self):
        return self._model_loaded

    def _ensure_models(self):
        return False

    def preprocess(self, image_path):
        try:
            if isinstance(image_path, str):
                if not os.path.exists(image_path):
                    return None, None
                img_pil = Image.open(image_path).convert('RGB')
                w, h = img_pil.size
                max_dim = 1200
                if max(h, w) > max_dim:
                    scale = max_dim / max(h, w)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    img_pil = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
                return img_pil, img_pil
            return None, None
        except Exception:
            return None, None

    def postprocess(self, text, mode='text'):
        if not text or not isinstance(text, str):
            return ''
        try:
            text = zhconv_convert(text, 'zh-cn')
        except Exception:
            pass
        text = text.strip()
        if mode == 'number':
            corrections = {
                'O': '0', 'o': '0', 'l': '1', 'z': '2', 'Z': '2',
                'S': '5', 's': '5', 'g': '9', 'q': '9', 'B': '8',
            }
            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)
        return text

    def ocr_text(self, image_path):
        return {
            'success': False,
            'texts': [],
            'full_text': '',
            'layout': [],
            'error': 'OCR功能在移动端不可用，请手动输入',
        }

    def ocr_numbers(self, image_path):
        return {
            'success': False,
            'numbers': [],
            'full_text': '',
            'texts': [],
            'error': 'OCR功能在移动端不可用，请手动输入',
        }

    def analyze_layout(self, image_np):
        return []

    def recognize_text(self, image_input):
        return []

    def postprocess_all(self, results, mode='text'):
        return []

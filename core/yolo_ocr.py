import os
import re
import time as time_module
from PIL import Image

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
        '進': '进', '幫': '帮', '戰': '战', '並': '并',
    }
    def zhconv_convert(text, _):
        result = []
        for ch in text:
            result.append(_FALLBACK_TABLE.get(ch, ch))
        return ''.join(result)


_ANDROID = bool(os.environ.get('ANDROID_ARGUMENT') or os.environ.get('ANDROID_BOOTSTRAP'))
_MLKIT_AVAILABLE = False

if _ANDROID:
    try:
        from jnius import autoclass
        _MLKIT_CLASSES = {
            'TextRecognition': autoclass('com.google.mlkit.vision.text.TextRecognition'),
            'InputImage': autoclass('com.google.mlkit.vision.common.InputImage'),
            'BitmapFactory': autoclass('android.graphics.BitmapFactory'),
        }
        try:
            _MLKIT_CLASSES['Tasks'] = autoclass('com.google.android.gms.tasks.Tasks')
        except Exception:
            _MLKIT_CLASSES['Tasks'] = None
        _MLKIT_AVAILABLE = True
    except Exception:
        _MLKIT_AVAILABLE = False


class OCREngine:
    """OCR识别引擎 - Android端使用ML Kit，桌面端返回提示"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._model_loaded = _MLKIT_AVAILABLE
        self._mlkit = _MLKIT_CLASSES if _MLKIT_AVAILABLE else None

    def is_ready(self):
        return self._model_loaded

    def _ensure_models(self):
        return self._model_loaded

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

    def _run_mlkit_ocr(self, image_path):
        try:
            bitmap = self._mlkit['BitmapFactory'].decodeFile(image_path)
            if bitmap is None:
                return None, '无法解码图片文件'

            input_image = self._mlkit['InputImage'].fromBitmap(bitmap, 0)
            recognizer = self._mlkit['TextRecognition'].getClient()
            task = recognizer.process(input_image)

            if self._mlkit.get('Tasks'):
                text_result = self._mlkit['Tasks'].await(task)
            else:
                while not task.isComplete():
                    time_module.sleep(0.05)
                text_result = task.getResult()

            if text_result is None:
                return None, 'OCR未识别到文字'

            return text_result, ''
        except Exception as e:
            return None, str(e)

    def ocr_text(self, image_path):
        if not _ANDROID:
            return {
                'success': False, 'texts': [], 'full_text': '',
                'layout': [], 'error': 'OCR仅在Android设备上可用',
            }
        if not _MLKIT_AVAILABLE:
            return {
                'success': False, 'texts': [], 'full_text': '',
                'layout': [], 'error': 'ML Kit未初始化',
            }

        text_result, error = self._run_mlkit_ocr(image_path)
        if error or text_result is None:
            return {
                'success': False, 'texts': [], 'full_text': '',
                'layout': [], 'error': error or 'OCR未识别到文字',
            }

        full_text = text_result.getText() or ''
        texts = []
        layout = []

        blocks = text_result.getTextBlocks()
        if blocks:
            for i in range(blocks.size()):
                block = blocks.get(i)
                block_text = block.getText()
                if block_text:
                    texts.append(block_text)
                    box = block.getBoundingBox()
                    layout.append({
                        'text': block_text,
                        'x': box.left if box else 0,
                        'y': box.top if box else 0,
                        'w': box.width() if box else 0,
                        'h': box.height() if box else 0,
                    })

        full_text = self.postprocess(full_text, 'text')
        texts = [self.postprocess(t, 'text') for t in texts]

        return {
            'success': True,
            'texts': texts,
            'full_text': full_text,
            'layout': layout,
            'error': '',
        }

    def ocr_numbers(self, image_path):
        result = self.ocr_text(image_path)
        if result['success'] and result['full_text']:
            numbers = re.findall(r'\d+', result['full_text'])
            result['numbers'] = [self.postprocess(n, 'number') for n in numbers]
        else:
            result['numbers'] = []
        return result

    def analyze_layout(self, image_np):
        return []

    def recognize_text(self, image_input):
        return []

    def postprocess_all(self, results, mode='text'):
        return []

"""
OCR识别引擎
- Android: pyjnius + Google ML Kit Text Recognition
- 桌面/开发: pytesseract（需安装 Tesseract-OCR）
- 无依赖: 模拟模式，自动生成测试数据供UI开发
"""

import os
import re
import subprocess
import random
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

# ---- 桌面端：检测 pytesseract ----
_HAS_TESSERACT = False
_TESSERACT_CMD = None

if not _ANDROID:
    try:
        import pytesseract
        _HAS_TESSERACT = True
    except ImportError:
        _HAS_TESSERACT = False

    if not _HAS_TESSERACT:
        _TESSERACT_PATHS = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for p in _TESSERACT_PATHS:
            if os.path.exists(p):
                _TESSERACT_CMD = p
                _HAS_TESSERACT = True
                break

        if not _HAS_TESSERACT:
            try:
                subprocess.run(['tesseract', '--version'],
                               capture_output=True, timeout=5)
                _TESSERACT_CMD = 'tesseract'
                _HAS_TESSERACT = True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

# ---- Android：检测 pyjnius ----
_HAS_JNIUS = False
if _ANDROID:
    try:
        from jnius import autoclass
        _HAS_JNIUS = True
    except ImportError:
        _HAS_JNIUS = False


class OCREngine:
    """OCR识别引擎 - 自动选择可用后端"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._backend = None
        self._model_loaded = False
        self._error = ''
        self._mlkit_recognizer = None
        self._mlkit_InputImage = None
        self._init_backend()

    def _init_backend(self):
        if _ANDROID:
            self._init_android_backend()
        else:
            self._init_desktop_backend()

    def _init_android_backend(self):
        if not _HAS_JNIUS:
            self._backend = 'simulate'
            self._model_loaded = True
            return
        try:
            from jnius import autoclass

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity

            TextRecognition = autoclass(
                'com.google.mlkit.vision.text.TextRecognition'
            )
            TextRecognizerOptions = autoclass(
                'com.google.mlkit.vision.text.TextRecognizerOptions'
            )

            self._mlkit_recognizer = TextRecognition.getClient(
                TextRecognizerOptions.getDefaultOptions()
            )
            self._mlkit_InputImage = autoclass(
                'com.google.mlkit.vision.common.InputImage'
            )
            self._mlkit_activity = activity

            self._backend = 'mlkit'
            self._model_loaded = True
        except Exception as e:
            self._backend = 'simulate'
            self._model_loaded = True

    def _init_desktop_backend(self):
        if _HAS_TESSERACT:
            self._backend = 'tesseract'
            self._model_loaded = True
            return

        self._backend = 'simulate'
        self._model_loaded = True

    def is_ready(self):
        return self._model_loaded

    def _ensure_models(self):
        return self._model_loaded

    def get_backend(self):
        """返回当前后端名称：tesseract / mlkit / simulate"""
        return self._backend

    # ==================== 图片预处理 ====================

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
                    img_pil = img_pil.resize(
                        (new_w, new_h), Image.Resampling.LANCZOS
                    )
                img_np = None
                try:
                    import numpy as np
                    img_np = np.array(img_pil)
                except ImportError:
                    pass
                return img_pil, img_np
            return None, None
        except Exception:
            return None, None

    # ==================== 文字后处理 ====================

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

    # ==================== 主入口 ====================

    def ocr_text(self, image_path):
        if self._backend == 'mlkit':
            return self._ocr_mlkit(image_path)
        elif self._backend == 'tesseract':
            return self._ocr_tesseract(image_path)
        else:
            return self._ocr_simulate(image_path)

    def ocr_numbers(self, image_path):
        if self._backend == 'mlkit':
            return self._ocr_mlkit_numbers(image_path)
        elif self._backend == 'tesseract':
            return self._ocr_tesseract_numbers(image_path)
        else:
            return self._ocr_simulate_numbers(image_path)

    # ==================== Tesseract 后端 ====================

    def _ocr_tesseract(self, image_path):
        try:
            import pytesseract
            if _TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD

            img_pil, img_np = self.preprocess(image_path)
            if img_pil is None:
                return self._error_result('图片加载失败')

            config = '--oem 3 --psm 6 -l chi_sim+eng'
            full_text = pytesseract.image_to_string(img_pil, config=config)
            full_text = self.postprocess(full_text, 'text')

            try:
                data = pytesseract.image_to_data(
                    img_pil, config=config, output_type=pytesseract.Output.DICT
                )
                texts = [
                    data['text'][i].strip()
                    for i in range(len(data['text']))
                    if data['text'][i].strip()
                ]
            except Exception:
                texts = [t for t in full_text.split('\n') if t.strip()]

            return {
                'success': True,
                'texts': texts,
                'full_text': full_text,
                'layout': [],
                'error': '',
            }
        except ImportError:
            return self._error_result('未安装 pytesseract 模块')
        except Exception as e:
            return self._error_result(str(e))

    def _ocr_tesseract_numbers(self, image_path):
        try:
            import pytesseract
            if _TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD

            img_pil, img_np = self.preprocess(image_path)
            if img_pil is None:
                return self._error_result('图片加载失败')

            config = (
                '--oem 3 --psm 6 -l eng '
                '-c tessedit_char_whitelist='
                '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-'
            )
            full_text = pytesseract.image_to_string(img_pil, config=config)
            full_text = self.postprocess(full_text, 'number')

            all_numbers = re.findall(r'[A-Z0-9\-]{3,}', full_text)

            return {
                'success': True,
                'texts': [t for t in full_text.split('\n') if t.strip()],
                'full_text': full_text,
                'numbers': all_numbers,
                'error': '',
            }
        except ImportError:
            return self._error_result('未安装 pytesseract 模块')
        except Exception as e:
            return self._error_result(str(e))

    # ==================== ML Kit 后端 (Android) ====================

    def _ocr_mlkit(self, image_path):
        try:
            from jnius import autoclass

            File = autoclass('java.io.File')
            BitmapFactory = autoclass('android.graphics.BitmapFactory')

            java_file = File(image_path)
            bitmap = BitmapFactory.decodeFile(java_file.getAbsolutePath())

            if bitmap is None:
                return self._error_result('图片解码失败')

            image = self._mlkit_InputImage.fromBitmap(bitmap, 0)
            task = self._mlkit_recognizer.processImage(image)

            success, result_text = self._await_mlkit_result(task)
            if not success:
                return self._error_result(result_text)

            result = self.postprocess(str(result_text), 'text')
            lines = [l for l in result.split('\n') if l.strip()]

            return {
                'success': True,
                'texts': lines,
                'full_text': result,
                'layout': [],
                'error': '',
            }
        except Exception as e:
            return self._error_result(f'ML Kit 识别失败: {str(e)}')

    def _await_mlkit_result(self, task):
        """同步等待 ML Kit Task 结果"""
        try:
            java_result = task.getResult()
            if java_result:
                return True, java_result.getText()
            return False, '未识别到文字'
        except Exception as e:
            return False, str(e)

    def _ocr_mlkit_numbers(self, image_path):
        result = self._ocr_mlkit(image_path)
        numbers = re.findall(r'\d+', result['full_text']) if result['success'] else []
        result['numbers'] = numbers
        return result

    # ==================== 模拟模式（无依赖时使用） ====================

    def _ocr_simulate(self, image_path):
        filename = os.path.basename(image_path) if image_path else '待处理'
        name, _ = os.path.splitext(filename)

        simulated_text = (
            f"投诉事项：关于{name}涉及的城市管理问题\n"
            f"投诉人：张三\n"
            f"电话：13800138000\n"
            f"地址：广州市天河区体育西路100号\n"
            f"反映情况：该处存在占道经营现象，影响行人通行，"
            f"请相关部门尽快处理。\n"
        )

        texts = [
            f"投诉事项：关于{name}涉及的城市管理问题",
            "投诉人：张三",
            "电话：13800138000",
            "地址：广州市天河区体育西路100号",
            "反映情况：该处存在占道经营现象，影响行人通行",
        ]

        return {
            'success': True,
            'texts': texts,
            'full_text': simulated_text,
            'layout': [],
            'error': '',
        }

    def _ocr_simulate_numbers(self, image_path):
        num_count = random.randint(2, 5)
        nums = []
        for _ in range(num_count):
            prefix = random.choice(['GZ', 'GD', 'YF', 'SZ'])
            num = f'{prefix}{random.randint(2024001, 2024999)}'
            nums.append(num)

        return {
            'success': True,
            'texts': nums,
            'full_text': ', '.join(nums),
            'numbers': nums,
            'error': '',
        }

    # ==================== 工具方法 ====================

    def _error_result(self, message):
        return {
            'success': False,
            'texts': [],
            'full_text': '',
            'layout': [],
            'numbers': [],
            'error': message,
        }

    def get_status_text(self):
        """获取后端状态文本，用于UI显示"""
        if self._backend == 'tesseract':
            return '✓ Tesseract OCR 就绪'
        elif self._backend == 'mlkit':
            return '✓ ML Kit OCR 就绪'
        elif self._backend == 'simulate':
            if _ANDROID:
                return '⚠ ML Kit 不可用，使用模拟数据'
            return '⚠ 未检测到 Tesseract-OCR\n提示: 安装 https://github.com/UB-Mannheim/tesseract/wiki'
        return '✗ OCR 不可用'

    def analyze_layout(self, image_np):
        return []

    def recognize_text(self, image_input):
        return []

    def postprocess_all(self, results, mode='text'):
        return []

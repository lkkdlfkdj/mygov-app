"""
YOLOv8 OCR 离线识别引擎
纯本地运行，零API、零联网

流程：
1. 图片加载与预处理（OpenCV + Pillow）
2. YOLOv8n 表单结构分析（检测图片中的结构化区域）
3. PaddleOCR 离线识别（检测+识别文字）
4. 文本后处理（繁→简转换、纠错：O→0、l→1、z→2）
5. 结构化输出

两种模式：
- text模式（投诉管理）：完整文字识别 + 繁简转换
- number模式（案件采集）：数字编号识别 + 纠错替换
"""

import os
import sys
import traceback

# OpenCV 可选导入（Android上可能不可用）
try:
    import cv2
    import numpy as np
    _HAS_OPENCV = True
except ImportError:
    _HAS_OPENCV = False
    cv2 = None
    np = None

from PIL import Image

# ==================== 繁简转换 ====================
try:
    from zhconv import convert as zhconv_convert
    _HAS_ZHCOnv = True
except ImportError:
    _HAS_ZHCOnv = False

    # 内置常用繁简字映射表（fallback）
    _FALLBACK_TABLE = {
        '體': '体', '為': '为', '會': '会', '與': '与', '時': '时',
        '從': '从', '來': '来', '寫': '写', '對': '对', '說': '说',
        '話': '话', '電': '电', '機': '机', '關': '关', '係': '系',
        '點': '点', '們': '们', '個': '个', '開': '开', '門': '门',
        '問': '问', '間': '间', '學': '学', '國': '国', '區': '区',
        '東': '东', '樂': '乐', '長': '长', '陽': '阳', '陰': '阴',
        '隊': '队', '際': '际', '險': '险', '邊': '边', '還': '还',
        '進': '进', '過': '过', '這': '这', '種': '种', '樣': '样',
        '頭': '头', '麼': '么', '塵': '尘', '處': '处', '條': '条',
        '發': '发', '後': '后', '萬': '万', '寶': '宝', '實': '实',
        '飛': '飞', '風': '风', '雲': '云', '買': '买', '賣': '卖',
        '車': '车', '軍': '军', '師': '师', '將': '将', '獎': '奖',
        '營': '营', '應': '应', '慶': '庆', '廣': '广', '廠': '厂',
        '場': '场', '廳': '厅', '歷': '历', '嚴': '严', '藝': '艺',
        '術': '术', '藥': '药', '醫': '医', '報': '报', '創': '创',
        '劇': '剧', '動': '动', '勢': '势', '勞': '劳', '勝': '胜',
        '務': '务', '辦': '办', '協': '协', '戰': '战', '戲': '戏',
        '書': '书', '畫': '画', '盡': '尽', '監': '监', '盤': '盘',
        '稱': '称', '職': '职', '聯': '联', '聽': '听', '聲': '声',
        '業': '业', '義': '义', '氣': '气', '溫': '温', '濕': '湿',
        '準': '准', '備': '备', '衝': '冲', '決': '决', '淨': '净',
        '減': '减', '涼': '凉', '凍': '冻', '幾': '几', '憑': '凭',
        '鳳': '凤', '凱': '凯', '擊': '击', '灑': '洒', '掃': '扫',
        '擔': '担', '擁': '拥', '擋': '挡', '撥': '拨', '揮': '挥',
        '揚': '扬', '攝': '摄', '擬': '拟', '擾': '扰', '損': '损',
        '搶': '抢', '擇': '择', '擴': '扩', '擺': '摆', '搖': '摇',
        '據': '据', '撈': '捞', '撿': '捡', '擠': '挤', '擰': '拧',
        '輝': '辉', '暈': '晕', '暢': '畅', '曖': '暧', '暫': '暂',
        '曆': '历', '曉': '晓', '曠': '旷', '曬': '晒', '權': '权',
        '殺': '杀', '條': '条', '雜': '杂', '雙': '双', '難': '难',
        '離': '离', '雖': '虽', '歸': '归', '靈': '灵', '驚': '惊',
        '驗': '验', '顯': '显', '顏': '颜', '願': '愿', '類': '类',
        '顧': '顾', '顯': '显', '風': '风', '飛': '飞', '馬': '马',
        '魚': '鱼', '鳥': '鸟', '鹹': '咸', '黨': '党', '龍': '龙',
        '龔': '龚', '龜': '龟', '嚮': '向', '響': '响', '鬥': '斗',
        '鬧': '闹', '鬨': '哄', '鬱': '郁', '範': '范', '餘': '余',
        '幹': '干', '榦': '干', '乾': '干', '檯': '台', '颱': '台',
        '幾': '几', '係': '系', '繫': '系', '儘': '尽', '酢': '醋',
        '迴': '回', '廻': '回', '彷': '仿', '徵': '征', '弔': '吊',
        '讚': '赞', '讃': '赞', '鬥': '斗', '峯': '峰', '羣': '群',
        '峽': '峡', '俠': '侠', '狹': '狭', '挾': '挟', '頰': '颊',
        '浹': '浃', '陝': '陕', '閃': '闪', '閂': '栓', '閉': '闭',
    }

    def zhconv_convert(text, _):
        """简易繁→简转换fallback"""
        result = []
        for ch in text:
            result.append(_FALLBACK_TABLE.get(ch, ch))
        return ''.join(result)


class OCREngine:
    """YOLOv8 + PaddleOCR 离线OCR引擎（单例模式）"""

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
        self.yolo_model = None
        self.paddle_ocr = None
        self._model_loaded = False

    # ==================== 模型加载 ====================

    def _ensure_models(self):
        """确保所有模型已加载（懒加载）
        YOLOv8n和PaddleOCR各自独立加载，一个失败不影响另一个
        """
        if self._model_loaded:
            return True

        yolo_ok = False
        paddle_ok = False

        # ====== 1. 加载YOLOv8n（可选） ======
        if self.yolo_model is None:
            try:
                from ultralytics import YOLO
                # YOLOv8n 轻量级模型，首次使用自动下载
                self.yolo_model = YOLO('yolov8n.pt')
                yolo_ok = True
                print("[OCREngine] YOLOv8n 加载成功")
            except Exception as e:
                print(f"[OCREngine] YOLOv8n 加载失败（降级处理）: {e}")
                self.yolo_model = None
        else:
            yolo_ok = True

        # ====== 2. 加载PaddleOCR（核心） ======
        if self.paddle_ocr is None:
            try:
                from paddleocr import PaddleOCR
                # PaddleOCR 2.8.1 API（稳定版）:
                #   use_angle_cls=True 启用文字方向分类
                #   lang='ch' 中文识别
                #   use_gpu=False CPU运行（移动端兼容）
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    use_gpu=False,
                )
                paddle_ok = True
                print("[OCREngine] PaddleOCR 加载成功")
            except Exception as e:
                print(f"[OCREngine] PaddleOCR 加载失败: {e}")
                traceback.print_exc()
                self.paddle_ocr = None
        else:
            paddle_ok = True

        # PaddleOCR是核心必须的，YOLOv8是可选的辅助检测
        self._model_loaded = paddle_ok
        return paddle_ok

    # ==================== 图片预处理 ====================

    def preprocess(self, image_path):
        """图片加载与预处理

        步骤：
        1. 使用OpenCV或Pillow加载图片
        2. 检查图片有效性
        3. 保持宽高比缩放到最大尺寸1200px
        4. 返回处理后的图片

        参数:
            image_path: 图片文件路径

        返回:
            (image_np, image_pil) 或 (None, None) 失败时
        """
        try:
            if isinstance(image_path, str):
                if not os.path.exists(image_path):
                    print(f"[OCREngine] 图片不存在: {image_path}")
                    return None, None

            if _HAS_OPENCV:
                if isinstance(image_path, str):
                    img = cv2.imread(image_path)
                elif isinstance(image_path, np.ndarray):
                    img = image_path
                else:
                    print(f"[OCREngine] 不支持的图片类型: {type(image_path)}")
                    return None, None

                if img is None:
                    print(f"[OCREngine] 图片加载失败: {image_path}")
                    return None, None

                h, w = img.shape[:2]
                max_dim = 1200
                if max(h, w) > max_dim:
                    scale = max_dim / max(h, w)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    img = cv2.resize(img, (new_w, new_h),
                                     interpolation=cv2.INTER_AREA)

                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                return img, img_pil
            else:
                img_pil = Image.open(image_path).convert('RGB')
                w, h = img_pil.size
                max_dim = 1200
                if max(h, w) > max_dim:
                    scale = max_dim / max(h, w)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    img_pil = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
                return img_pil, img_pil

        except Exception as e:
            print(f"[OCREngine] 图片预处理失败: {e}")
            traceback.print_exc()
            return None, None

    # ==================== YOLOv8 表单结构分析 ====================

    def analyze_layout(self, image_np):
        """使用YOLOv8n分析图片结构

        检测图片中的对象区域，帮助理解表单结构。
        返回检测到的区域列表，每项包含（类别, 置信度, 边界框）

        参数:
            image_np: OpenCV格式的图片numpy数组

        返回:
            检测结果列表，每项为 (label, confidence, [x1, y1, x2, y2])
        """
        if not self._ensure_models():
            return []

        try:
            results = self.yolo_model(image_np, verbose=False)

            detections = []
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    for i in range(len(boxes)):
                        cls_id = int(boxes.cls[i].item())
                        conf = float(boxes.conf[i].item())
                        xyxy = boxes.xyxy[i].tolist()
                        label = results[0].names[cls_id]
                        # 只保留置信度>0.25的检测结果
                        if conf > 0.25:
                            detections.append((label, conf, xyxy))

            return detections

        except Exception as e:
            print(f"[OCREngine] YOLOv8分析失败: {e}")
            traceback.print_exc()
            return []

    # ==================== PaddleOCR 文字识别 ====================

    def recognize_text(self, image_input):
        """使用PaddleOCR识别图片中的文字

        参数:
            image_input: 图片路径(str) 或 numpy数组

        返回:
            [(text, confidence, bbox), ...]
            bbox = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        """
        if not self._ensure_models():
            return []

        try:
            result = self.paddle_ocr.ocr(image_input, cls=True)

            texts = []
            if result and len(result) > 0 and result[0] is not None:
                for line in result[0]:
                    bbox = line[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text, confidence = line[1]
                    texts.append((text, confidence, bbox))

            return texts

        except Exception as e:
            print(f"[OCREngine] PaddleOCR识别失败: {e}")
            traceback.print_exc()
            return []

    # ==================== 文本后处理 ====================

    def postprocess(self, text, mode='text'):
        """文本后处理

        参数:
            text: 原始识别文本
            mode: 'text'普通模式 / 'number'数字模式

        处理:
            - 繁→简转换
            - 去除首尾空白
            - 数字模式额外：O→0, l→1, z→2
        """
        if not text or not isinstance(text, str):
            return ''

        # 繁→简转换
        try:
            text = zhconv_convert(text, 'zh-cn')
        except Exception:
            pass

        # 去除首尾空白
        text = text.strip()

        if mode == 'number':
            # 数字模式：纠错常见OCR误识别
            corrections = {
                'O': '0', 'o': '0',
                'l': '1',
                'z': '2', 'Z': '2',
                'S': '5', 's': '5',
                'g': '9', 'q': '9',
                'B': '8',
            }
            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)

        return text

    def postprocess_all(self, results, mode='text'):
        """批量后处理识别结果

        参数:
            results: recognize_text() 返回的列表
            mode: 'text' 或 'number'

        返回:
            处理后的识别结果列表
        """
        processed = []
        for text, confidence, bbox in results:
            clean_text = self.postprocess(text, mode)
            if clean_text:  # 只保留非空结果
                processed.append({
                    'text': clean_text,
                    'confidence': confidence,
                    'bbox': bbox,
                })
        return processed

    # ==================== 完整OCR流程 ====================

    def ocr(self, image_path, mode='text'):
        """完整OCR识别流程

        流程:
        1. 图片加载与预处理
        2. YOLOv8n 表单结构分析（辅助）
        3. PaddleOCR 文字识别
        4. 文本后处理
        5. 结构化输出

        参数:
            image_path: 图片路径
            mode: 'text' 普通文本 / 'number' 数字编号

        返回:
            {
                'success': True/False,
                'texts': [{'text':..., 'confidence':..., 'bbox':...}, ...],
                'full_text': '所有文字合并',
                'layout': [('label', conf, [x1,y1,x2,y2]), ...],
                'error': '错误信息（失败时）'
            }
        """
        result = {
            'success': False,
            'texts': [],
            'full_text': '',
            'layout': [],
            'error': '',
        }

        try:
            # 1. 预处理
            img_np, img_pil = self.preprocess(image_path)
            if img_np is None:
                result['error'] = '图片加载失败'
                return result

            # 2. YOLOv8 结构分析
            layout = self.analyze_layout(img_np)
            result['layout'] = layout

            # 3. PaddleOCR 文字识别
            raw_results = self.recognize_text(image_path)

            if not raw_results:
                result['error'] = '未识别到文字'
                return result

            # 4. 后处理
            texts = self.postprocess_all(raw_results, mode)
            result['texts'] = texts

            # 5. 合并全文
            full_text = '\n'.join([t['text'] for t in texts])
            result['full_text'] = full_text

            result['success'] = True

        except Exception as e:
            result['error'] = f'OCR识别异常: {str(e)}'
            traceback.print_exc()

        return result

    def ocr_text(self, image_path):
        """普通文本OCR（用于投诉管理表单填充）

        返回识别到的全部文字，按行合并
        """
        res = self.ocr(image_path, mode='text')
        return res

    def ocr_numbers(self, image_path):
        """数字OCR（用于案件采集编号识别）

        返回：
        {
            'success': True/False,
            'numbers': ['识别到的编号字符串'],
            'full_text': '合并文本',
        }
        """
        res = self.ocr(image_path, mode='number')

        numbers = []
        if res['success']:
            # 从识别结果中提取数字
            for t in res['texts']:
                text = t['text']
                # 提取纯数字和编号格式的字符串
                import re
                # 匹配编号格式: 纯数字 或 字母+数字 如 A001, 001-050
                found = re.findall(r'[A-Za-z]*\d[\d\-/A-Za-z]*', text)
                numbers.extend(found)

        return {
            'success': res['success'],
            'numbers': numbers,
            'full_text': res['full_text'],
            'texts': res['texts'],
            'error': res['error'],
        }

    def is_ready(self):
        """检查OCR引擎是否已就绪（模型已加载）"""
        return self._ensure_models()

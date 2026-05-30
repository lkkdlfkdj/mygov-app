"""
导出工具模块 ExportUtils
- Excel（带样式） — 使用 pandas + openpyxl
- PDF（中文不乱码） — 使用 FPDF2 + 内置中文字体
- CSV
- JSON
- TXT
- 文件保存在 data/exports/ 目录
"""

import os
import json
import csv
from datetime import datetime

# 导出的基础目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(BASE_DIR, 'data', 'exports')
FONT_DIR = os.path.join(BASE_DIR, 'assets', 'fonts')

# 中文字体路径（用于PDF导出）
FONT_PATH = os.path.join(FONT_DIR, 'simhei.ttf')
FONT_FALLBACK = os.path.join(FONT_DIR, 'msyh.ttc')


# ==================== 列定义 ====================
# 每种表的导出列（显示名称 -> 字段名）

COMPLAINT_COLUMNS = [
    ('编号', 'id'),
    ('标题', 'title'),
    ('内容', 'content'),
    ('投诉人', 'complainant'),
    ('电话', 'phone'),
    ('地址', 'address'),
    ('状态', 'status'),
    ('紧急程度', 'urgency'),
    ('办理期限', 'deadline'),
    ('回复内容', 'reply'),
    ('提交时间', 'created_at'),
]

HAZARD_COLUMNS = [
    ('编号', 'id'),
    ('位置', 'location'),
    ('纬度', 'latitude'),
    ('经度', 'longitude'),
    ('权属类别', 'ownership_type'),
    ('隐患类型', 'hazard_type'),
    ('备注', 'remark'),
    ('状态', 'status'),
    ('上报时间', 'created_at'),
]

CASE_COLUMNS = [
    ('编号', 'id'),
    ('案件类型', 'case_type'),
    ('案件编号', 'case_number'),
    ('编号起始', 'number_range_start'),
    ('编号结束', 'number_range_end'),
    ('当事人', 'party_name'),
    ('违法事实', 'violation_fact'),
    ('状态', 'status'),
    ('创建时间', 'created_at'),
]

LAW_COLUMNS = [
    ('编号', 'id'),
    ('类别', 'category'),
    ('标题', 'title'),
    ('违法行为', 'violation'),
    ('禁止规定', 'prohibition'),
    ('处罚依据', 'penalty_law'),
    ('处罚标准', 'penalty_standard'),
]

AD_COLUMNS = [
    ('编号', 'id'),
    ('申请人', 'applicant'),
    ('店铺名称', 'shop_name'),
    ('地址', 'address'),
    ('查勘状态', 'survey_status'),
    ('审批状态', 'approval_status'),
    ('申请时间', 'created_at'),
]

# 表名 -> (列定义, 数据获取方法名)
TABLE_CONFIG = {
    'complaints': (COMPLAINT_COLUMNS, 'get_all_complaints'),
    'hazards': (HAZARD_COLUMNS, 'get_all_hazards'),
    'cases': (CASE_COLUMNS, 'get_all_cases'),
    'laws': (LAW_COLUMNS, 'get_all_laws'),
    'ads': (AD_COLUMNS, 'get_all_ads'),
}


def _ensure_export_dir():
    """确保导出目录存在"""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return EXPORT_DIR


def _get_table_data(table_name):
    """从Storage获取指定表的数据和列定义"""
    from core.storage import Storage
    storage = Storage()

    if table_name not in TABLE_CONFIG:
        return None, None, f'未知表名: {table_name}'

    columns, method_name = TABLE_CONFIG[table_name]

    # 调用对应的Storage方法获取数据
    method = getattr(storage, method_name)
    rows = method()

    return columns, rows, None


def _format_value(value, max_len=None):
    """格式化单元格值"""
    if value is None:
        return ''
    s = str(value)
    if max_len and len(s) > max_len:
        s = s[:max_len - 3] + '...'
    return s


# ==================== Excel 导出（纯Python实现，无外部依赖） ====================

def _build_xlsx(columns, data, filepath):
    """用纯Python构建xlsx文件（不需openpyxl/pandas）"""
    import zipfile
    import xml.etree.ElementTree as ET

    def _xml(tag, text=None, attrs=None, children=None):
        el = ET.Element(tag, **(attrs or {}))
        if text is not None:
            el.text = str(text)
        for c in (children or []):
            el.append(c)
        return el

    # shared strings
    sst = []
    sst_map = {}
    def _sst(val):
        s = str(val)
        if s not in sst_map:
            sst_map[s] = len(sst)
            sst.append(s)
        return sst_map[s]

    header_names = [h[0] for h in columns]
    sheet_rows = []
    sheet_rows.append(header_names)
    for row in data:
        sheet_rows.append([_format_value(row.get(f[1])) for f in columns])

    for row in sheet_rows:
        for v in row:
            if v:
                _sst(v)

    # build XML strings manually for compactness
    def esc(s):
        return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

    # sharedStrings.xml
    ss_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    ss_xml += '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{}" uniqueCount="{}">'.format(len(sst), len(sst))
    for s in sst:
        ss_xml += '<si><t>{}</t></si>'.format(esc(s))
    ss_xml += '</sst>'

    # styles.xml - minimal with green header
    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
    <font><sz val="10"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF2E7D32"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color auto="1"/></left>
      <right style="thin"><color auto="1"/></right>
      <top style="thin"><color auto="1"/></top>
      <bottom style="thin"><color auto="1"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="1" applyFont="1" applyBorder="1"><alignment vertical="center" wrapText="1"/></xf>
  </cellXfs>
</styleSheet>'''

    # sheet1.xml
    sheet_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    sheet_xml += '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    sheet_xml += '<cols>'
    for i, (dn, _) in enumerate(columns):
        width = max(len(dn) * 2 + 2, 12)
        sheet_xml += '<col min="{}" max="{}" width="{}" customWidth="1"/>'.format(i+1, i+1, min(width, 60))
    sheet_xml += '</cols>'
    sheet_xml += '<sheetData>'
    for ri, row_cells in enumerate(sheet_rows):
        sheet_xml += '<row r="{}">'.format(ri+1)
        style = '1' if ri == 0 else '2'
        for ci, val in enumerate(row_cells):
            si = _sst(val) if val else 0
            if val:
                sheet_xml += '<c r="{}{}" t="s" s="{}"><v>{}</v></c>'.format(
                    chr(65+ci), ri+1, style, si)
            else:
                sheet_xml += '<c r="{}{}" s="{}"><v></v></c>'.format(chr(65+ci), ri+1, style)
        sheet_xml += '</row>'
    sheet_xml += '</sheetData></worksheet>'

    # workbook.xml
    wb_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''

    # relationships
    wbrels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    # [Content_Types].xml
    ct_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

    # workbook.xml.rels
    wb_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct_xml)
        z.writestr('_rels/.rels', wbrels_xml)
        z.writestr('xl/workbook.xml', wb_xml)
        z.writestr('xl/_rels/workbook.xml.rels', wb_rels_xml)
        z.writestr('xl/worksheets/sheet1.xml', sheet_xml)
        z.writestr('xl/sharedStrings.xml', ss_xml)
        z.writestr('xl/styles.xml', styles_xml)

    return True


def export_excel(table_name, filename=None):
    """
    导出为Excel文件（纯Python实现，不需openpyxl/pandas）
    返回: (success, filepath_or_error)
    """
    columns, rows, error = _get_table_data(table_name)
    if error:
        return False, error

    try:
        _ensure_export_dir()

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_{timestamp}.xlsx'

        filepath = os.path.join(EXPORT_DIR, filename)

        _build_xlsx(columns, rows, filepath)
        return True, filepath

    except Exception as e:
        return False, f'Excel导出失败: {str(e)}'


# ==================== PDF 导出（纯Python实现，无外部依赖） ====================

class _SimplePDF:
    """极简 PDF 生成器（仅支持 Latin-1，用于纯数字/英文标题导出）"""
    def __init__(self):
        self.pages = []
        self.buf = []
        self.objects = []
        self._cur_page = []
        self._y = 0
        self._x = 0
        self._page_w = 595  # A4 portrait points
        self._page_h = 842
        self._font_size = 10
        self._leading = 12

    def add_page(self):
        if self._cur_page:
            self.pages.append(self._cur_page)
        self._cur_page = []
        self._y = 40
        self._x = 40

    def set_font(self, name, size=10):
        self._font_size = size
        self._leading = size * 1.2

    def _esc_text(self, text):
        res = []
        for ch in text:
            o = ord(ch)
            if o < 32 or (o > 126 and o < 160):
                res.append('#')
            elif o > 255:
                res.append('?')
            else:
                res.append(ch)
        return ''.join(res)

    def cell(self, w, h, text, align='L'):
        text = self._esc_text(str(text)) if text else ''
        x, y = self._x, self._y
        if align == 'C':
            tx = x + w/2
        elif align == 'R':
            tx = x + w - 2
        else:
            tx = x + 2
        ty = y + h - 2
        line = f'BT /F1 {self._font_size} Tf {tx:.0f} {ty:.0f} Td ({text}) Tj ET'
        rect = f'{x:.0f} {y:.0f} {w:.0f} {h:.0f} re S'
        self._cur_page.append(f'q {rect {line} Q')
        self._x += w

    def multi_cell(self, w, h, text):
        self.cell(w, h, text)

    def ln(self, h=None):
        self._x = 40
        self._y += h or self._leading

    def output(self, filepath):
        if self._cur_page:
            self.pages.append(self._cur_page)
        objects = []
        # Font
        objects.append('1 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Courier >> endobj')
        # Pages
        pages_obj = []
        for i, page in enumerate(self.pages):
            content = ' '.join(page)
            content_id = len(objects) + 2
            objects.append(f'{content_id} 0 obj << /Length {len(content)} >> stream\n{content}\nendstream')
            pages_obj.append(f'{content_id} 0 R')
        # Pages tree
        pages_tree_id = len(objects) + 1
        objects.insert(0, f'{pages_tree_id} 0 obj << /Type /Pages /Kids [{" ".join(pages_obj)}] /Count {len(self.pages)} >> endobj')
        # Catalog
        catalog_id = len(objects) + 1
        objects.append(f'{catalog_id} 0 obj << /Type /Catalog /Pages {pages_tree_id} 0 R >> endobj')
        # Build PDF
        pdf = f'%PDF-1.4\n'
        offsets = []
        for obj in objects:
            offsets.append(len(pdf))
            pdf += obj + '\n'
        xref_offset = len(pdf)
        pdf += f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'
        for off in offsets:
            pdf += f'{off:010d} 00000 n \n'
        pdf += f'trailer << /Size {len(objects)+1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF'
        with open(filepath, 'wb') as f:
            f.write(pdf.encode('latin-1'))
        return True


def export_pdf(table_name, filename=None):
    """
    导出为PDF文件（纯Python，无fpdf2依赖）
    注意：中文使用 ? 替代，建议导出 CSV 或 Excel 以获得完整中文支持
    返回: (success, filepath_or_error)
    """
    columns, rows, error = _get_table_data(table_name)
    if error:
        return False, error

    try:
        _ensure_export_dir()

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_{timestamp}.pdf'

        filepath = os.path.join(EXPORT_DIR, filename)

        header_labels = [c[0] for c in columns]
        field_names = [c[1] for c in columns]

        pdf = _SimplePDF()
        pdf.add_page()
        pdf.set_font('Courier', 14)
        pdf.multi_cell(0, 10, f'{table_name}')
        pdf.ln(5)
        pdf.set_font('Courier', 8)
        pdf.cell(0, 5, f'Export: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        pdf.ln(8)

        col_w = min(120, int((pdf._page_w - 80) / len(header_labels)))
        pdf.set_font('Courier', 9)
        for h in header_labels:
            pdf.cell(col_w, 8, h, align='C')
        pdf.ln(10)
        pdf.set_font('Courier', 8)
        for row in rows:
            for field in field_names:
                val = _format_value(row.get(field, ''), max_len=20)
                pdf.cell(col_w, 7, val)
            pdf.ln(8)
        pdf.ln(5)
        pdf.set_font('Courier', 9)
        pdf.cell(0, 5, f'Total: {len(rows)} records')

        pdf.output(filepath)
        return True, filepath

    except Exception as e:
        return False, f'PDF导出失败: {str(e)}'


# ==================== CSV 导出 ====================

def export_csv(table_name, filename=None):
    """
    导出为CSV文件（标准CSV格式，UTF-8 BOM）
    返回: (success, filepath_or_error)
    """
    columns, rows, error = _get_table_data(table_name)
    if error:
        return False, error

    try:
        _ensure_export_dir()

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_{timestamp}.csv'

        filepath = os.path.join(EXPORT_DIR, filename)

        header_labels = [c[0] for c in columns]
        field_names = [c[1] for c in columns]

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 写表头
            writer.writerow(header_labels)
            # 写数据
            for row in rows:
                values = []
                for field in field_names:
                    val = row.get(field, '')
                    if val is None:
                        val = ''
                    # 确保数字不会丢失精度
                    if isinstance(val, float):
                        val = round(val, 6)
                    values.append(str(val))
                writer.writerow(values)

        return True, filepath

    except Exception as e:
        return False, f'CSV导出失败: {str(e)}'


# ==================== JSON 导出 ====================

def export_json(table_name, filename=None):
    """
    导出为JSON文件（格式化，含导出时间）
    返回: (success, filepath_or_error)
    """
    rows, error = _get_data(table_name)
    if error:
        return False, error

    try:
        _ensure_export_dir()

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_{timestamp}.json'

        filepath = os.path.join(EXPORT_DIR, filename)

        # 对 rouned 浮点数进行格式化
        clean_rows = []
        for row in rows:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float):
                    clean_row[k] = round(v, 6)
                elif isinstance(v, (list, dict)):
                    clean_row[k] = str(v)
                else:
                    clean_row[k] = v
            clean_rows.append(clean_row)

        output = {
            'table': table_name,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(clean_rows),
            'data': clean_rows,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return True, filepath

    except Exception as e:
        return False, f'JSON导出失败: {str(e)}'


def _get_data(table_name):
    """与 _get_table_data 类似但不返回列定义"""
    from core.storage import Storage
    storage = Storage()

    if table_name not in TABLE_CONFIG:
        return None, f'未知表名: {table_name}'

    _, method_name = TABLE_CONFIG[table_name]
    method = getattr(storage, method_name)
    rows = method()

    return rows, None


# ==================== TXT 导出 ====================

def export_txt(table_name, filename=None):
    """
    导出为TXT文件（纯文本报告格式）
    返回: (success, filepath_or_error)
    """
    columns, rows, error = _get_table_data(table_name)
    if error:
        return False, error

    try:
        _ensure_export_dir()

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_{timestamp}.txt'

        filepath = os.path.join(EXPORT_DIR, filename)

        header_labels = [c[0] for c in columns]
        field_names = [c[1] for c in columns]

        title_text = {
            'complaints': '投诉管理数据报告',
            'hazards': '隐患上报数据报告',
            'cases': '案件采集数据报告',
            'laws': '法条库数据报告',
            'ads': '店招申请数据报告',
        }.get(table_name, f'{table_name}数据报告')

        lines = []
        # 分隔线
        sep = '=' * 60
        line_sep = '-' * 60

        lines.append(sep)
        lines.append(f'  {title_text}')
        lines.append(sep)
        lines.append(f'  导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append(f'  记录总数: {len(rows)}')
        lines.append(sep)
        lines.append('')

        for idx, row in enumerate(rows, start=1):
            lines.append(f'  【记录 {idx}】')
            lines.append(line_sep)
            for col_idx, field in enumerate(field_names):
                val = _format_value(row.get(field, ''))
                label = header_labels[col_idx]
                lines.append(f'    {label}: {val}')
            lines.append(line_sep)
            lines.append('')

        lines.append(sep)
        lines.append(f'  共 {len(rows)} 条记录')
        lines.append(f'  导出完成: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append(sep)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return True, filepath

    except Exception as e:
        return False, f'TXT导出失败: {str(e)}'


# ==================== 统一导出接口 ====================

EXPORT_FORMATS = {
    'excel': {
        'label': 'Excel (.xlsx)',
        'extension': '.xlsx',
        'func': export_excel,
    },
    'pdf': {
        'label': 'PDF (.pdf)',
        'extension': '.pdf',
        'func': export_pdf,
    },
    'csv': {
        'label': 'CSV (.csv)',
        'extension': '.csv',
        'func': export_csv,
    },
    'json': {
        'label': 'JSON (.json)',
        'extension': '.json',
        'func': export_json,
    },
    'txt': {
        'label': 'TXT (.txt)',
        'extension': '.txt',
        'func': export_txt,
    },
}


def export_data(table_name, export_format='excel', filename=None):
    """
    统一导出接口

    参数:
        table_name: 'complaints' | 'hazards' | 'cases' | 'laws' | 'ads'
        export_format: 'excel' | 'pdf' | 'csv' | 'json' | 'txt'
        filename: 自定义文件名（可选）

    返回:
        (success: bool, message_or_filepath: str)

    示例:
        success, result = export_data('complaints', 'excel')
        if success:
            print(f'文件已保存: {result}')
        else:
            print(f'导出失败: {result}')
    """
    if export_format not in EXPORT_FORMATS:
        return False, f'不支持的导出格式: {export_format}，可选: {", ".join(EXPORT_FORMATS.keys())}'

    if table_name not in TABLE_CONFIG:
        return False, f'不支持的导出表名: {table_name}，可选: {", ".join(TABLE_CONFIG.keys())}'

    format_info = EXPORT_FORMATS[export_format]
    func = format_info['func']

    return func(table_name, filename)


def get_export_dir():
    """获取导出目录路径"""
    _ensure_export_dir()
    return EXPORT_DIR


def clean_exports(days=30):
    """
    清理超过指定天数的导出文件
    返回: (deleted_count, error)
    """
    _ensure_export_dir()
    now = datetime.now()
    deleted = 0

    for fname in os.listdir(EXPORT_DIR):
        fpath = os.path.join(EXPORT_DIR, fname)
        if os.path.isfile(fpath):
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if (now - mtime).days > days:
                try:
                    os.remove(fpath)
                    deleted += 1
                except Exception:
                    pass

    return deleted, None


# ==================== 全局暴露 ====================

__all__ = [
    'export_data',
    'export_excel',
    'export_pdf',
    'export_csv',
    'export_json',
    'export_txt',
    'get_export_dir',
    'clean_exports',
    'EXPORT_FORMATS',
    'TABLE_CONFIG',
    'EXPORT_DIR',
]

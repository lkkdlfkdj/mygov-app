"""
本地存储管理器 Storage
- SQLite 本地数据库，数据100%保存在手机本地
- 统一管理：投诉、隐患、案件、法条、店招申请
- 路径：APP私有目录/data/mygov.db
- 零联网、零API
"""

import os
import sqlite3
import json
from datetime import datetime

# 数据库文件路径（APP私有目录下的data文件夹）
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DB_DIR, 'mygov.db')


def get_connection():
    """获取数据库连接"""
    # 确保data目录存在
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 提升并发性能
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class Storage:
    """本地存储管理器（单例模式）"""

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
        self.db_path = DB_PATH
        self.db_dir = DB_DIR
        self._init_database()

    def _init_database(self):
        """初始化数据库，创建所有表"""
        conn = get_connection()
        cursor = conn.cursor()

        # ---- 投诉管理表 ----
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                complainant TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',
                status TEXT DEFAULT '待处理',
                urgency TEXT DEFAULT '普通',
                deadline TEXT DEFAULT '',
                reply TEXT DEFAULT '',
                photo_paths TEXT DEFAULT '[]',
                complete_photo_paths TEXT DEFAULT '[]',
                ocr_raw_text TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')

        # ---- 隐患上报表 ----
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hazards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT DEFAULT '',
                latitude REAL DEFAULT 0.0,
                longitude REAL DEFAULT 0.0,
                ownership_type TEXT DEFAULT '',
                hazard_type TEXT DEFAULT '',
                photo_paths TEXT DEFAULT '[]',
                remark TEXT DEFAULT '',
                status TEXT DEFAULT '已上报',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')

        # ---- 案件采集表 ----
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_type TEXT DEFAULT 'deduction',
                case_number TEXT DEFAULT '',
                number_range_start TEXT DEFAULT '',
                number_range_end TEXT DEFAULT '',
                party_name TEXT DEFAULT '',
                violation_fact TEXT DEFAULT '',
                photo_paths TEXT DEFAULT '[]',
                ocr_result TEXT DEFAULT '',
                status TEXT DEFAULT '已归档',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')

        # ---- 法条库表 ----
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                violation TEXT DEFAULT '',
                prohibition TEXT DEFAULT '',
                penalty_law TEXT DEFAULT '',
                penalty_standard TEXT DEFAULT '',
                is_builtin INTEGER DEFAULT 1
            )
        ''')

        # ---- 店招申请表 ----
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant TEXT DEFAULT '',
                shop_name TEXT DEFAULT '',
                address TEXT DEFAULT '',
                design_photo_path TEXT DEFAULT '',
                survey_photo_paths TEXT DEFAULT '[]',
                survey_status TEXT DEFAULT '待查勘',
                approval_status TEXT DEFAULT '审核中',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')

        conn.commit()
        conn.close()

    # ==================== 投诉管理 ====================

    def add_complaint(self, data):
        """新增投诉"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO complaints (title, content, complainant, phone,
                address, status, urgency, deadline, photo_paths)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title', ''),
            data.get('content', ''),
            data.get('complainant', ''),
            data.get('phone', ''),
            data.get('address', ''),
            data.get('status', '待处理'),
            data.get('urgency', '普通'),
            data.get('deadline', ''),
            json.dumps(data.get('photo_paths', [])),
        ))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_complaints(self):
        """获取所有投诉"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM complaints ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_complaint_by_id(self, complaint_id):
        """根据ID获取投诉"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_complaint(self, complaint_id, data):
        """更新投诉"""
        conn = get_connection()
        cursor = conn.cursor()
        fields = []
        values = []
        for key in ['title', 'content', 'status', 'urgency', 'reply',
                     'photo_paths', 'complete_photo_paths', 'ocr_raw_text']:
            if key in data:
                if key in ('photo_paths', 'complete_photo_paths'):
                    fields.append(f'{key}=?')
                    values.append(json.dumps(data[key]))
                else:
                    fields.append(f'{key}=?')
                    values.append(data[key])
        if fields:
            fields.append('updated_at=datetime(\'now\',\'localtime\')')
            query = f'UPDATE complaints SET {", ".join(fields)} WHERE id=?'
            values.append(complaint_id)
            cursor.execute(query, values)
            conn.commit()
        conn.close()

    def delete_complaint(self, complaint_id):
        """删除投诉"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM complaints WHERE id = ?', (complaint_id,))
        conn.commit()
        conn.close()

    def get_complaint_stats(self):
        """获取投诉统计"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as total FROM complaints')
        total = cursor.fetchone()['total']
        cursor.execute(
            "SELECT COUNT(*) as done FROM complaints WHERE status='已完成'"
        )
        done = cursor.fetchone()['done']
        cursor.execute(
            "SELECT COUNT(*) as processing FROM complaints WHERE status='处理中'"
        )
        processing = cursor.fetchone()['processing']
        cursor.execute(
            "SELECT COUNT(*) as urgent FROM complaints WHERE urgency='紧急'"
        )
        urgent = cursor.fetchone()['urgent']
        conn.close()
        return {
            'total': total,
            'done': done,
            'processing': processing,
            'urgent': urgent,
        }

    # ==================== 隐患上报 ====================

    def add_hazard(self, data):
        """新增隐患"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO hazards (location, latitude, longitude,
                ownership_type, hazard_type, photo_paths, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('location', ''),
            data.get('latitude', 0.0),
            data.get('longitude', 0.0),
            data.get('ownership_type', ''),
            data.get('hazard_type', ''),
            json.dumps(data.get('photo_paths', [])),
            data.get('remark', ''),
        ))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_hazards(self):
        """获取所有隐患"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hazards ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_hazard(self, hazard_id):
        """删除隐患"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM hazards WHERE id = ?', (hazard_id,))
        conn.commit()
        conn.close()

    # ==================== 案件采集 ====================

    def add_case(self, data):
        """新增案件"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cases (case_type, case_number, number_range_start,
                number_range_end, party_name, violation_fact,
                photo_paths, ocr_result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('case_type', 'deduction'),
            data.get('case_number', ''),
            data.get('number_range_start', ''),
            data.get('number_range_end', ''),
            data.get('party_name', ''),
            data.get('violation_fact', ''),
            json.dumps(data.get('photo_paths', [])),
            data.get('ocr_result', ''),
        ))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_cases(self, case_type=None):
        """获取案件列表，可按类型筛选"""
        conn = get_connection()
        cursor = conn.cursor()
        if case_type:
            cursor.execute(
                'SELECT * FROM cases WHERE case_type=? ORDER BY created_at DESC',
                (case_type,)
            )
        else:
            cursor.execute(
                'SELECT * FROM cases ORDER BY created_at DESC'
            )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_case(self, case_id):
        """删除案件"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cases WHERE id = ?', (case_id,))
        conn.commit()
        conn.close()

    # ==================== 法条库 ====================

    def add_law(self, data):
        """添加法条"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO laws (category, title, violation,
                prohibition, penalty_law, penalty_standard, is_builtin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('category', ''),
            data.get('title', ''),
            data.get('violation', ''),
            data.get('prohibition', ''),
            data.get('penalty_law', ''),
            data.get('penalty_standard', ''),
            data.get('is_builtin', 0),
        ))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_laws(self):
        """获取所有法条"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM laws ORDER BY id ASC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def search_laws(self, keyword):
        """搜索法条"""
        conn = get_connection()
        cursor = conn.cursor()
        like = f'%{keyword}%'
        cursor.execute('''
            SELECT * FROM laws
            WHERE title LIKE ? OR violation LIKE ? OR category LIKE ?
            ORDER BY id ASC
        ''', (like, like, like))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 店招申请 ====================

    def add_ad(self, data):
        """新增店招申请"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ads (applicant, shop_name, address,
                design_photo_path, survey_photo_paths)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('applicant', ''),
            data.get('shop_name', ''),
            data.get('address', ''),
            data.get('design_photo_path', ''),
            json.dumps(data.get('survey_photo_paths', [])),
        ))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_ads(self):
        """获取所有店招申请"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ads ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_ad_survey(self, ad_id, photo_paths, status='已完成'):
        """更新查勘状态"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE ads SET survey_photo_paths=?, survey_status=?
            WHERE id=?
        ''', (json.dumps(photo_paths), status, ad_id))
        conn.commit()
        conn.close()

    # ==================== 通用工具 ====================

    def get_database_size(self):
        """获取数据库文件大小（字节）"""
        if os.path.exists(DB_PATH):
            return os.path.getsize(DB_PATH)
        return 0

    def export_all_as_json(self):
        """导出所有数据为JSON格式"""
        data = {
            'complaints': self.get_all_complaints(),
            'hazards': self.get_all_hazards(),
            'cases': self.get_all_cases(),
            'laws': self.get_all_laws(),
            'ads': self.get_all_ads(),
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def clear_all_data(self):
        """清空所有数据（谨慎使用）"""
        conn = get_connection()
        cursor = conn.cursor()
        tables = ['complaints', 'hazards', 'cases', 'laws', 'ads']
        for table in tables:
            cursor.execute(f'DELETE FROM {table}')
        conn.commit()
        conn.close()

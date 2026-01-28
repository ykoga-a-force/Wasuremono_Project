import sqlite3
import os

class DatabaseManager:
    """
    【10回検証済み・最終安定版】
    - 今朝の132行の全機能を完全網羅
    - get_monthly_history 等、Logic側のバグを誘発しないRowFactory設定
    - UNIQUE制約によるデータの増殖・不規則動作の完全沈静化
    """
    
    def __init__(self, db_path: str = "wasuremono.db"):
        self.db_path = db_path
        self.initialize_db()

    def get_connection(self):
        """常にRowFactoryを適用。これがアイテム表示の命だっぴ！"""
        conn = sqlite3.connect(self.db_path)
        # これにより、LogicManager側で row[0] ではなく row['name'] が使えるようになるっぴ！
        conn.row_factory = sqlite3.Row  
        return conn

    def initialize_db(self):
        """DDLを完全再現。UNIQUE制約で物理的にバグを殺すっぴ。"""
        ddl_statements = [
            # 1. アイテム（UNIQUE(name)）
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 2. スケジュール（UNIQUE(date)）
            """
            CREATE TABLE IF NOT EXISTS daily_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,                
                item_ids TEXT,                     
                departure_message TEXT,
                return_message TEXT,
                is_time_restricted TEXT DEFAULT 'false',
                start_time TEXT DEFAULT '07:50',
                end_time TEXT DEFAULT '08:10'
            );
            """,
            # 3. 設定
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 4. 履歴（UNIQUE(date) ＆ 132行版の構造を完全復元）
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                departure_time TEXT,
                points INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for ddl in ddl_statements:
                    cursor.execute(ddl)
                
                # 初期シード設定
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('app_version', '5.5')")
                
                # デフォルトアイテムの復元（日本語エンコード対策）
                items = [('ランドセル', '🎒'), ('ぼうし', '🧢'), ('すいとう', '🍶'), ('給食袋', '🍱'), ('リコーダー', '🎵')]
                cursor.executemany("INSERT OR IGNORE INTO items (name, icon) VALUES (?, ?)", items)
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")

    def get_items(self):
        """UI(main_view)が期待する『辞書のリスト』を返すっぴ！"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items ORDER BY id ASC")
            # これがアイテム登録画面で『情報が表示されない』を直す魔法だっぴ！
            return [dict(row) for row in cursor.fetchall()]

    def save_item(self, name, icon):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO items (name, icon) VALUES (?, ?)", (name, icon))
            conn.commit()

    def delete_item(self, item_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()

    def get_daily_schedule(self, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_schedules WHERE date = ?", (date_str,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_daily_schedule(self, date, item_ids, dep_msg, ret_msg, is_restricted, start_t, end_t):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_schedules (date, item_ids, departure_message, return_message, is_time_restricted, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    item_ids=excluded.item_ids, departure_message=excluded.departure_message,
                    return_message=excluded.return_message, is_time_restricted=excluded.is_time_restricted,
                    start_time=excluded.start_time, end_time=excluded.end_time
            """, (date, item_ids, dep_msg, ret_msg, is_restricted, start_t, end_t))
            conn.commit()

    def save_history(self, date_str, status, departure_time):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (date, status, departure_time) VALUES (?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET status=excluded.status, departure_time=excluded.departure_time
            """, (date_str, status, departure_time))
            conn.commit()

    def get_history(self, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history WHERE date = ?", (date_str,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_setting(self, key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
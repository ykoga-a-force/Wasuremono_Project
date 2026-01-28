-- ==========================================
-- キラキラ出発マスター データベース定義 (SQLite)
-- ==========================================

-- 1. 持ち物マスターテーブル (items)
-- お子様がチェックする持ち物の定義
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- 持ち物名 (例: ランドセル)
    icon TEXT,                         -- 絵文字アイコン (例: 🎒)
    display_order INTEGER DEFAULT 0,   -- 表示順
    is_active INTEGER DEFAULT 1,       -- 有効フラグ (1:有効, 0:無効)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. アプリ設定テーブル (settings)
-- 出発時間やメッセージの設定
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,              -- 設定キー (start_time, end_time, message)
    value TEXT NOT NULL,               -- 設定値
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 出発履歴テーブル (history)
-- 日々の成功・失敗の記録
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,         -- 日付 (YYYY-MM-DD)
    status TEXT NOT NULL,              -- 状態 (success: 時間内, failure: 時間外)
    departure_time TEXT,               -- 実際のボタン押下時刻 (HH:MM:SS)
    points INTEGER DEFAULT 0,          -- 獲得ポイント
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初期データの投入例
INSERT OR IGNORE INTO settings (key, value) VALUES ('start_time', '07:50');
INSERT OR IGNORE INTO settings (key, value) VALUES ('end_time', '08:10');
INSERT OR IGNORE INTO settings (key, value) VALUES ('reward_message', '今日も元気にいってらっしゃい！');

INSERT OR IGNORE INTO items (name, icon, display_order) VALUES ('ランドセル', '🎒', 1);
INSERT OR IGNORE INTO items (name, icon, display_order) VALUES ('ぼうし', '🧢', 2);
INSERT OR IGNORE INTO items (name, icon, display_order) VALUES ('すいとう', '🍶', 3);
INSERT OR IGNORE INTO items (name, icon, display_order) VALUES ('ハンカチ', '🧼', 4);

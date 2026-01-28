-- ==========================================
-- キラキラ出発マスター v2.1 データベース定義 (SQLite)
-- 【完全日付単位制御版】
-- ==========================================

-- ---------------------------------------------------------
-- 1. 持ち物マスターテーブル (items)
-- ---------------------------------------------------------
-- アプリに登録されている全ての持ち物の名前とアイコンを管理。
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- 持ち物名 (例: ランドセル)
    icon TEXT,                         -- 絵文字アイコン (例: 🎒)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- 2. 日別スケジュールテーブル (daily_schedules)
-- ---------------------------------------------------------
-- 日付単位ですべての制御項目（持ち物・メッセージ・時間制限）を管理。
-- 案Bに基づき、時間制御フラグとfrom-toの時間をこちらへ統合。
CREATE TABLE IF NOT EXISTS daily_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                -- 設定対象日 (YYYY-MM-DD)
    item_ids TEXT,                     -- 持ち物IDのカンマ区切り (例: "1,2,5")
    departure_message TEXT,            -- 子どもへの「いってらっしゃい」
    return_message TEXT,               -- 子どもへの「おかえり」
    is_time_restricted TEXT DEFAULT 'false', -- その日の時間制限をするか ('true'/'false')
    start_time TEXT DEFAULT '07:50',   -- その日の有効開始時間 (from)
    end_time TEXT DEFAULT '08:10',     -- その日の有効終了時間 (to)
    UNIQUE(date)                       -- 1日につき1レコード
);

-- ---------------------------------------------------------
-- 3. アプリ設定テーブル (settings)
-- ---------------------------------------------------------
-- アプリ全体で共通するシステム設定（バージョン管理など）に使用。
-- 日付に依存しない設定はこちらで管理。
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,              -- 設定の名前
    value TEXT NOT NULL,               -- 設定の値
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- 4. 出発履歴テーブル (history)
-- ---------------------------------------------------------
-- 日々の結果を記録する。
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,         -- 出発した日 (YYYY-MM-DD)
    status TEXT NOT NULL,              -- 状態 (success, failure)
    departure_time TEXT,               -- ボタンを押した時刻 (HH:MM:SS)
    points INTEGER DEFAULT 0,          -- 獲得ポイント
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- 初期データの投入 (シードデータ)
-- ---------------------------------------------------------

-- 1. アプリ全体設定の初期化
INSERT OR IGNORE INTO settings (key, value) VALUES ('app_version', '2.1');

-- 2. 持ち物の初期ラインナップ
INSERT OR IGNORE INTO items (name, icon) VALUES ('ランドセル', '🎒');
INSERT OR IGNORE INTO items (name, icon) VALUES ('ぼうし', '🧢');
INSERT OR IGNORE INTO items (name, icon) VALUES ('すいとう', '🍶');
INSERT OR IGNORE INTO items (name, icon) VALUES ('給食袋', '🍱');
INSERT OR IGNORE INTO items (name, icon) VALUES ('リコーダー', '🎵');

-- 3. 日付単位設定のサンプル例 (2月3日の魔法)
-- 持ち物ID 1〜5をセットし、時間制限をONにした例だっぴ！
INSERT OR IGNORE INTO daily_schedules (
    date, 
    item_ids, 
    departure_message, 
    return_message, 
    is_time_restricted, 
    start_time, 
    end_time
) VALUES (
    '2026-02-03', 
    '1,2,3,4,5', 
    '今日はリコーダーがあるよ！', 
    'リコーダー忘れてないかな？おかえり！', 
    'true', 
    '07:50', 
    '08:10'
);
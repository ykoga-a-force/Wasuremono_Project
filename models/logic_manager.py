from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from models.db_manager import DatabaseManager
import sqlite3

class LogicManager:
    """
    Handles business logic for the application.
    Implements Mode Logic and Data Persistence with safe connection handling.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_current_mode(self) -> Dict[str, any]:
        """
        Determines the current application mode safely.
        """
        today_str = date.today().isoformat()
        current_dt = datetime.now()
        
        try:
            history = self.db.get_history(today_str)
            
            if not history or history.get("status") != "success":
                msg = f"Mode check: No record for {today_str} (morning)"
                return {"mode": "morning", "debug_msg": msg}
            
            dep_time_str = history.get("departure_time", "00:00:00")
            msg = f"Mode check: Found record at {dep_time_str}"
            
            try:
                t = datetime.strptime(dep_time_str, "%H:%M:%S").time()
            except:
                t = datetime.strptime(dep_time_str, "%H:%M").time()

            dep_dt = datetime.combine(date.today(), t)
            diff = current_dt - dep_dt
            hours_passed = diff.total_seconds() / 3600
            
            if hours_passed < 4:
                return {"mode": "departure", "dep_time": dep_time_str, "debug_msg": f"Mode: Departure ({hours_passed:.2f}h passed)"}
            else:
                return {"mode": "return", "debug_msg": f"Mode: Return ({hours_passed:.2f}h passed)"}

        except Exception as e:
            err = f"Mode determination failed: {e}"
            return {"mode": "morning", "debug_msg": err}

    def record_departure(self):
        """Records the current time as departure time."""
        today_str = date.today().isoformat()
        now_dt = datetime.now()
        now_str = now_dt.strftime("%H:%M:%S")
        self.db.save_history(today_str, "success", now_str)
        return now_str

    def get_items_for_today(self) -> List[dict]:
        """Returns items for today using high-level db methods."""
        today_str = date.today().isoformat()
        schedule = self.db.get_daily_schedule(today_str)
        
        if not schedule or not schedule.get("item_ids"):
            return []

        item_ids = []
        for i in schedule["item_ids"].split(","):
            if i.strip().isdigit():
                item_ids.append(int(i.strip()))
        
        if not item_ids:
            return []

        # DatabaseManager has get_items but no multi-ID fetcher.
        # We fetch manually but ensure the connection is closed.
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        try:
            placeholders = ",".join("?" * len(item_ids))
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM items WHERE id IN ({placeholders})", item_ids)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] get_items_for_today: {e}")
            return []
        finally:
            conn.close()

    def get_messages_for_today(self) -> Dict[str, str]:
        """Returns departure and return messages."""
        today_str = date.today().isoformat()
        schedule = self.db.get_daily_schedule(today_str)
        if schedule:
            return {
                "departure": schedule.get("departure_message", ""),
                "return": schedule.get("return_message", "")
            }
        return {"departure": "", "return": ""}

    def get_time_restriction(self) -> Dict[str, any]:
        """Returns time restriction settings."""
        today_str = date.today().isoformat()
        schedule = self.db.get_daily_schedule(today_str)
        
        is_restricted = False
        start_time = datetime.strptime("07:50", "%H:%M").time()
        end_time = datetime.strptime("08:10", "%H:%M").time()

        if schedule:
            is_restricted = str(schedule.get("is_time_restricted", "false")).lower() == "true"
            try:
                if schedule.get("start_time"):
                    start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                if schedule.get("end_time"):
                    end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
            except ValueError:
                pass

        return {
            "is_restricted": is_restricted,
            "start_time": start_time,
            "end_time": end_time
        }

    def save_time_settings(self, is_restricted: bool, start_t, end_t):
        """Global time settings helper (saves to today's schedule as well)."""
        today_str = date.today().isoformat()
        schedule = self.db.get_daily_schedule(today_str) or {}
        
        item_ids = schedule.get("item_ids", "")
        dep_msg = schedule.get("departure_message", "")
        ret_msg = schedule.get("return_message", "")
        
        val_restricted = "true" if is_restricted else "false"
        val_start = start_t.strftime("%H:%M")
        val_end = end_t.strftime("%H:%M")
        
        self.db.save_daily_schedule(today_str, item_ids, dep_msg, ret_msg, val_restricted, val_start, val_end)

    def get_scheduled_dates(self, year: int, month: int) -> List[str]:
        month_pattern = f"{year}-{month:02d}-%"
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT date FROM daily_schedules WHERE date LIKE ?", (month_pattern,))
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def get_schedule_details(self, date_str: str) -> Dict[str, any]:
        schedule = self.db.get_daily_schedule(date_str)
        data = {
            "item_names": [],
            "departure_message": "",
            "return_message": "",
            "is_restricted": False,
            "start_time": datetime.strptime("07:50", "%H:%M").time(),
            "end_time": datetime.strptime("08:10", "%H:%M").time()
        }
        if schedule:
            data["departure_message"] = schedule.get("departure_message", "")
            data["return_message"] = schedule.get("return_message", "")
            data["is_restricted"] = str(schedule.get("is_time_restricted", "false")).lower() == "true"
            try:
                if schedule.get("start_time"):
                    data["start_time"] = datetime.strptime(schedule["start_time"], "%H:%M").time()
                if schedule.get("end_time"):
                    data["end_time"] = datetime.strptime(schedule["end_time"], "%H:%M").time()
            except ValueError:
                pass

            if schedule.get("item_ids"):
                item_ids = [int(i) for i in schedule["item_ids"].split(",") if i.strip().isdigit()]
                if item_ids:
                    conn = self.db.get_connection()
                    try:
                        placeholders = ",".join("?" * len(item_ids))
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT name FROM items WHERE id IN ({placeholders})", item_ids)
                        data["item_names"] = [row[0] for row in cursor.fetchall()]
                    finally:
                        conn.close()
        return data

    def save_schedule_from_ui(self, date_str: str, item_names: List[str], 
                            dep_msg: str, ret_msg: str,
                            is_restricted: bool, start_time, end_time):
        clean_names = [n.strip() for n in item_names if n.strip()]
        item_ids = []
        
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            for name in clean_names:
                cursor.execute("SELECT id FROM items WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    item_ids.append(str(row[0]))
                else:
                    cursor.execute("INSERT INTO items (name, icon) VALUES (?, ?)", (name, "🎒"))
                    item_ids.append(str(cursor.lastrowid))
            conn.commit()
        finally:
            conn.close()
        
        item_ids_str = ",".join(item_ids)
        val_restricted = "true" if is_restricted else "false"
        val_start = start_time.strftime("%H:%M")
        val_end = end_time.strftime("%H:%M")
        self.db.save_daily_schedule(date_str, item_ids_str, dep_msg, ret_msg, val_restricted, val_start, val_end)

    def save_bulk_schedule_from_ui(self, date_list: List[str], item_names: List[str], 
                                 dep_msg: str, ret_msg: str,
                                 is_restricted: bool, start_time, end_time):
        clean_names = [n.strip() for n in item_names if n.strip()]
        item_ids_str = ""
        
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            ids = []
            for name in clean_names:
                cursor.execute("SELECT id FROM items WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    ids.append(str(row[0]))
                else:
                    cursor.execute("INSERT INTO items (name, icon) VALUES (?, ?)", (name, "🎒"))
                    ids.append(str(cursor.lastrowid))
            conn.commit()
            item_ids_str = ",".join(ids)
        finally:
            conn.close()

        val_restricted = "true" if is_restricted else "false"
        val_start = start_time.strftime("%H:%M")
        val_end = end_time.strftime("%H:%M")
        for d_str in date_list:
            self.db.save_daily_schedule(d_str, item_ids_str, dep_msg, ret_msg, val_restricted, val_start, val_end)

    def get_monthly_history(self, year: int, month: int) -> Dict[int, Dict[str, any]]:
        month_pattern = f"{year}-{month:02d}-%"
        history_data = {}
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT date, status, departure_time FROM history WHERE date LIKE ?", (month_pattern,))
            rows = cursor.fetchall()
            for row in rows:
                d_str = row[0]
                day_int = int(d_str.split("-")[2])
                history_data[day_int] = {"status": row[1], "time": row[2]}
        except Exception:
            pass
        finally:
            conn.close()
        return history_data

    def reset_today_history(self):
        today_str = date.today().isoformat()
        self.db.save_history(today_str, "morning", "")
        # Actually delete to be sure
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE date = ?", (today_str,))
            conn.commit()
        finally:
            conn.close()

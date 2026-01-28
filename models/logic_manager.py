from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from models.db_manager import DatabaseManager
import sqlite3

class LogicManager:
    """
    Handles business logic for Glancal Journey.
    Implements Mode Logic and Data Persistence.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_current_mode(self) -> Dict[str, any]:
        """
        Determines the current application mode.
        1. Morning: No history for today.
        2. Departure: History exists, within 4 hours.
        3. Return: History exists, after 4 hours.
        """
        today_str = date.today().isoformat()
        current_dt = datetime.now()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT departure_time FROM history WHERE date = ? AND status = 'success'", 
                    (today_str,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return {"mode": "morning"}
                
                dep_time_str = row[0]
                try:
                    t = datetime.strptime(dep_time_str, "%H:%M:%S").time()
                except ValueError:
                    t = datetime.strptime(dep_time_str, "%H:%M").time()

                dep_dt = datetime.combine(date.today(), t)
                diff = current_dt - dep_dt
                hours_passed = diff.total_seconds() / 3600
                
                if hours_passed < 4:
                    return {"mode": "departure", "dep_time": dep_time_str}
                else:
                    return {"mode": "return"}

        except Exception as e:
            print(f"Error determining mode: {e}")
            return {"mode": "morning"}

    def record_departure(self):
        """Records the current time as departure time."""
        today_str = date.today().isoformat()
        now_str = datetime.now().strftime("%H:%M:%S")
        self.db.save_history(today_str, "success", now_str)

    def get_items_for_today(self) -> List[dict]:
        """Returns items for today."""
        today_str = date.today().isoformat()
        schedule = self.db.get_daily_schedule(today_str)
        
        items = []
        if schedule and schedule.get("item_ids"):
            item_ids = [int(i) for i in schedule["item_ids"].split(",") if i.isdigit()]
            if item_ids:
                placeholders = ",".join("?" * len(item_ids))
                with self.db.get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM items WHERE id IN ({placeholders})", item_ids)
                    items = [dict(row) for row in cursor.fetchall()]
        return items

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
            is_restricted = schedule.get("is_time_restricted", "false").lower() == "true"
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

    def get_scheduled_dates(self, year: int, month: int) -> List[str]:
        month_pattern = f"{year}-{month:02d}-%"
        dates = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT date FROM daily_schedules WHERE date LIKE ?", (month_pattern,))
                dates = [row[0] for row in cursor.fetchall()]
        except Exception:
            pass
        return dates

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
            data["is_restricted"] = schedule.get("is_time_restricted", "false").lower() == "true"
            try:
                if schedule.get("start_time"):
                    data["start_time"] = datetime.strptime(schedule["start_time"], "%H:%M").time()
                if schedule.get("end_time"):
                    data["end_time"] = datetime.strptime(schedule["end_time"], "%H:%M").time()
            except ValueError:
                pass

            if schedule.get("item_ids"):
                item_ids = [int(i) for i in schedule["item_ids"].split(",") if i.isdigit()]
                if item_ids:
                    placeholders = ",".join("?" * len(item_ids))
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT name FROM items WHERE id IN ({placeholders})", item_ids)
                        data["item_names"] = [row[0] for row in cursor.fetchall()]
        return data

    def save_schedule_from_ui(self, date_str: str, item_names: List[str], 
                            dep_msg: str, ret_msg: str,
                            is_restricted: bool, start_time, end_time):
        print(f"DEBUG: Saving schedule for {date_str}")
        print(f"DEBUG: Received item_names: {item_names}")
        clean_names = [n.strip() for n in item_names if n.strip()]
        print(f"DEBUG: Cleaned names: {clean_names}")
        
        item_ids = []
        with self.db.get_connection() as conn:
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
        
        item_ids_str = ",".join(item_ids)
        print(f"DEBUG: Generated item_ids_str: {item_ids_str}")
        val_restricted = "true" if is_restricted else "false"
        val_start = start_time.strftime("%H:%M")
        val_end = end_time.strftime("%H:%M")
        self.db.save_daily_schedule(date_str, item_ids_str, dep_msg, ret_msg, val_restricted, val_start, val_end)

    def save_bulk_schedule_from_ui(self, date_list: List[str], item_names: List[str], 
                                 dep_msg: str, ret_msg: str,
                                 is_restricted: bool, start_time, end_time):
        clean_names = [n.strip() for n in item_names if n.strip()]
        item_ids = []
        with self.db.get_connection() as conn:
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
        item_ids_str = ",".join(item_ids)
        val_restricted = "true" if is_restricted else "false"
        val_start = start_time.strftime("%H:%M")
        val_end = end_time.strftime("%H:%M")
        for d_str in date_list:
            self.db.save_daily_schedule(d_str, item_ids_str, dep_msg, ret_msg, val_restricted, val_start, val_end)

    def get_monthly_history(self, year: int, month: int) -> Dict[int, Dict[str, any]]:
        month_pattern = f"{year}-{month:02d}-%"
        history_data = {}
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT date, status, departure_time FROM history WHERE date LIKE ?", (month_pattern,))
                rows = cursor.fetchall()
                for row in rows:
                    d_str = row[0]
                    day_int = int(d_str.split("-")[2])
                    history_data[day_int] = {"status": row[1], "time": row[2]}
        except Exception:
            pass
        return history_data

    def reset_today_history(self):
        today_str = date.today().isoformat()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history WHERE date = ?", (today_str,))
                conn.commit()
        except Exception:
            pass

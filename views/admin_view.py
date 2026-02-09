import streamlit as st
import calendar
import time
from datetime import datetime, timedelta
from views.utils import inject_common_css

class AdminView:
    def __init__(self, logic_manager):
        self.logic_manager = logic_manager

    def render(self):
        inject_common_css()
        self._inject_admin_css()
        
        if "admin_year" not in st.session_state:
            st.session_state.admin_year = datetime.now().year
        if "admin_month" not in st.session_state:
            st.session_state.admin_month = datetime.now().month
        
        if "admin_bulk_mode" not in st.session_state:
            st.session_state.admin_bulk_mode = False
        if "admin_selected_dates" not in st.session_state:
            st.session_state.admin_selected_dates = set()

        year = st.session_state.admin_year
        month = st.session_state.admin_month

        if not st.session_state.admin_bulk_mode and "admin_dialog_date" in st.session_state:
            self.edit_dialog(st.session_state["admin_dialog_date"])
        
        if st.session_state.admin_bulk_mode and st.session_state.get("show_bulk_dialog"):
            self.bulk_edit_dialog()

        col_back, col_prev, col_title, col_next, col_add = st.columns([1, 1, 2, 1, 1])
        
        with col_back:
            if st.button("⬅️", key="btn_back_main", use_container_width=True):
                keys_to_clear = ["admin_dialog_date", "show_bulk_dialog", "admin_bulk_mode", "admin_selected_dates"]
                for k in keys_to_clear:
                    if k in st.session_state:
                        del st.session_state[k]
                st.session_state["page"] = "main"
                st.rerun()

        with col_prev:
            if st.button("◀️", key="admin_prev_month", use_container_width=True):
                if st.session_state.admin_month == 1:
                    st.session_state.admin_month = 12
                    st.session_state.admin_year -= 1
                else:
                    st.session_state.admin_month -= 1
                st.rerun()

        with col_title:
            st.markdown(f'<div class="admin-header-title">{year}年{month}月</div>', unsafe_allow_html=True)

        with col_next:
            if st.button("▶️", key="admin_next_month", use_container_width=True):
                if st.session_state.admin_month == 12:
                    st.session_state.admin_month = 1
                    st.session_state.admin_year += 1
                else:
                    st.session_state.admin_month += 1
                st.rerun()

        with col_add:
            btn_label = "✅ 一括" if not st.session_state.admin_bulk_mode else "戻る"
            if st.button(btn_label, key="btn_toggle_bulk", type="primary" if st.session_state.admin_bulk_mode else "secondary", use_container_width=True):
                st.session_state.admin_bulk_mode = not st.session_state.admin_bulk_mode
                if "admin_dialog_date" in st.session_state:
                    del st.session_state["admin_dialog_date"]
                if "show_bulk_dialog" in st.session_state:
                    del st.session_state["show_bulk_dialog"]
                st.session_state.admin_selected_dates = set()
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.admin_bulk_mode:
            st.info("📅 日付を選択して、「一括登録」ボタンを押してください。")
            if st.session_state.admin_selected_dates:
                if st.button(f"指定した {len(st.session_state.admin_selected_dates)} 日分を一括登録する", type="primary", use_container_width=True):
                    st.session_state["show_bulk_dialog"] = True
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        scheduled_dates = self.logic_manager.get_scheduled_dates(year, month)
        cal = calendar.Calendar(firstweekday=6) 
        month_days = cal.monthdayscalendar(year, month)
        
        cols = st.columns(7)
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(weekdays):
            cols[i].markdown(f'<div class="weekday-header">{day}</div>', unsafe_allow_html=True)

        for week in month_days:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.markdown('<div class="empty-day"></div>', unsafe_allow_html=True)
                    else:
                        current_date_str = f"{year}-{month:02d}-{day:02d}"
                        is_scheduled = current_date_str in scheduled_dates
                        
                        if st.session_state.admin_bulk_mode:
                            is_selected = current_date_str in st.session_state.admin_selected_dates
                            label = f"{day}"
                            if is_scheduled: label += "✨"
                            
                            def _on_check(iso_date=current_date_str):
                                if iso_date in st.session_state.admin_selected_dates:
                                    st.session_state.admin_selected_dates.discard(iso_date)
                                else:
                                    st.session_state.admin_selected_dates.add(iso_date)

                            st.checkbox(label, value=is_selected, key=f"chk_{current_date_str}", on_change=_on_check, kwargs={"iso_date": current_date_str})
                        else:
                            label = f"{day}"
                            if is_scheduled: label += " ✨"
                            if st.button(label, key=f"day_{current_date_str}", use_container_width=True):
                                st.session_state["admin_dialog_date"] = current_date_str
                                # 以前のダイアログデータが残っているのを防ぐため、明示的にクリアするっぴ
                                if "dialog_date" in st.session_state:
                                    del st.session_state["dialog_date"]
                                st.rerun()

        if not st.session_state.admin_bulk_mode:
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.subheader("⚙️ Global Time Rules")
            
            with st.expander("Departure Time Limits", expanded=True):
                current_settings = self.logic_manager.get_time_restriction()
                is_restricted = st.checkbox("Limit the 'Let's Go' button timing", value=current_settings["is_restricted"])
                col_start, col_end = st.columns(2)
                with col_start:
                    start_t = st.time_input("Start Time", value=current_settings["start_time"], disabled=not is_restricted, step=300)
                with col_end:
                    end_t = st.time_input("End Time", value=current_settings["end_time"], disabled=not is_restricted, step=300)
                    
                if st.button("Save Time Rules"):
                    self.logic_manager.save_time_settings(is_restricted, start_t, end_t)
                    st.success("Time rules updated for Today!")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("⚠️ Danger Zone (緊急リセット)"):
                st.warning("本日の出発記録を取り消します。")
                if st.button("本日の履歴をリセットする", type="primary"):
                    self.logic_manager.reset_today_history()
                    st.success("本日の履歴を削除しました。")
                    time.sleep(1)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="admin-footer-banner">
            Tap the date to cast a spell on tomorrow. 🪄
        </div>
        """, unsafe_allow_html=True)

    @st.dialog("🔥 Batch Registration")
    def bulk_edit_dialog(self):
        st.subheader(f"Registering for {len(st.session_state.admin_selected_dates)} days")
        st.markdown("#### 🎒 Items to bring")
        item_inputs = []
        for i in range(10):
            col_idx, col_input = st.columns([1, 9])
            with col_idx: st.write(f"{i+1}.")
            with col_input:
                val = st.text_input(f"Item {i+1}", key=f"bulk_item_{i}", placeholder="Item...")
                if val.strip(): item_inputs.append(val.strip())

        st.markdown("<br>", unsafe_allow_html=True)
        dep_msg = st.text_area("🌅 Departure Message", key="bulk_dep_msg", placeholder="行ってらっしゃい！...")
        ret_msg = st.text_area("🏠 Return Message", key="bulk_ret_msg", placeholder="おかえり！...")

        st.markdown("#### ⏱️ Time Rules")
        is_restricted = st.checkbox("Enable Time Limit", key="bulk_time_restricted")
        col_start, col_end = st.columns(2)
        with col_start:
            start_t = st.time_input("Start", key="bulk_start", disabled=not is_restricted, step=300, value=datetime.strptime("07:50", "%H:%M").time())
        with col_end:
            end_t = st.time_input("End", key="bulk_end", disabled=not is_restricted, step=300, value=datetime.strptime("08:10", "%H:%M").time())

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Register All", type="primary", use_container_width=True):
            date_list = list(st.session_state.admin_selected_dates)
            self.logic_manager.save_bulk_schedule_from_ui(date_list, item_inputs, dep_msg, ret_msg, is_restricted, start_t, end_t)
            st.success("Batch registration complete!")
            st.session_state["show_bulk_dialog"] = False
            st.session_state.admin_selected_dates = set()
            st.session_state.admin_bulk_mode = False
            st.rerun()

    @st.dialog("🪄 Setting up the Magic")
    def edit_dialog(self, target_date_str):
        dt = datetime.strptime(target_date_str, "%Y-%m-%d")
        st.caption(f"Preparing for {dt.strftime('%B %d, %Y')}")

        if "dialog_data" not in st.session_state or st.session_state.get("dialog_date") != target_date_str:
            data = self.logic_manager.get_schedule_details(target_date_str)
            st.session_state["dialog_data"] = data
            st.session_state["dialog_date"] = target_date_str
            current_items = data["item_names"]
            for i in range(10):
                st.session_state[f"input_item_{i}"] = current_items[i] if i < len(current_items) else ""
            st.session_state["input_dep_msg"] = data["departure_message"]
            st.session_state["input_ret_msg"] = data["return_message"]
            st.session_state["input_time_restricted"] = data["is_restricted"]
            st.session_state["input_start_time"] = data["start_time"]
            st.session_state["input_end_time"] = data["end_time"]

        if st.button("Copy from Previous Day 📋"):
            prev_day = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_data = self.logic_manager.get_schedule_details(prev_day)
            prev_items = prev_data["item_names"]
            for i in range(10):
                st.session_state[f"input_item_{i}"] = prev_items[i] if i < len(prev_items) else ""
            st.session_state["input_dep_msg"] = prev_data["departure_message"]
            st.session_state["input_ret_msg"] = prev_data["return_message"]
            st.session_state["input_time_restricted"] = prev_data["is_restricted"]
            st.session_state["input_start_time"] = prev_data["start_time"]
            st.session_state["input_end_time"] = prev_data["end_time"]
            st.toast(f"Copied data from {prev_day}!", icon="📋")
            st.rerun()

        st.markdown("---")
        st.markdown("#### 🎒 Items to bring")
        item_inputs = []
        for i in range(10):
            col_idx, col_input, _ = st.columns([1, 8, 1])
            with col_idx: st.markdown(f"<div style='text-align: right; padding-top: 10px; font-weight: bold; color: #aaa;'>{i+1}.</div>", unsafe_allow_html=True)
            with col_input:
                val = st.text_input(f"Item {i+1}", key=f"input_item_{i}", label_visibility="collapsed")
                if val.strip(): item_inputs.append(val.strip())

        st.markdown("<br>", unsafe_allow_html=True)
        dep_msg = st.text_area("🌅 Departure Message", key="input_dep_msg", height=68)
        ret_msg = st.text_area("🏠 Return Message", key="input_ret_msg", height=68)

        st.markdown("#### ⏱️ Time Rules")
        is_restricted = st.checkbox("行ってきますボタンを時間で制御する", key="input_time_restricted")
        col_start, col_end = st.columns(2)
        with col_start: start_t = st.time_input("Start Time", key="input_start_time", disabled=not is_restricted, step=300)
        with col_end: end_t = st.time_input("End Time", key="input_end_time", disabled=not is_restricted, step=300)

        if st.button("✨ Work a spell with this content ✨", type="primary", use_container_width=True):
            self.logic_manager.save_schedule_from_ui(target_date_str, item_inputs, dep_msg, ret_msg, is_restricted, start_t, end_t)
            st.success("Saved perfectly!")
            if "admin_dialog_date" in st.session_state: del st.session_state["admin_dialog_date"]
            if "dialog_date" in st.session_state: del st.session_state["dialog_date"] # Force reload on next click
            st.rerun()

    def _inject_admin_css(self):
        st.markdown("""
        <style>
        .admin-header-title { font-size: 2rem; font-weight: bold; text-align: center; color: #333; }
        .weekday-header { text-align: center; font-weight: bold; color: #888; margin-bottom: 5px; }
        .empty-day { height: 50px; }
        .admin-footer-banner { background-color: #E0F2F2; color: #00695C; padding: 15px; border-radius: 15px; text-align: center; font-weight: bold; }
        div[data-testid="stColumn"] button { height: 60px; border-radius: 10px; background-color: white; color: #333; }
        </style>
        """, unsafe_allow_html=True)

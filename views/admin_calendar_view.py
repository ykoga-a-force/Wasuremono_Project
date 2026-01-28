import streamlit as st
import calendar
import time
from datetime import datetime, date, timedelta
from consts.messages import ERROR_MESSAGES

class AdminCalendarView:
    def __init__(self, logic_manager):
        self.logic_manager = logic_manager

    def render(self):
        self._inject_custom_css()
        
        # --- State Management for Calendar ---
        if "admin_year" not in st.session_state:
            st.session_state.admin_year = datetime.now().year
        if "admin_month" not in st.session_state:
            st.session_state.admin_month = datetime.now().month
        
        # Bulk Mode State
        if "admin_bulk_mode" not in st.session_state:
            st.session_state.admin_bulk_mode = False
        if "admin_selected_dates" not in st.session_state:
            st.session_state.admin_selected_dates = set()

        year = st.session_state.admin_year
        month = st.session_state.admin_month

        year = st.session_state.admin_year
        month = st.session_state.admin_month

        # --- Trigger Dialogs from State ---
        # Single Edit Dialog (Only in Normal Mode)
        if not st.session_state.admin_bulk_mode and "admin_dialog_date" in st.session_state:
            self.edit_dialog(st.session_state["admin_dialog_date"])
        
        # Bulk Dialog (Only in Bulk Mode)
        if st.session_state.admin_bulk_mode and st.session_state.get("show_bulk_dialog"):
            self.bulk_edit_dialog()

        # --- (A) Header Area ---
        col_back, col_title, col_add = st.columns([1, 4, 1])
        
        with col_back:
            if st.button("⬅️", key="btn_back_main"):
                # Clean up Admin States before leaving
                keys_to_clear = ["admin_dialog_date", "show_bulk_dialog", "admin_bulk_mode", "admin_selected_dates"]
                for k in keys_to_clear:
                    if k in st.session_state:
                        del st.session_state[k]
                
                st.session_state["page"] = "main"
                st.rerun()

        with col_title:
            month_name = calendar.month_name[month]
            st.markdown(f'<div class="admin-header-title">{month_name} {year}</div>', unsafe_allow_html=True)

        with col_add:
            # Toggle Bulk Mode
            btn_label = "✅ 一括" if not st.session_state.admin_bulk_mode else "戻る"
            if st.button(btn_label, key="btn_toggle_bulk", help="一括登録モードへ切り替え", type="primary" if st.session_state.admin_bulk_mode else "secondary"):
                st.session_state.admin_bulk_mode = not st.session_state.admin_bulk_mode
                
                # Clear dialog states when switching modes
                if "admin_dialog_date" in st.session_state:
                    del st.session_state["admin_dialog_date"]
                if "show_bulk_dialog" in st.session_state:
                    del st.session_state["show_bulk_dialog"]
                
                # Clear selection on toggle
                st.session_state.admin_selected_dates = set()
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Bulk Mode Actions
        if st.session_state.admin_bulk_mode:
            st.info("📅 日付を選択して、「一括登録」ボタンを押してください。")
            if st.session_state.admin_selected_dates:
                if st.button(f"指定した {len(st.session_state.admin_selected_dates)} 日分を一括登録する", type="primary", use_container_width=True):
                    st.session_state["show_bulk_dialog"] = True
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        # --- (B) Calendar Area ---
        scheduled_dates = self.logic_manager.get_scheduled_dates(year, month)
        cal = calendar.Calendar(firstweekday=6) 
        month_days = cal.monthdayscalendar(year, month)
        
        # Weekday Headers
        cols = st.columns(7)
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(weekdays):
            cols[i].markdown(f'<div class="weekday-header">{day}</div>', unsafe_allow_html=True)

        # Days Grid
        for week in month_days:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.markdown('<div class="empty-day"></div>', unsafe_allow_html=True)
                    else:
                        current_date_str = f"{year}-{month:02d}-{day:02d}"
                        is_scheduled = current_date_str in scheduled_dates
                        
                        # --- Normal Mode or Bulk Mode ---
                        if st.session_state.admin_bulk_mode:
                            # Checkbox logic
                            is_selected = current_date_str in st.session_state.admin_selected_dates
                            label = f"{day}"
                            if is_scheduled: label += "✨"
                            
                            # Use checkbox for selection
                            # Note: checkbox in loop needs unique key. 
                            # If checked, add to set. If unchecked, remove.
                            # Streamlit checkbox state persists, so we bind it to the set manually or let st handle it?
                            # Use callback to manage set.
                            def _on_check(iso_date=current_date_str):
                                if iso_date in st.session_state.admin_selected_dates:
                                    st.session_state.admin_selected_dates.discard(iso_date)
                                else:
                                    st.session_state.admin_selected_dates.add(iso_date)

                            st.checkbox(label, value=is_selected, key=f"chk_{current_date_str}", on_change=_on_check, kwargs={"iso_date": current_date_str})
                            
                        else:
                            # Normal Button Logic
                            label = f"{day}"
                            if is_scheduled:
                                label += " ✨"
                            
                            if st.button(label, key=f"day_{current_date_str}", use_container_width=True):
                                st.session_state["admin_dialog_date"] = current_date_str
                                st.rerun()


        # --- (C) Footer Area (Settings) - Only show in Normal Mode for simplicity ---
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
        
        # Pre-fill settings (from Today or default)
        
        # --- Items Inputs ---
        st.markdown("#### 🎒 Items to bring")
        item_inputs = []
        for i in range(10):
            col_idx, col_input = st.columns([1, 9])
            with col_idx:
                st.write(f"{i+1}.")
            with col_input:
                val = st.text_input(f"Item {i+1}", key=f"bulk_item_{i}", placeholder="Item...")
                if val.strip():
                    item_inputs.append(val.strip())

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Messages Inputs ---
        dep_msg = st.text_area("🌅 Departure Message", key="bulk_dep_msg", placeholder="行ってらっしゃい！...")
        ret_msg = st.text_area("🏠 Return Message", key="bulk_ret_msg", placeholder="おかえり！...")

        # --- Time Settings ---
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
            self.logic_manager.save_bulk_schedule_from_ui(
                date_list, item_inputs, dep_msg, ret_msg,
                is_restricted, start_t, end_t
            )
            st.success("Batch registration complete!")
            
            # Cleanup
            st.session_state["show_bulk_dialog"] = False
            st.session_state.admin_selected_dates = set()
            st.session_state.admin_bulk_mode = False
            st.rerun()

    @st.dialog("🪄 Setting up the Magic")
    def edit_dialog(self, target_date_str):
        # Format title
        dt = datetime.strptime(target_date_str, "%Y-%m-%d")
        st.caption(f"Preparing for {dt.strftime('%B %d, %Y')}")

        # Load existing data
        if "dialog_data" not in st.session_state or st.session_state.get("dialog_date") != target_date_str:
            data = self.logic_manager.get_schedule_details(target_date_str)
            
            st.session_state["dialog_data"] = data
            st.session_state["dialog_date"] = target_date_str
            
            # Pre-fill session items for inputs
            current_items = data["item_names"]
            for i in range(10):
                val = current_items[i] if i < len(current_items) else ""
                st.session_state[f"input_item_{i}"] = val
            
            st.session_state["input_dep_msg"] = data["departure_message"]
            st.session_state["input_ret_msg"] = data["return_message"]
            
            st.session_state["input_time_restricted"] = data["is_restricted"]
            st.session_state["input_start_time"] = data["start_time"]
            st.session_state["input_end_time"] = data["end_time"]

        
        # --- Copy Function ---
        # Logic: Fetch prev day, update SESSION STATE variables, then RERUN dialog.
        # Rerun is kept safe by render() checking session_state["admin_dialog_date"]
        if st.button("Copy from Previous Day 📋", help="前日の設定をコピーします"):
            prev_day = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_data = self.logic_manager.get_schedule_details(prev_day)
            prev_items = prev_data["item_names"]
            
            # Update session state for Items/Messages only (Time settings are global-ish but handled per day)
            for i in range(10):
                val = prev_items[i] if i < len(prev_items) else ""
                st.session_state[f"input_item_{i}"] = val
            
            st.session_state["input_dep_msg"] = prev_data["departure_message"]
            st.session_state["input_ret_msg"] = prev_data["return_message"]
            
            # Update time settings
            st.session_state["input_time_restricted"] = prev_data["is_restricted"]
            st.session_state["input_start_time"] = prev_data["start_time"]
            st.session_state["input_end_time"] = prev_data["end_time"]
            
            st.toast(f"Copied data from {prev_day}!", icon="📋")
            st.rerun()

        st.markdown("---")

        # --- Items Inputs ---
        st.markdown("#### 🎒 Items to bring")
        item_inputs = []
        for i in range(10):
            col_idx, col_input, col_icon = st.columns([1, 8, 1])
            with col_idx:
                st.markdown(f"<div style='text-align: right; padding-top: 10px; font-weight: bold; color: #aaa;'>{i+1}.</div>", unsafe_allow_html=True)
            with col_input:
                val = st.text_input(f"Item {i+1}", key=f"input_item_{i}", label_visibility="collapsed", placeholder="Input item name...")
                if val.strip():
                    item_inputs.append(val.strip())
            with col_icon:
                st.markdown("<div style='padding-top: 10px;'>➡️</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Messages Inputs ---
        dep_msg = st.text_area("🌅 Departure Message", key="input_dep_msg", placeholder="行ってらっしゃい！...", height=68)
        ret_msg = st.text_area("🏠 Return Message", key="input_ret_msg", placeholder="おかえり！...", height=68)

        # --- Time Settings (Inside Dialog) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⏱️ Time Rules")
        is_restricted = st.checkbox("行ってきますボタンを時間で制御する", key="input_time_restricted")
        
        col_start, col_end = st.columns(2)
        with col_start:
            start_t = st.time_input("Start Time", key="input_start_time", disabled=not is_restricted, step=300)
        with col_end:
            end_t = st.time_input("End Time", key="input_end_time", disabled=not is_restricted, step=300)

        # --- Save Button ---
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Work a spell with this content ✨", type="primary", use_container_width=True):
            self.logic_manager.save_schedule_from_ui(
                target_date_str, item_inputs, dep_msg, ret_msg,
                is_restricted, start_t, end_t
            )
            st.success("Saved perfectly!")
            
            # Close dialog cleanup
            if "admin_dialog_date" in st.session_state:
                del st.session_state["admin_dialog_date"]
            st.rerun()

    def _inject_custom_css(self):
        st.markdown("""
        <style>
        /* Admin View Specific Styles */
        
        /* Header */
        .admin-header-title {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            color: #333;
            font-family: 'Arial', sans-serif;
        }

        /* Calendar Grid */
        .weekday-header {
            text-align: center;
            font-weight: bold;
            color: #888;
            margin-bottom: 5px;
        }
        
        .empty-day {
            height: 50px;
        }

        /* Footer Banner */
        .admin-footer-banner {
            background-color: #E0F2F1; /* Mint Green */
            color: #00695C;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Button Styling attempt for Calendar Days */
        /* This targets buttons inside the grid roughly */
        div[data-testid="stColumn"] > div > div > div > button {
            height: 60px;
            border-radius: 10px;
            border: 1px solid #eee;
            background-color: white;
            color: #333;
            font-size: 1.2rem;
            transition: all 0.2s;
        }
        
        div[data-testid="stColumn"] > div > div > div > button:hover {
            border-color: #87CEEB;
            color: #87CEEB;
        }

        /* Note: It's hard to inject distinct classes into specific buttons (Scheduled vs Normal) 
           without custom components. 
           However, we can differentiate by the button LABEL content if we use attribute selectors,
           or just accept that they all look similar but "Scheduled" ones have a mark.
           
           Strict visual requirements: "Background Pale Yellow or Mint Green for scheduled".
           We can try to use `st.markdown` with links or non-button layout if buttons fail.
           But buttons are best for interaction.
           
           Alternative: Use `st.container` with background color and a button inside?
           Streamlit layout is rigid. 
           
           Compromise: All buttons are white, but we add an emoji/mark for scheduled days in the label,
           as implemented in the python code (label += " ✨").
        */
        
        </style>
        """, unsafe_allow_html=True)

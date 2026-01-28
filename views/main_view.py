import streamlit as st
import streamlit.components.v1 as components
import calendar
import os
import random
import base64
import time
import textwrap
from datetime import datetime
from PIL import Image

# --- Cache-able Functions (Global to take advantage of st.cache) ---
@st.cache_data
def get_img_base64_cached(path):
    """Caches the heavy disk I/O and base64 encoding."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

class MainView:
    def __init__(self, logic_manager):
        self.logic_manager = logic_manager

    def render(self):
        self._inject_custom_css()
        self._render_header()

        # Page Routing based on session state
        if "page" not in st.session_state:
            st.session_state.page = "main"

        if st.session_state.page == "results":
            self._render_achievement_page()
            return st.empty()
        elif st.session_state.page == "admin":
            return st.empty() 
        else:
            return self._render_child_screen()
        
        return st.empty()

    def _render_header(self):
        st.markdown('<h2 class="app-title">✨ Glancal Journey ✨</h2>', unsafe_allow_html=True)
        
        # Independent Clock Component
        clock_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    background-color: transparent;
                    color: white;
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    text-align: center;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    height: 100vh;
                }
                .date-text {
                    font-size: 1.5rem;
                    font-weight: bold;
                    margin-bottom: 5px;
                    letter-spacing: 1px;
                }
                .time-text {
                    font-size: 4.5rem;
                    font-weight: 900;
                    line-height: 1;
                    letter-spacing: 2px;
                    margin-top: 5px;
                }
            </style>
        </head>
        <body>
            <div id="clock_app">
                <div class="date-text"></div>
                <div class="time-text"></div>
            </div>
            <script>
                function updateClock() {
                    var now = new Date();
                    var y = now.getFullYear();
                    var m = ("0" + (now.getMonth() + 1)).slice(-2);
                    var d = ("0" + now.getDate()).slice(-2);
                    var dateStr = `${y}年${m}月${d}日`;
                    
                    var h = ("0" + now.getHours()).slice(-2);
                    var min = ("0" + now.getMinutes()).slice(-2);
                    var s = ("0" + now.getSeconds()).slice(-2);
                    var timeStr = `${h}:${min}:${s}`;
                    
                    var app = document.getElementById("clock_app");
                    if (app) {
                        app.querySelector(".date-text").innerText = dateStr;
                        app.querySelector(".time-text").innerText = timeStr;
                    }
                }
                setInterval(updateClock, 1000);
                updateClock();
            </script>
        </body>
        </html>
        """
        components.html(clock_html, height=150)

    def _render_child_screen(self):
        mode_info = self.logic_manager.get_current_mode()
        mode = mode_info["mode"]

        if mode == "morning":
            return self._render_morning_mode()
        elif mode == "departure":
            self._render_departure_mode(mode_info.get("dep_time", ""))
            self._render_footer()
            return st.empty()
        elif mode == "return":
            self._render_return_mode()
            self._render_footer()
            return st.empty()
        
        return st.empty()

    def _render_morning_mode(self):
        clock_placeholder = st.empty()
        items = self.logic_manager.get_items_for_today()
        
        if not items:
            st.warning("📭 本日の持ち物設定はありません")
            self._render_footer()
            return clock_placeholder 
        
        if 'checked_items' not in st.session_state:
            st.session_state.checked_items = set()

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        cols = st.columns(2)
        
        for i, item in enumerate(items):
            item_id = item["id"]
            is_checked = item_id in st.session_state.checked_items
            
            with cols[i % 2]:
                st.markdown('<div class="item-btn-marker"></div>', unsafe_allow_html=True)
                label = f"{item['name']}"
                
                btn_type = "primary" if is_checked else "secondary"
                
                if st.button(label, key=f"btn_item_{item_id}", type=btn_type, use_container_width=True):
                    if is_checked:
                        st.session_state.checked_items.discard(item_id)
                    else:
                        st.session_state.checked_items.add(item_id)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        self._render_departure_button()
        
        self._render_footer()
        return clock_placeholder

    def _render_departure_button(self):
        time_rules = self.logic_manager.get_time_restriction()
        is_disabled = False
        warning_msg = ""

        if time_rules["is_restricted"]:
            now_t = datetime.now().time()
            if not (time_rules["start_time"] <= now_t <= time_rules["end_time"]):
                is_disabled = True
                warning_msg = f"今は魔法が使えない時間だよ。<br>{time_rules['start_time'].strftime('%H:%M')}になったら押せるよ！"
        
        _, col, _ = st.columns([1, 2, 1])
        with col:
            if is_disabled:
                 st.button("🕐 待機中...", key="btn_main_go", disabled=True, use_container_width=True)
                 if warning_msg:
                     st.markdown(f"<div style='text-align:center; color:red; font-weight:bold;'>{warning_msg}</div>", unsafe_allow_html=True)
            else:
                if st.button("🚀 行ってきます！", key="btn_main_go", type="primary", use_container_width=True):
                    self.logic_manager.record_departure()
                    st.session_state.just_departed = True
                    st.rerun()

    def _render_departure_mode(self, dep_time):
        if st.session_state.get("just_departed"):
            self._trigger_celebration()
            st.session_state.just_departed = False

        messages = self.logic_manager.get_messages_for_today()
        msg = messages.get("departure") or "気をつけていってらっしゃい！"
        
        st.markdown(f"""
        <div class="message-card" style="background-color:#E0F7FA; color:#006064;">
            <h2>👋 いってらっしゃい！</h2>
            <p style="font-size:1.2rem; margin-top:10px;">{msg}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if dep_time:
            st.markdown(f"<div style='text-align:center; color:#555;'>出発時刻: {dep_time[:5]}</div>", unsafe_allow_html=True)

    def _render_return_mode(self):
        messages = self.logic_manager.get_messages_for_today()
        msg = messages.get("return") or "おかえりなさい！"
        
        st.markdown(f"""
        <div class="message-card" style="background-color:#FFFACD; color:#333;">
            <h2>🏠 おかえりなさい！</h2>
            <p>{msg}</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_achievement_page(self):
        st.markdown("---")
        st.markdown('<h2 style="text-align:center;">🏆 実績カレンダー 🏆</h2>', unsafe_allow_html=True)
        
        if st.button("⬅️ メイン画面に戻る", key="btn_back_home"):
            st.session_state.page = "main"
            st.rerun()

        year = datetime.now().year
        month = datetime.now().month
        
        # --- Optimization: GET DATA ONCE OUTSIDE THE LOOP ---
        history = self.logic_manager.get_monthly_history(year, month)
        
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year, month)
        
        cols_h = st.columns(7)
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, d in enumerate(weekdays):
            cols_h[i].markdown(f"<div style='text-align:center; font-weight:bold; color:white;'>{d}</div>", unsafe_allow_html=True)
            
        for week in month_days:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day != 0:
                        # LOOKUP FROM CACHED DICTIONARY
                        self._render_cal_cell(day, history.get(day))
                    else:
                        st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)

    def _render_cal_cell(self, day, data):
        bg = "rgba(255,255,255,0.9)"
        content = f"<div>{day}</div>"
        if data and data["status"] == "success":
            content += "<div>💮</div>"
            content += f"<div style='font-size:0.7rem;'>{data['time'][:5]}</div>"
        
        st.markdown(f"""
        <div style="background:{bg}; border-radius:15px; padding:5px; text-align:center; height:80px; margin-bottom:5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
            {content}
        </div>
        """, unsafe_allow_html=True)

    def _render_footer(self):
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏆 実績を見る", key="ft_results", use_container_width=True):
                st.session_state.page = "results"
                st.rerun()
        with c2:
            if st.button("⚙️ 保護者メニュー", key="ft_admin", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

    def _trigger_celebration(self):
        """ランダムでエフェクトを再生するっぴ！"""
        eff = random.choice(["balloons", "snow", "mix"])
        
        if eff == "balloons":
            st.balloons()
            st.toast("🎈 ふわふわ〜！いってらっしゃい！", icon="🎈")
        elif eff == "snow":
            st.snow()
            st.toast("❄️ クールに出発！いってらっしゃい！", icon="❄️")
        else:
            st.balloons()
            time.sleep(0.5)
            st.snow()
            st.toast("🌟 スター級の出発だね！", icon="🤩")

    def _inject_custom_css(self):
        # Optimization: Use Cached Image Encoding
        b64_on = get_img_base64_cached("image/check_on.png")
        b64_off = get_img_base64_cached("image/check_off.png")

        st.markdown(f"""
        <style>
        .stApp {{ background-color: #87CEEB; font-family: 'Helvetica', sans-serif; }}
        .app-title {{ text-align: center; color: white; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
        .date-display {{ text-align: center; color: white; margin-bottom: 20px; font-weight: bold; }}
        .message-card {{ padding: 30px; border-radius: 20px; text-align: center; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        
        /* Hide Marker */
        .item-btn-marker {{ display: none; }}

        /* Global Button Styles */
        div[data-testid="stButton"] button {{
            min-height: 80px; 
            border-radius: 20px; 
            font-size: 1.5rem !important;
            font-weight: bold !important;
            border: 3px solid white !important;
            box-shadow: 0 4px 0 rgba(0,0,0,0.1);
            transition: all 0.1s;
        }}
        
        div[data-testid="stButton"] button:active {{
            box-shadow: 0 0 0 rgba(0,0,0,0.1);
            transform: translateY(4px);
        }}

        /* Targeting Strategy: :has() */
        div:has(.item-btn-marker) + div button {{
            padding-left: 70px !important; 
            position: relative;
            display: flex;
            align-items: center;
            justify-content: flex-start;
        }}

        div:has(.item-btn-marker) + div button::before {{
            content: "";
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            width: 45px;
            height: 45px;
            background-repeat: no-repeat;
            background-position: center;
            background-size: contain;
        }}

        div:has(.item-btn-marker) + div button[kind="primary"] {{
            background-color: #98FB98 !important; 
            color: #006400 !important;
            border-color: #006400 !important;
        }}
        div:has(.item-btn-marker) + div button[kind="primary"]::before {{
            background-image: url('data:image/png;base64,{b64_on}');
        }}

        div:has(.item-btn-marker) + div button[kind="secondary"] {{
            background-color: #FFFACD !important;
            color: #555 !important;
        }}
        div:has(.item-btn-marker) + div button[kind="secondary"]::before {{
            background-image: url('data:image/png;base64,{b64_off}');
        }}

        button[key="btn_main_go"] {{
            background-color: #FFEB3B !important;
            height: 120px !important;
            font-size: 2.5rem !important;
            border-radius: 60px !important;
            justify-content: center !important; 
            padding-left: 20px !important; 
        }}
        </style>
        """, unsafe_allow_html=True)
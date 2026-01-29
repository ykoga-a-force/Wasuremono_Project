import streamlit as st
import time
import random
from datetime import datetime
from views.utils import inject_common_css, render_header, render_footer

class ChildView:
    def __init__(self, logic_manager):
        self.logic_manager = logic_manager

    def render(self):
        inject_common_css()
        render_header()

        if "debug_logs" not in st.session_state:
            st.session_state.debug_logs = []

        # 1. Get Mode
        mode_info = self.logic_manager.get_current_mode()
        mode = mode_info["mode"]

        # 2. Celebration (Always at top for visibility)
        if st.session_state.get("just_departed") or st.session_state.get("trigger_balloon"):
            print("[UI] SUCCESS: FLYING BALLOONS")
            st.session_state.debug_logs.append("Effect: SUCCESS")
            self._trigger_celebration()
            st.session_state.just_departed = False
            st.session_state.trigger_balloon = False

        # 3. Debug Sidebar
        with st.sidebar:
            st.title("🛠 Debug Panel")
            st.write(f"**Current Mode:** {mode}")
            st.write(f"**Status Info:** {mode_info.get('debug_msg', '')}")
            st.write("---")
            st.write("**Recent Logs:**")
            for log in reversed(st.session_state.debug_logs[-10:]):
                st.text(log)
            if st.button("Reset All"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # 4. Main Rendering
        if mode == "morning":
            self._render_morning_mode()
        elif mode == "departure":
            self._render_departure_mode(mode_info.get("dep_time", ""))
            render_footer()
        elif mode == "return":
            self._render_return_mode()
            render_footer()

    def _render_morning_mode(self):
        items = self.logic_manager.get_items_for_today()
        
        if not items:
            st.warning("📭 本日の持ち物設定はありません")
            render_footer()
            return
        
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
        self._render_departure_button_logic()
        render_footer()

    @st.fragment(run_every="10s")
    def _render_departure_button_logic(self):
        time_rules = self.logic_manager.get_time_restriction()
        is_disabled = False
        warning_msg = ""
        now_t = datetime.now().time()

        if time_rules["is_restricted"]:
            if not (time_rules["start_time"] <= now_t <= time_rules["end_time"]):
                is_disabled = True
                warning_msg = f"現在は出発できません。{time_rules['start_time'].strftime('%H:%M')}〜{time_rules['end_time'].strftime('%H:%M')}の間だけボタンが押せます。"
        
        # 10秒ごとに自動更新していることを示すインジケーター（開発用/ユーザー安心用）
        st.markdown(f"<div style='text-align:right; font-size:0.7rem; color:#ccc;'>Last Update: {now_t.strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

        _, col, _ = st.columns([1, 2, 1])
        with col:
            if is_disabled:
                 st.button("🕐 待機中...", key="btn_main_go", disabled=True, use_container_width=True)
                 if warning_msg:
                     st.markdown(f"<div style='text-align:center; color:red; font-size:0.8rem;'>{warning_msg}</div>", unsafe_allow_html=True)
            else:
                if st.button("🚀 行ってきます！", key="btn_main_go", type="primary", use_container_width=True):
                    st.session_state.debug_logs.append("Button Clicked!")
                    self.logic_manager.record_departure()
                    st.session_state.just_departed = True
                    st.session_state.trigger_balloon = True
                    st.session_state.debug_logs.append("DB Saved & Rerunning...")
                    st.rerun()

    def _render_departure_mode(self, dep_time):
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

    def _trigger_celebration(self):
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

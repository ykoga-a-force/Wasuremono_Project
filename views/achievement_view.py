import streamlit as st
import calendar
from datetime import datetime
from views.utils import inject_common_css, render_header, render_footer

class AchievementView:
    def __init__(self, logic_manager):
        self.logic_manager = logic_manager

    def render(self):
        inject_common_css()
        render_header(show_clock=False)

        st.markdown("---")
        st.markdown('<h2 style="text-align:center;">🏆 実績カレンダー 🏆</h2>', unsafe_allow_html=True)
        
        if st.button("⬅️ メイン画面に戻る", key="btn_back_home"):
            st.session_state.page = "main"
            st.rerun()

        year = datetime.now().year
        month = datetime.now().month
        
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
                        self._render_cal_cell(day, history.get(day))
                    else:
                        st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
        
        render_footer()

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

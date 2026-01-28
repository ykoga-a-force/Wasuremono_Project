import streamlit as st
import streamlit.components.v1 as components
import os
import base64

@st.cache_data
def get_img_base64_cached(path):
    """Caches the heavy disk I/O and base64 encoding."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

def inject_common_css():
    """Injects core design system styles (Helvetica, shared button styles)."""
    b64_on = get_img_base64_cached("image/check_on.png")
    b64_off = get_img_base64_cached("image/check_off.png")

    st.markdown(f"""
    <style>
    /* Global Styles */
    .stApp {{ background-color: #87CEEB; font-family: 'Helvetica', sans-serif; }}
    .app-title {{ text-align: center; color: white; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
    .date-display {{ text-align: center; color: white; margin-bottom: 20px; font-weight: bold; }}
    .message-card {{ padding: 30px; border-radius: 20px; text-align: center; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    
    /* Child View Specific (Keep for consistency) */
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

    /* Item Buttons (Check on/off) */
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
        background-color: #98FB98 !important; /* Light Green */
        color: #006400 !important;
        border-color: #006400 !important;
    }}
    div:has(.item-btn-marker) + div button[kind="primary"]::before {{
        background-image: url('data:image/png;base64,{b64_on}');
    }}

    div:has(.item-btn-marker) + div button[kind="secondary"] {{
        background-color: #FFFACD !important; /* Creamy Yellow */
        color: #555 !important;
    }}
    div:has(.item-btn-marker) + div button[kind="secondary"]::before {{
        background-image: url('data:image/png;base64,{b64_off}');
    }}

    /* Go Button */
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

def render_header(show_clock=True):
    """Renders the app title and optionally the independent HTML clock."""
    st.markdown('<h2 class="app-title">✨ Glancal Journey ✨</h2>', unsafe_allow_html=True)
    
    if show_clock:
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
                .date-text { font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; letter-spacing: 1px; }
                .time-text { font-size: 4.5rem; font-weight: 900; line-height: 1; letter-spacing: 2px; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div id="clock_app"><div class="date-text"></div><div class="time-text"></div></div>
            <script>
                function updateClock() {
                    var now = new Date();
                    var y = now.getFullYear();
                    var m = ("0" + (now.getMonth() + 1)).slice(-2);
                    var d = ("0" + now.getDate()).slice(-2);
                    document.querySelector(".date-text").innerText = `${y}年${m}月${d}日`;
                    var h = ("0" + now.getHours()).slice(-2);
                    var min = ("0" + now.getMinutes()).slice(-2);
                    var s = ("0" + now.getSeconds()).slice(-2);
                    document.querySelector(".time-text").innerText = `${h}:${min}:${s}`;
                }
                setInterval(updateClock, 1000);
                updateClock();
            </script>
        </body>
        </html>
        """
        components.html(clock_html, height=150)

def render_footer():
    """Renders the navigation buttons at the bottom."""
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

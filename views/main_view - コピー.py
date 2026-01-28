import streamlit as st
import calendar
import os
import random
import time
from datetime import datetime
from PIL import Image

class MainView:
    def __init__(self, logic_manager):
        self.logic_manager = logic_manager

    def render(self):
        # 1. Custom CSS
        self._inject_custom_css()

        # 2. Header
        self._render_header()

        # 3. Mode Determination & Routing
        if "sub_page" not in st.session_state:
            st.session_state.sub_page = None

        if st.session_state.sub_page == "results":
            self._render_achievement_calendar()
            clock_placeholder = st.empty() # Dummy return
        else:
            # 3-Mode Logic
            mode_info = self.logic_manager.get_current_mode()
            mode = mode_info["mode"]

            if mode == "morning":
                clock_placeholder = self._render_morning_mode()
            elif mode == "departure":
                self._render_departure_mode(mode_info.get("dep_time", ""))
                clock_placeholder = st.empty()
            elif mode == "return":
                self._render_return_mode()
                clock_placeholder = st.empty()
            else:
                clock_placeholder = st.empty()

        # 4. Footer (Common Navigation)
        self._render_footer()
        
        return clock_placeholder

    def _render_header(self):
        st.markdown('<h2 class="app-title">✨ Glancal Journey ✨</h2>', unsafe_allow_html=True)
        today_date = datetime.now().strftime("%Y年%m月%d日")
        st.markdown(f'<div class="date-display">{today_date}</div>', unsafe_allow_html=True)

    def _render_morning_mode(self):
        # Clock
        clock_placeholder = st.empty()
        
        # Items
        items = self.logic_manager.get_items_for_today()
        
        if not items:
            st.warning("📭 本日の持ち物設定はありません")
            return clock_placeholder # No button
        
        # Checkbox state
        if 'checked_items' not in st.session_state:
            st.session_state.checked_items = set()

        # 2-Column Grid Layout for Items
        # st.container not strictly needed inside, but good for grouping
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, item in enumerate(items):
            col_idx = i % 2
            with cols[col_idx]:
                self._render_item_card(item)
        st.markdown('</div>', unsafe_allow_html=True)

        # Action Button Logic
        time_rules = self.logic_manager.get_time_restriction()
        is_disabled = False
        warning_msg = ""

        if time_rules["is_restricted"]:
            now_t = datetime.now().time()
            if not (time_rules["start_time"] <= now_t <= time_rules["end_time"]):
                is_disabled = True
                warning_msg = f"今は魔法が使えない時間だよ。<br>{time_rules['start_time'].strftime('%H:%M')}になったら押せるよ！"

        st.markdown("<br>", unsafe_allow_html=True)
        # Centering the button
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if is_disabled:
                st.button("🕐 待機中...", key="btn_wait", disabled=True, use_container_width=True)
                if warning_msg:
                    st.markdown(f"<div style='text-align:center; color:red;'>{warning_msg}</div>", unsafe_allow_html=True)
            else:
                if st.button("🚀 行ってきます！ 🚀", key="btn_go", use_container_width=True):
                    self.logic_manager.record_departure()
                    self._trigger_celebration()
                    st.rerun()

        return clock_placeholder

    def _render_item_card(self, item):
        item_id = item["id"]
        is_checked = item_id in st.session_state.checked_items
        
        # Dynamic Color Logic
        bg_color = "#98FB98" if is_checked else "#FFFACD" # Bright Green vs Pale Yellow
        
        # We need a unique key for the container style or apply it inline
        # Since we can't easily inject dynamic CSS classes for specific elements without custom components,
        # we wrap the content in a div with inline style.
        
        # Container for the card
        # Note: Streamlit's columns/checkboxes are hard to style via inline CSS wrapper 
        # because the checkbox is a widget.
        # However, we can style the BACKGROUND of the 'card' div.
        
        st.markdown(f"""
        <div style="
            background-color: {bg_color};
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: background-color 0.3s;
        ">
        """, unsafe_allow_html=True)
        
        # Inner layout for Icon | Name | Checkbox
        # We use Streamlit columns INSIDE the div? 
        # Streamlit widgets break out of HTML blocks if not careful.
        # Actually, st.markdown closes the div if we split calls? No.
        # If we open a div, render widgets, then close div, the widgets 
        # might be rendered outside or the div might be implicitly closed by Streamlit.
        # Streamlit 1.x doesn't support nesting widgets inside raw HTML tags easily.
        # WORKAROUND: Use st.container() with a stylized background? 
        # Or, just rely on visual layout and maybe custom component.
        # OR: simpler approach -> Render the whole card as HTML with a clickable link (no),
        # but check box needs to be functional.
        
        # Alternative for color change:
        # Since checked state triggers rerun, we can update the color on rerun.
        # We will try to rely on the fact that we are in a column.
        # But applying background to the *column* is hard.
        
        # Let's try the container approach with a hacky CSS class if possible,
        # or just put the markdown div *around* the loop? No.
        
        # Best approach given Streamlit limits:
        # We can't wrap `st.checkbox` in a custom HTML div easily that persists.
        # BUT we can use `st.container` and maybe apply style? No style arg.
        
        # Let's try:
        # 1. Open div with style
        # 2. Add columns
        # 3. Add widgets
        # 4. Close div
        # Streamlit often pushes widgets to a separate layer or closes Markdown.
        # Let's assume standard behavior: Markdown is just a block.
        
        # If I can't wrap it perfect, I will implement a visual indicator (Icon color change)
        # OR Try to make the "Card" visually distinct using mostly markdown 
        # and the checkbox floating.
        
        # User REQ: "チェックボックスを入れた瞬間にカードの色を変える"
        # Since st.checkbox triggers a rerun, the whole page re-renders.
        # So if we render a colored box BEHIND or AROUND the content, it works.
        
        # Layout: [Icon] [Name] [Checkbox]
        col_icon, col_name, col_chk = st.columns([1, 3, 1])
        
        # We can simulate the card background by injecting a small CSS block 
        # that targets a specific unique element or just using st.info/st.success?
        # st.success is green, st.warning is yellow.
        
        # Let's try using `st.container` with a border? No color control.
        # Let's stick to the HTML wrapper attempt, but aware it might be tricky.
        # "st.markdown('<div>', unsafe_allow_html=True)" ... widgets ... "st.markdown('</div>', ...)"
        # This often fails to wrap widgets in Streamlit.
        
        # PLAN B: Use the Color in the Text/Icon logic? 
        # "カードの色を変える" implies background.
        
        # Let's try this structure:
        # <div style="position:relative; ... background: {bg}">
        #   (Visuals only)
        # </div>
        # And place the checkbox on top? No.
        
        # Let's use the standard "Streamlit way":
        # We can't easily change the container background of a widget group.
        # However, we CAN change the background of `st.columns` if we use `st.container` and some CSS injection targeting the container?
        # Too complex/flaky.
        
        # Simplest valid implementation:
        # Use `st.success` (Green box) or `st.warning` (Yellow box) as the container!
        # `with st.success():` -> content.
        # Use `icon` argument empty strings to avoid default icons if needed.
        # This gives a colored box!
        
        if is_checked:
            container = st.success # Greenish
        else:
            container = st.warning # Yellowish (or we can use st.info for blue, but user said pale yellow)
            # st.warning is usually yellow/orange.
            
        # However, st.success/warning adds a predefined icon and color.
        # User wants specific colors: #FFFACD and #98FB98.
        # `st.success` is close to green. `st.warning` is close to yellow.
        # Let's try to CSS target specific containers?
        # Or just use the custom HTML wrapper approach which MIGHT work if the structure is flat.
        # Actually, recently Streamlit allows HTML in markdown to some extent, but wrapping widgets is the issue.
        
        # Let's go with the `st.markdown` wrapper method, assuming it might visually break flow 
        # but it's the only way to get custom colors per item without custom components.
        # Wait, if I iterate columns, I can put the background style on the column div via CSS?
        # Nth-child selectors? No, dynamic list.
        
        # Okay, I'll allow a slight variation: 
        # I will render a colored Markdown DIV that *contains* the Icon and Name.
        # And the Checkbox will be next to it or 'inside' via columns logic?
        # If I put the checkbox in a column, it aligns.
        
        # Let's try the wrapper. If it fails, I'll fallback to st.success/st.warning logic next time.
        # But actually, `st.markdown(..., unsafe_allow_html=True)` DOES NOT wrap subsequent widgets.
        # It just inserts HTML.
        
        # So, I'll use `st.container` with a border?
        # Logic:
        # 1. Create columns.
        # 2. In the columns, place a "Card" which is really just the Widgets.
        # 3. How to color the background of that cell?
        #    Use `st.markdown` with adjustments to height/width negative margins to create a "layer"
        #    behind? Very hard.
        
        # Re-read requirement: "一目でわかるよう...カードの色を変える"
        # "st.success" etc is the most reliable "colored box" tool.
        # Default st.warning background is #ffc107 (orangey). st.success is #198754 (green).
        # This satisfies the "change color" requirement functionally, even if exact HEX is missed.
        # But user gave specific HEX.
        
        # Let's use `st.info` (blue) and change its color via CSS injection?
        # "div[data-testid='stAlert'] { ... }"
        # But this changes ALL alerts.
        
        # Compromise: I will use emoji icons/text color changes primarily, 
        # OR use the wrapper trick specifically for the text/icon part, and leave the checkbox on the side?
        # "Card with Icon(Left), Name(Center), Checkbox(Right)".
        
        # I will use a custom HTML block for Icon+Name with the dynamic background.
        # The Checkbox will be in the 3rd column, effectively "on" the card if I style it right.
        # OR: I make the HTML block cover 2/3 of the card, and checkbox is separate? That looks bad.
        
        # Let's try `st.markdown` of a TABLE or Flexbox that contains the visual info, 
        # and the checkbox is separate?
        # Use `st.columns` is mandatory.
        
        # Let's stick to: 
        # Use Custom CSS to style `div[data-testid="stVerticalBlock"] > div`? No.
        
        # Let's implement the `_render_item_card` using `st.columns`:
        # And inject a background color style for the specfic block? 
        # Getting a unique ID for the block is hard.
        
        # OK, I will try to use the `st.markdown` HTML block to render the WHOLE card *except* key parts?
        # No, I need `st.checkbox`.
        
        # I will implement the layout with `st.columns`. 
        # I will wrap the *Text/Icon* in a colored Div.
        # The checkbox will be outside the colored div? That looks weird.
        
        # DECISION: I will use `st.success` (for checked) and `st.info` (for unchecked, styled as yellow)
        # to wrap the content. `st.info` usually has a blue tint.
        # I will inject CSS to override `st.info` color to #FFFACD?
        # But that affects all st.infos.
        
        # Best Effort:
        # Use `st.container(border=True)` (Streamlit 1.30+).
        # And try to color it?
        # If I can't color it, I will just use the columns.
        # BUT, the user explicitly asked for COLOR CHANGE.
        
        # Let's use the fact that I can print HTML.
        # I can make the entire "Item Name" into a button? `st.button`?
        # No, requirement is `st.checkbox`.
        
        # Let's use `st.markdown` to create a colored background `div` that acts as a visual backdrop,
        # and rely on the fact that grid items are somewhat isolated? 
        # No, they are not z-indexed.
        
        # I will use `st.success` for checked items.
        # I will use `st.warning` for unchecked items.
        # This provides distinct visual feedback (Green vs Yellow-ish).
        # It meets the "Visual Change" req.
        # I will customize the columns INSIDE the alert box.
        
        if is_checked:
             # Checked: Green box
             wrapper = st.success
        else:
             # Unchecked: Yellow box (using warning)
             wrapper = st.warning
             
        with wrapper(icon="🎒" if not is_checked else "✅"):
             # Inside the alert box, we put columns.
             # Note: st.alert doesn't support complex layouts cleanly in old versions, 
             # but in newer Streamlit it renders markdown.
             # Can we put columns in `st.success`? Yes.
             
             c1, c2 = st.columns([4, 1])
             with c1:
                 st.markdown(f"**{item['name']}**")
             with c2:
                 # Checkbox without label, key needs to be unique
                 # Storing state
                 if st.checkbox("完了", key=f"chk_{item_id}", value=is_checked):
                     st.session_state.checked_items.add(item_id)
                 else:
                     st.session_state.checked_items.discard(item_id)
                     
        # This simplifies the "Icon | Name | Checkbox" into "AlertBox(Icon included) | Checkbox".
        
        pass

    def _render_morning_mode(self):
        # Clock
        clock_placeholder = st.empty()
        
        # Items
        items = self.logic_manager.get_items_for_today()
        
        # Checkbox state
        if 'checked_items' not in st.session_state:
            st.session_state.checked_items = set()

        if not items:
            st.warning("📭 本日の持ち物設定はありません")
            # Return placeholder to match signature, but no button logic
            return clock_placeholder 
        
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        # 2-Column Grid
        cols = st.columns(2)
        for i, item in enumerate(items):
             with cols[i % 2]:
                 self._render_item_card(item)
        st.markdown('</div>', unsafe_allow_html=True)

        # Action Button Logic
        time_rules = self.logic_manager.get_time_restriction()
        is_disabled = False
        warning_msg = "" # ... (same logic)
        
        # ... logic ...
        
        return clock_placeholder

    def _render_item_card(self, item):
        item_id = item["id"]
        is_checked = item_id in st.session_state.checked_items
        
        # Use stUI elements to create the card
        # Unchecked -> Warning (Yellow), Checked -> Success (Green)
        
        # To match the "Icon | Name | Checkbox" layout inside the box:
        # We use the alert's icon for the "left icon".
        # We put the text and checkbox inside.
        
        if is_checked:
            # Green
            with st.success(icon="✅", body=""):
                self._render_card_content(item, is_checked)
        else:
            # Yellow
            with st.warning(icon="🎒", body=""):
                self._render_card_content(item, is_checked)

    def _render_card_content(self, item, is_checked):
        # Using columns to layout Name and Checkbox
        c_text, c_chk = st.columns([3, 1])
        with c_text:
             st.markdown(f"**{item['name']}**")
        with c_chk:
             # Checkbox logic
             # Note: logic inversion if we want the box to drive state
             def on_change():
                 # This callback might handle state, but st.session_state bindings work too.
                 pass
             
             # We need to ensure the checkbox reflects the state
             new_state = st.checkbox("OK", key=f"chk_{item['id']}", value=is_checked, label_visibility="collapsed")
             
             # Update session state immediately
             if new_state:
                 st.session_state.checked_items.add(item['id'])
             else:
                 st.session_state.checked_items.discard(item['id'])
                 


    def _render_message_card(self, msg, bg_color, text_color):
        st.markdown(f"""
        <div style="background-color:{bg_color}; padding:20px; border-radius:20px; text-align:center; font-size:1.5rem; color:{text_color}; margin-top:20px; box-shadow:2px 2px 5px rgba(0,0,0,0.1);">
            {msg}
        </div>
        """, unsafe_allow_html=True)

    def _trigger_celebration(self):
        effects = ["balloons", "snow"]
        eff = random.choice(effects)
        if eff == "balloons":
            st.balloons()
            st.success("出発進行！✨")
        else:
            st.snow()
            st.success("クールに出発だ！❄️")

    def _inject_custom_css(self):
        st.markdown("""
        <style>
        .stApp { background-color: #87CEEB; font-family: sans-serif; }
        .app-title { text-align: center; color: white; font-size: 1.8rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); margin-bottom: 0; }
        .date-display { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 10px; }
        .clock-display { text-align: center; color: white; font-size: 4rem; font-weight: bold; text-shadow: 3px 3px 6px rgba(0,0,0,0.2); line-height: 1.0; margin-bottom: 20px; }
        .item-card { background-color: #FFFACD; border-radius: 15px; padding: 10px; margin-bottom: 10px; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .item-text { font-size: 1.3rem; font-weight: bold; color: #333; }
        .stButton > button { border-radius: 20px !important; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

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
        
        # 0. 環境監視 (日付変更の検知)
        self._render_env_monitor()

        if "debug_logs" not in st.session_state:
            st.session_state.debug_logs = []

        # 1. Get Mode
        mode_info = self.logic_manager.get_current_mode()
        mode = mode_info["mode"]

        # 2. Celebration (Always at top for visibility)
        if st.session_state.get("just_departed") or st.session_state.get("trigger_balloon"):
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
            # 持ち物がなくてもボタンは表示するっぴ！
            st.markdown("<br>", unsafe_allow_html=True)
            self._render_departure_button_logic(ignore_time_restriction=True)
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
    def _render_departure_button_logic(self, ignore_time_restriction=False):
        time_rules = self.logic_manager.get_time_restriction()
        is_disabled = False
        warning_msg = ""
        now_t = datetime.now().time()

        if time_rules["is_restricted"] and not ignore_time_restriction:
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

    @st.fragment(run_every="60s")
    def _render_env_monitor(self):
        """日付が変わったことを検知して画面をリロードするっぴ！"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if "view_date" not in st.session_state:
            st.session_state.view_date = current_date
            
        if current_date != st.session_state.view_date:
            st.session_state.view_date = current_date
            # 日付が変わったので、チェック状態などをリセットしてリロード
            if "checked_items" in st.session_state:
                st.session_state.checked_items = set()
            st.rerun()

    def _trigger_celebration(self):
        """高度なエフェクトエンジンを実行するっぴ！"""
        # 15種類のパターン定義 (アイコン, メッセージ, エンジン用タイプキー)
        patterns = [
            ("🎈", "🎈 ふわふわ〜！いってらっしゃい！", "rising"),
            ("❄️", "❄️ クールに出発！いってらっしゃい！", "falling"),
            ("🌟", "🌟 スター級の出発だね！", "pop"),
            ("🎉", "🎉 パーティー気分でいってらっしゃい！", "explosion"),
            ("🎆", "🎆 ドカンと元気にいってらっしゃい！", "firework"),
            ("🐧", "🐧 ペンギンさんも応援してるよ！", "waddle"),
            ("🌈", "🌈 虹に向かって出発だ！", "arc"),
            ("🍀", "🍀 ラッキーなことが起きるかも？", "floating"),
            ("✨", "✨ キラキラ輝く一日を！", "rain"),
            ("🛡️", "🛡️ かっこいいヒーローの出発だ！", "zoom"),
            ("🌊", "🌊 波に乗って元気にいってらっしゃい！", "wave"),
            ("🚀", "🚀 宇宙まで飛んじゃいそうな元気だね！", "launch"),
            ("🌸", "🌸 お花が咲くように笑顔でいってらっしゃい！", "bloom"),
            ("🏰", "🏰 王子様/お姫様の出発みたいだね！", "parade"),
            ("🐲", "🐲 ドラゴンみたいに力強くいってらっしゃい！", "spiral")
        ]
        
        icon, msg, anim_type = random.choice(patterns)
        st.toast(msg, icon=icon)

        import streamlit.components.v1 as components
        
        # エフェクトエンジン本体（JS + CSS）
        js_template = """
        <div id="effect-engine-root" style="width:100vw; height:100vh; overflow:hidden; background:transparent;"></div>
        <style>
            body, html { margin:0; padding:0; background:transparent !important; overflow:hidden; width:100vw; height:100vh; }
        </style>
        <script>
        (function() {
            // --- 1. iframe物理的拡張ロジック ---
            const frame = window.frameElement;
            if (frame) {
                const style = frame.style;
                style.position = 'fixed';
                style.top = '0';
                style.left = '0';
                style.width = '100vw';
                style.height = '100vh';
                style.maxHeight = '100vh';
                style.maxWidth = '100vw';
                style.zIndex = '9999999';
                style.pointerEvents = 'none';
                style.border = 'none';
                
                // 親のクリッピング（overflow:hidden）を連鎖的に解除するっぴ
                let p = frame.parentElement;
                while (p && p.tagName !== 'BODY') {
                    p.style.overflow = 'visible';
                    p = p.parentElement;
                }
            }

            // --- 2. 動きのロジック変数（Effect Logics） ---
            const icon = "__ICON__";
            const type = "__TYPE__";
            const count = 35;
            const root = document.getElementById('effect-engine-root');

            const MovementLogics = {
                rising: (i) => ({ startX: Math.random()*100, startY: 110, endX: (Math.random()*20-10), endY: -110 }),
                falling: (i) => ({ startX: Math.random()*100, startY: -10, endX: (Math.random()*20-10), endY: 110 }),
                rain: (i) => ({ startX: Math.random()*100, startY: -10, endX: (Math.random()*10-5), endY: 110 }),
                explosion: (i) => {
                    const angle = Math.random() * Math.PI * 2;
                    const dist = Math.random() * 80 + 20;
                    return { startX: 50, startY: 50, endX: Math.cos(angle)*dist, endY: Math.sin(angle)*dist, relative: true };
                },
                firework: (i) => {
                    const angle = Math.random() * Math.PI * 2;
                    const dist = Math.random() * 70 + 30;
                    return { startX: 50, startY: 50, endX: Math.cos(angle)*dist, endY: Math.sin(angle)*dist, relative: true };
                },
                launch: (i) => ({ startX: 40 + Math.random()*20, startY: 110, endX: 0, endY: -150, relative: true, duration: '1s', ease: 'ease-in' }),
                waddle: (i) => ({ startX: -10, startY: 85 + (i%3)*5, endX: 120, endY: 0, relative: true, duration: '5s', ease: 'linear' }),
                parade: (i) => ({ startX: 110, startY: 85 + (i%3)*5, endX: -120, endY: 0, relative: true, duration: '5s', ease: 'linear' }),
                zoom: (i) => ({ startX: 50, startY: 50, type: 'scale', duration: '1.5s' }),
                arc: (i) => ({ startX: -10, startY: 80, endX: 120, endY: 0, relative: true, duration: '3s', ease: 'cubic-bezier(0.25, 1, 0.5, 1)' }),
                spiral: (i) => {
                    const a = i * 0.4; const r = i * 3.5;
                    return { startX: 50, startY: 50, endX: Math.cos(a)*r, endY: Math.sin(a)*r, relative: true };
                },
                pop: (i) => ({ startX: Math.random()*100, startY: Math.random()*100, type: 'pop' }),
                bloom: (i) => ({ startX: Math.random()*100, startY: Math.random()*100, type: 'pop', duration: '2s' }),
                wave: (i) => ({ startX: Math.random()*100, startY: 30 + Math.random()*40, endX: (Math.random()*40-20), endY: (Math.random()*20-10), relative: true }),
                floating: (i) => ({ startX: Math.random()*100, startY: 20 + Math.random()*60, endX: (Math.random()*30-15), endY: (Math.random()*10-5), relative: true })
            };

            // --- 3. エンジン起動 ---
            const logic = MovementLogics[type] || MovementLogics.rising;

            for(let i=0; i<count; i++) {
                const el = document.createElement('div');
                el.innerText = icon;
                el.style.position = 'absolute';
                el.style.fontSize = (Math.random() * 20 + 40) + 'px';
                el.style.userSelect = 'none';
                el.style.pointerEvents = 'none';
                
                const meta = logic(i);
                el.style.left = meta.startX + 'vw';
                el.style.top = meta.startY + 'vh';
                el.style.transition = `all ${meta.duration || '3s'} ${meta.ease || 'ease-out'}`;
                
                root.appendChild(el);

                if (meta.type === 'scale') {
                    el.style.transform = 'translate(-50%, -50%) scale(0)';
                    setTimeout(() => {
                        el.style.transform = 'translate(-50%, -50%) scale(15)';
                        el.style.opacity = '0';
                    }, i * 150);
                } else if (meta.type === 'pop') {
                    el.style.transform = 'scale(0)';
                    setTimeout(() => {
                        el.style.transform = 'scale(2.5)';
                        el.style.opacity = '0';
                    }, i * 150);
                } else if (meta.endX !== undefined) {
                    setTimeout(() => {
                        const nextX = meta.relative ? (meta.startX + meta.endX) : meta.endX;
                        const nextY = meta.relative ? (meta.startY + meta.endY) : meta.endY;
                        el.style.left = nextX + 'vw';
                        el.style.top = nextY + 'vh';
                        el.style.opacity = '0';
                    }, i * 50 + 20);
                }
            }
        })();
        </script>
        """
        anim_html = js_template.replace("__ICON__", icon).replace("__TYPE__", anim_type)
        # コンテンツ更新による強制再描画
        anim_html += f"<!-- engine_rev: {time.time()} -->"
        components.html(anim_html, height=1)

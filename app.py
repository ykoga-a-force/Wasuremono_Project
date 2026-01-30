import streamlit as st
from models.db_manager import DatabaseManager
from models.logic_manager import LogicManager
from views.child_view import ChildView
from views.admin_view import AdminView
from views.achievement_view import AchievementView

# Page Config
st.set_page_config(
    page_title="Glancal Journey",
    page_icon="🎒",
    layout="centered"
)


# --- Initialization Caching ---
@st.cache_resource
def get_logic_manager():
    db_manager = DatabaseManager()
    return LogicManager(db_manager)

def main():
    # 1. Initialize MVP Components (Cached)
    logic_manager = get_logic_manager()
    
    # 2. Session State Management
    if "page" not in st.session_state:
        st.session_state.page = "main"

    # 3. Routing
    if st.session_state.page == "main":
        view = ChildView(logic_manager)
        view.render()
    
    elif st.session_state.page == "results":
        view = AchievementView(logic_manager)
        view.render()
        
    elif st.session_state.page == "admin":
        view = AdminView(logic_manager)
        view.render()

if __name__ == "__main__":
    main()

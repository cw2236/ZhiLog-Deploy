import streamlit as st
from components.sidebar import handle_file_upload
from components.pdf_viewer import render_pdf_viewer
from components.chat_interface import render_chat_interface, render_notes_chat_interface
from components.notes_interface import render_notes_interface

def initialize_session_state():
    """初始化会话状态"""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "pdf"
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "notes_chat_history" not in st.session_state:
        st.session_state["notes_chat_history"] = []
    if "notes_content" not in st.session_state:
        st.session_state["notes_content"] = ""
    if "directory_name" not in st.session_state:
        st.session_state["directory_name"] = ""
    if "has_notes" not in st.session_state:
        st.session_state["has_notes"] = False

def render_custom_sidebar():
    st.markdown(
        """
        <style>
        .custom-sidebar {
            font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
            background: #f7f9fa;
            height: 100vh;
            min-width: 320px;
            max-width: 350px;
            width: 350px;
            padding: 0;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            border-right: 1px solid #e5e7eb;
            position: fixed;
            left: 0;
            top: 0;
            z-index: 100;
        }
        .block-container {
            margin-left: 350px !important;
            max-width: 100vw;
            width: 100vw;
            padding: 0 !important;
        }
        </style>
        <div class="custom-sidebar">
            <div>
                <div class="sidebar-content" style="padding:0 24px;">
                    <div class="menu-btn-row" style="display:flex;align-items:center;gap:12px;margin-bottom:32px;">
                        <span style="font-size:22px;cursor:pointer;">&#9776;</span>
                        <form action="#" method="post" style="display:inline;"></form>
                        <span style="flex:1;"></span>
                        <span style="font-size:22px;cursor:pointer;">&#9654;</span>
                    </div>
                    <div style="margin-bottom:16px;">
                        <form action="#" method="post">
                            <button class="menu-btn" type="submit" name="new_chat" id="new_chat_btn" style="background:#f2f3f5;border:none;border-radius:24px;padding:8px 24px;font-size:18px;font-weight:500;color:#222;cursor:pointer;">+ New chat</button>
                        </form>
                    </div>
                    <div class="section-title" style="font-weight:bold;font-size:18px;margin:24px 0 8px 0;">Knowledge Map</div>
                    <div class="workspace" style="margin-bottom:24px;">
                        <div class="folder" style="font-weight:bold;font-size:16px;margin-bottom:4px;">Workspace</div>
                        <form method="post">
                            <button class="item-btn" name="generative_agents_btn" type="submit" style="margin-left:16px;font-size:15px;margin-bottom:2px;background:none;border:none;color:#222;text-align:left;cursor:pointer;padding:2px 0;width:100%;">1. Generative Agents</button>
                        </form>
                        <form method="post">
                            <button class="item-btn" name="quick_notes_btn" type="submit" style="margin-left:16px;font-size:15px;margin-bottom:2px;background:none;border:none;color:#222;text-align:left;cursor:pointer;padding:2px 0;width:100%;">✏️ 1.1 Quick Notes</button>
                        </form>
                    </div>
                    <div class="quick-action" style="margin-bottom:24px;">
                        <div class="quick-action-title" style="font-weight:bold;font-size:16px;margin-bottom:8px;">Quick Action</div>
                        <ul class="quick-action-list" style="list-style:none;padding:0;margin:0;">
                            <li style="display:flex;align-items:center;justify-content:space-between;color:#888;font-size:15px;margin-bottom:8px;"><form action="#" method="post" style="display:inline;"><button type="submit" name="help_btn" style="background:none;border:none;padding:0;color:#888;font-size:15px;">❗Help</button></form><span>•</span></li>
                            <li style="display:flex;align-items:center;justify-content:space-between;color:#888;font-size:15px;margin-bottom:8px;"><form action="#" method="post" style="display:inline;"><button type="submit" name="settings_btn" style="background:none;border:none;padding:0;color:#888;font-size:15px;">⚙️ Settings</button></form><span>•</span></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="sidebar-bottom" style="padding:0 24px 24px 24px;text-align:center;">
                <img class="avatar" src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=facearea&w=256&h=256" style="width:48px;height:48px;border-radius:50%;object-fit:cover;margin-bottom:8px;" />
                <div class="upgrade" style="font-weight:bold;color:#888;font-size:16px;">Upgrade Now !</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # 交互逻辑
    # New chat
    if st.session_state.get('new_chat_btn') or st.query_params.get('new_chat'):
        st.session_state.current_file = None
        st.session_state.chat_history = []
        st.session_state.selected_text = None
        st.session_state['new_chat_btn'] = False
        st.experimental_rerun()
    # Generative Agents
    if st.session_state.get('generative_agents_btn'):
        st.session_state["current_page"] = "pdf"
        st.session_state['generative_agents_btn'] = False
        st.experimental_rerun()
    # Quick Notes
    if st.session_state.get('quick_notes_btn'):
        st.session_state["current_page"] = "notes_chat"
        st.session_state['quick_notes_btn'] = False
        st.experimental_rerun()
    # Help
    if st.session_state.get('help_btn') or st.query_params.get('help_btn'):
        st.info("帮助信息弹窗（你可以自定义）")
        st.session_state['help_btn'] = False
    # Settings
    if st.session_state.get('settings_btn') or st.query_params.get('settings_btn'):
        st.info("设置弹窗（你可以自定义）")
        st.session_state['settings_btn'] = False

def main():
    st.set_page_config(page_title="ChatPDF", layout="wide")
    initialize_session_state()
    render_custom_sidebar()
    # 只用两栏，pdf viewer 和 chatbot
    col1, col2 = st.columns([2, 1.5], gap="large")
    with col1:
        if st.session_state["current_page"] == "pdf":
            uploaded_file = st.file_uploader(
                "上传 PDF 文件", type=["pdf"], key="main_pdf_uploader")
            if handle_file_upload(uploaded_file):
                st.success(f"文件 '{uploaded_file.name}' 上传成功！")
            render_pdf_viewer()
        else:
            render_notes_interface(read_only=False)
    with col2:
        if st.session_state["current_page"] == "pdf":
            render_chat_interface()
        else:
            render_notes_chat_interface()

if __name__ == "__main__":
    main() 
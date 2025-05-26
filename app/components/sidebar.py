import streamlit as st
import base64

def handle_file_upload(uploaded_file):
    """处理文件上传"""
    if uploaded_file is not None:
        # 将文件转换为 base64 编码
        pdf_data = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        
        # 存储文件信息到 session state
        if "pdf_files" not in st.session_state:
            st.session_state.pdf_files = {}
        
        # 只有当文件不存在时才添加
        if uploaded_file.name not in st.session_state.pdf_files:
            st.session_state.pdf_files[uploaded_file.name] = {
                "name": uploaded_file.name,
                "data": pdf_data
            }
            st.session_state.current_file = uploaded_file.name
            return True
    return False

def render_sidebar():
    st.markdown(
        '''
        <style>
        .custom-sidebar {
            font-family: "Inter", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
            background: #f7f9fa;
            height: 100vh;
            padding: 24px 0 0 0;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .custom-sidebar .top {
            padding: 0 24px;
        }
        .custom-sidebar .menu-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 32px;
        }
        .custom-sidebar .menu-btn button {
            background: #f2f3f5;
            border: none;
            border-radius: 24px;
            padding: 8px 24px;
            font-size: 18px;
            font-weight: 500;
            color: #222;
            cursor: pointer;
        }
        .custom-sidebar .section-title {
            font-weight: bold;
            font-size: 18px;
            margin: 24px 0 8px 0;
        }
        .custom-sidebar .workspace {
            margin-bottom: 24px;
        }
        .custom-sidebar .workspace .folder {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 4px;
        }
        .custom-sidebar .workspace .item {
            margin-left: 16px;
            font-size: 15px;
            margin-bottom: 2px;
        }
        .custom-sidebar .quick-action {
            margin-bottom: 24px;
        }
        .custom-sidebar .quick-action-title {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 8px;
        }
        .custom-sidebar .quick-action-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .custom-sidebar .quick-action-list li {
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #888;
            font-size: 15px;
            margin-bottom: 8px;
        }
        .custom-sidebar .bottom {
            padding: 0 24px 24px 24px;
            text-align: center;
        }
        .custom-sidebar .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 8px;
        }
        .custom-sidebar .upgrade {
            font-weight: bold;
            color: #888;
            font-size: 16px;
        }
        </style>
        <div class="custom-sidebar">
            <div>
                <div class="top">
                    <div class="menu-btn">
                        <span style="font-size:22px;cursor:pointer;">&#9776;</span>
                        <button>+ New chat</button>
                        <span style="font-size:22px;cursor:pointer;">&#9654;</span>
                    </div>
                    <div class="section-title">Knowledge Map</div>
                    <div class="workspace">
                        <div class="folder">Workspace</div>
                        <div class="item">1. Generative Agents</div>
                        <div class="item">✏️ 1.1 Quick Notes</div>
                    </div>
                </div>
                <div class="quick-action">
                    <div class="quick-action-title">Quick Action</div>
                    <ul class="quick-action-list">
                        <li><span>❗Help</span><span>•</span></li>
                        <li><span>⚙️ Settings</span><span>•</span></li>
                    </ul>
                </div>
            </div>
            <div class="bottom">
                <img class="avatar" src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=facearea&w=256&h=256" />
                <div class="upgrade">Upgrade Now !</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    # 显示文件列表
    if "pdf_files" in st.session_state and st.session_state.pdf_files:
        st.sidebar.markdown("### 已上传文件")
        
        for filename in st.session_state.pdf_files:
            if st.sidebar.button(
                f"📄 {filename}",
                key=f"file_{filename}",
                use_container_width=True
            ):
                st.session_state.current_file = filename
                st.session_state.chat_history = []  # 清空聊天历史
                st.session_state.selected_text = None  # 清空选中的文本 
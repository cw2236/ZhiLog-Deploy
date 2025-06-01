import streamlit as st

def render_notes_interface(read_only=False):
    """渲染笔记界面
    
    Args:
        read_only (bool): 是否为只读模式
    """
    # 笔记编辑区域
    st.subheader("�� 阅读笔记")
    
    # 如果是只读模式，使用 markdown 显示
    if read_only:
        if st.session_state.get("notes_content"):
            st.markdown(st.session_state["notes_content"])
        else:
            st.info("暂无笔记内容")
        return
    
    # 编辑模式下使用 text_area
    notes_content = st.text_area(
        "编辑笔记内容",
        value=st.session_state.get("notes_content", ""),
        height=300,
        key="notes_editor"
    )
    
    # 保存按钮
    if st.button("💾 保存笔记"):
        st.session_state["notes_content"] = notes_content
        st.success("笔记已保存！")
    
    # 导出按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 复制到剪贴板"):
            st.code(notes_content, language="text")
            st.success("笔记已复制到剪贴板！")
    with col2:
        if st.button("📥 导出为 TXT"):
            import base64
            b64 = base64.b64encode(notes_content.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="阅读笔记.txt">点击下载笔记</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("笔记已准备好下载！") 
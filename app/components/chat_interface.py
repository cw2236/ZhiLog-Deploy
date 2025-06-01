import streamlit as st
from openai import OpenAI
import base64
import os

def get_task_prompt(task_type, text):
    """根据任务类型生成提示词"""
    prompts = {
        "解释": f"请解释以下内容：\n\n{text}",
        "总结": f"请总结以下内容：\n\n{text}",
        "改写": f"请将以下内容改写为更清晰的表达：\n\n{text}"
    }
    return prompts.get(task_type, prompts["解释"])

def process_selected_text(text, task_type):
    """处理选中的文本"""
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-lxUWT88Z2f--5a-7CKZjxQ"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.ai.it.cornell.edu")
        )
        
        prompt = get_task_prompt(task_type, text)
        
        response = client.chat.completions.create(
            model="openai.gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个专业的文档分析助手，请根据用户的要求处理文本内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"处理文本时出错：{str(e)}")
        return None

def handle_task_button(task_type):
    """处理任务按钮点击"""
    selected_text = st.session_state.get("selected_text", "")

    if not isinstance(selected_text, str) or selected_text.strip() == "":
        st.warning("请先选择要处理的文本")
        return

    # 根据任务类型处理文本
    if task_type == "explain":
        prompt = f"请解释以下文本的含义：\n\n{selected_text}"
    elif task_type == "summarize":
        prompt = f"请总结以下文本的主要内容：\n\n{selected_text}"
    elif task_type == "rewrite":
        prompt = f"请用更简洁的语言重写以下文本：\n\n{selected_text}"
    else:
        st.error("未知的任务类型")
        return

    # 调用 OpenAI API
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-lxUWT88Z2f--5a-7CKZjxQ"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.ai.it.cornell.edu")
        )
        
        response = client.chat.completions.create(
            model="openai.gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个专业的文本分析助手，请用简洁明了的语言回答用户的问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # 获取回复内容
        reply = response.choices[0].message.content
        
        # 更新聊天历史
        st.session_state.chat_history.append({
            "role": "user",
            "content": f"【{task_type}】{selected_text}"
        })
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": reply
        })
        
        # 清空选中的文本
        st.session_state["selected_text"] = None
        
        # 刷新页面
        st.rerun()
        
    except Exception as e:
        st.error(f"处理文本时出错：{str(e)}")
        return None

def get_pdf_summary(pdf_content):
    """获取 PDF 摘要"""
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-lxUWT88Z2f--5a-7CKZjxQ"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.ai.it.cornell.edu")
        )
        
        prompt = f"""请对以下文档内容进行简要总结，包括：
1. 文档的主要主题
2. 关键要点
3. 重要结论

文档内容：
{pdf_content}
"""
        
        response = client.chat.completions.create(
            model="openai.gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个专业的文档分析助手，请用简洁明了的语言总结文档内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"生成摘要时出错：{str(e)}")
        return None

def render_pdf_summary():
    """渲染 PDF 摘要部分"""
    st.markdown("### 📑 文档摘要")
    
    # 检查是否有 PDF 内容
    if st.session_state.get("current_file"):
        # 如果有 PDF 内容，显示摘要
        if "pdf_summary" not in st.session_state and "pdf_text" in st.session_state:
            with st.spinner("正在生成文档摘要..."):
                summary = get_pdf_summary(st.session_state["pdf_text"])
                if summary:
                    st.session_state["pdf_summary"] = summary
        
        # 显示摘要内容
        if "pdf_summary" in st.session_state:
            st.markdown(st.session_state["pdf_summary"])
    else:
        # 如果没有 PDF，显示占位内容
        st.info("请上传 PDF 文档以查看摘要")

def render_chat_interface():
    """渲染聊天界面"""
    # 显示 PDF 摘要
    render_pdf_summary()
    
    st.markdown("---")
    
    # 初始化聊天历史
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    # 显示聊天历史
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 添加笔记导出按钮
    if st.button("📒 导出笔记", key="export_notes_btn"):
        handle_export_notes()
    
    # 用户输入区域
    if prompt := st.chat_input("输入您的问题..."):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # 添加用户问题到聊天历史
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })
        
        # 处理用户问题
        response = process_selected_text(prompt, "explain")
        if response:
            # 添加助手回复到聊天历史
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
            # 使用 st.rerun() 重新加载页面
            st.rerun()

def handle_export_notes():
    """处理笔记导出功能"""
    try:
        # 检查是否有聊天历史
        if not st.session_state.get("chat_history"):
            st.warning("没有可用的聊天记录来生成笔记")
            return
            
        # 构建提示词
        prompt = "请根据以下对话内容整理出一份结构化、条理清晰的阅读笔记：\n\n"
        for message in st.session_state["chat_history"]:
            role = "用户" if message["role"] == "user" else "AI助手"
            prompt += f"{role}: {message['content']}\n\n"
        
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-lxUWT88Z2f--5a-7CKZjxQ"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.ai.it.cornell.edu")
        )
        
        # 调用 OpenAI API 生成笔记
        with st.spinner("正在生成笔记..."):
            response = client.chat.completions.create(
                model="openai.gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的笔记整理助手，请根据对话内容生成结构化的阅读笔记。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            notes = response.choices[0].message.content
            
            # 保存笔记内容并切换到笔记问答界面
            st.session_state["notes_content"] = notes
            st.session_state["has_notes"] = True  # 设置笔记状态
            st.session_state["current_page"] = "notes_chat"
            st.rerun()
                    
    except Exception as e:
        st.error(f"生成笔记时出错: {str(e)}")
        return None

def render_notes_chat_interface():
    """渲染基于笔记的聊天界面"""
    st.subheader("📘 根据笔记继续提问")
    
    # 初始化笔记聊天历史
    if "notes_chat_history" not in st.session_state:
        st.session_state["notes_chat_history"] = []
    
    # 显示聊天历史
    for message in st.session_state["notes_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入区域
    if prompt := st.chat_input("输入您的问题..."):
        # 添加用户问题到聊天历史
        st.session_state["notes_chat_history"].append({
            "role": "user",
            "content": prompt
        })
        
        # 构建系统提示词，包含笔记内容
        system_prompt = f"""你是一个专业的学习助手。请基于以下笔记内容回答用户的问题：

{st.session_state.get("notes_content", "")}

请确保你的回答：
1. 准确反映笔记内容
2. 清晰易懂
3. 如果问题超出笔记范围，请明确说明
"""
        
        try:
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY", "sk-lxUWT88Z2f--5a-7CKZjxQ"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.ai.it.cornell.edu")
            )
            
            response = client.chat.completions.create(
                model="openai.gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # 添加助手回复到聊天历史
            st.session_state["notes_chat_history"].append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })
            
            # 刷新页面
            st.rerun()
            
        except Exception as e:
            st.error(f"处理问题时出错: {str(e)}")
            return None

# ... existing code ... 
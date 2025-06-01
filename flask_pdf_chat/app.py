from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, session
from flask_session import Session
import os
from werkzeug.utils import secure_filename
import openai
import PyPDF2
import hashlib
from datetime import datetime
import json
import shutil
import re
from flask_pdf_chat.agent import agent
from flask_pdf_chat.agent_logger import AgentOperationLogger

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session_data')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)
app.config['UPLOAD_FOLDER'] = 'flask_pdf_chat/uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

# 设置OpenAI API密钥
openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.base_url = "https://api.ai.it.cornell.edu"

# 清空 session 文件夹
session_dir = os.path.join(os.path.dirname(__file__), 'flask_session_data')
if os.path.exists(session_dir):
    shutil.rmtree(session_dir)
    os.makedirs(session_dir)

# 清空上传的 PDF 文件夹
upload_dir = os.path.join(os.path.dirname(__file__), 'flask_pdf_chat', 'uploads')
if os.path.exists(upload_dir):
    shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def extract_pdf_text(filepath):
    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def get_pdf_summary(pdf_text):
    """Get PDF summary"""
    try:
        client = openai.OpenAI()
        
        prompt = f"""Please briefly summarize the following document content, including:
1. Main topic of the document
2. Key points
3. Important conclusions

Document content:
{pdf_text[:3000]}  # Limit text length to avoid token overflow
"""
        
        response = client.chat.completions.create(
            model="openai.gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional document analysis assistant, please summarize the document content in concise and clear language."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

def extract_tags(note, max_tags=5, max_len=30):
    words = re.findall(r'\b[A-Za-z][A-Za-z0-9\-]{1,}\b', note)
    stopwords = set(['the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was', 'has', 'have', 'will', 'can', 'not', 'but', 'all', 'any', 'use', 'using', 'used', 'into', 'out', 'about', 'more', 'than', 'such', 'other', 'their', 'been', 'also', 'may', 'one', 'two', 'three', 'four', 'five'])
    tags = []
    for w in words:
        lw = w.lower()
        if lw not in stopwords and lw not in tags:
            tags.append(w)
        if len(tags) >= max_tags:
            break
    tag_str = ' '.join([f'#{t}' for t in tags])
    if len(tag_str) > max_len:
        tag_str = tag_str[:max_len] + '...'
    return tag_str

@app.route('/', methods=['GET', 'POST'])
def index():
    session.clear()
    pdf_url = session.get('pdf_url')
    if 'chat_sessions' not in session:
        session['chat_sessions'] = {}
    if 'pdf_text' not in session:
        session['pdf_text'] = ""
    if 'pdf_summary' not in session:
        session['pdf_summary'] = ""
    if 'selected_text' not in session:
        session['selected_text'] = ""
    if 'last_note' not in session:
        session['last_note'] = ""
    if 'note_chatbot_history' not in session:
        session['note_chatbot_history'] = []
    if request.method == 'POST':
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                pdf_url = url_for('uploaded_file', filename=filename)
                session['pdf_url'] = pdf_url
                session['pdf_filename'] = filename
                # 自动reset
                session['chat_sessions'] = {}
                session['pdf_text'] = ""
                session['pdf_summary'] = ""
                session['selected_text'] = ""
                session['last_note'] = ""
                session['note_chatbot_history'] = []
                # 提取PDF文本
                pdf_text = extract_pdf_text(filepath)
                session['pdf_text'] = pdf_text

                # 生成分块，健壮处理
                def chunk_text(text, chunk_size=1000, overlap=200):
                    if not text:
                        return []
                    chunks = []
                    start = 0
                    text_length = len(text)
                    while start < text_length:
                        end = min(start + chunk_size, text_length)
                        chunk = text[start:end]
                        chunks.append({
                            "content": chunk,
                            "start": start,
                            "end": end
                        })
                        # 防止死循环
                        if end == text_length:
                            break
                        start = end - overlap
                        if start < 0 or start >= text_length:
                            break
                    return chunks
                try:
                    chunks = chunk_text(pdf_text)
                    session['pdf_chunks'] = chunks
                except Exception as e:
                    print("chunk_text error:", e)
                    session['pdf_chunks'] = []
                # 生成PDF摘要
                summary = get_pdf_summary(pdf_text)
                if summary:
                    session['pdf_summary'] = summary
                session.modified = True
    has_note = bool(session.get('last_note', '').strip())
    return render_template('index.html',
                         pdf_url=session.get('pdf_url'),
                         chat_sessions=session.get('chat_sessions', {}),
                         pdf_summary=session.get('pdf_summary', ''),
                         selected_text=session.get('selected_text', ''),
                         mode='main',
                         note=session.get('last_note', ''),
                         note_chatbot_history=session.get('note_chatbot_history', []),
                         chat_history=[],
                         pdf_filename=session.get('pdf_filename', ''),
                         has_note=has_note
                         )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_reference_id(text, page):
    # Generate unique ID using reference text and page number
    return hashlib.md5(f'{text}__{page}'.encode('utf-8')).hexdigest()

@app.route('/select_text', methods=['POST'])
def select_text():
    data = request.get_json()
    text = data.get('text', '').strip()
    page = data.get('page', 1)
    bbox = data.get('bbox', None)
    if not text:
        return jsonify({'status': 'error', 'msg': 'No text selected'})
    ref_id = get_reference_id(text, page)
    if 'chat_sessions' not in session:
        session['chat_sessions'] = {}
    chat_sessions = session['chat_sessions']
    # 确保bbox为dict类型
    if bbox and isinstance(bbox, str):
        bbox = json.loads(bbox)
    chat_sessions[ref_id] = chat_sessions.get(ref_id, {
        'reference': text,
        'page': page,
        'bbox': bbox,
        'chat_history': [],
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    # 若已存在session，仅更新bbox
    if bbox:
        chat_sessions[ref_id]['bbox'] = bbox
    session['active_session'] = ref_id
    session.modified = True
    return jsonify({'status': 'success', 'session_id': ref_id, 'reference': text, 'page': page, 'bbox': bbox})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message')
    session_id = data.get('session_id')
    reference = data.get('reference', '')
    if not session_id:
        return jsonify({'status': 'error', 'msg': 'No session_id'})
    chat_sessions = session.get('chat_sessions', {})
    if session_id not in chat_sessions:
        return jsonify({'status': 'error', 'msg': 'Session not found'})
    chat_history = chat_sessions[session_id]['chat_history']
    reference_text = reference or chat_sessions[session_id].get('reference', '')

    # === 新增：用 reference_text 检索 chunk，拼接上下文 ===
    chunks = session.get('pdf_chunks', [])
    pdf_text = session.get('pdf_text', '')
    print("reference_text:", reference_text)
    print("pdf_text length:", len(pdf_text))
    print("chunks:", len(chunks))

    context = ""
    window_size = 1

    if reference_text and chunks:
        # 先用 in 查找所有包含 reference_text 的 chunk
        found = False
        for i, chunk in enumerate(chunks):
            if reference_text.strip() in chunk['content']:
                start = max(0, i - window_size)
                end = min(len(chunks), i + window_size + 1)
                context = ''.join([c['content'] for c in chunks[start:end]])
                found = True
                print(f"Found in chunk {i}, context length: {len(context)}")
                break
        # fallback: 用 find 定位 offset
        if not found and pdf_text:
            offset = pdf_text.find(reference_text.strip())
            print("offset:", offset)
            if offset >= 0:
                chunk_idx = -1
                for i, chunk in enumerate(chunks):
                    if chunk['start'] <= offset < chunk['end']:
                        chunk_idx = i
                        break
                if chunk_idx != -1:
                    start = max(0, chunk_idx - window_size)
                    end = min(len(chunks), chunk_idx + window_size + 1)
                    context = ''.join([c['content'] for c in chunks[start:end]])
                    print(f"Found by offset in chunk {chunk_idx}, context length: {len(context)}")
    if not context:
        print("Fallback to reference_text as context")
        context = reference_text

    print("Final context:", context[:300])  # 只打印前300字

    # === 构建 prompt ===
    print("context:", context)  # 调试用
    if not context:
        context = reference_text
    prompt = f"""你是一个专业的PDF文档助手。请只针对用户选中的内容进行回答，必要时可参考上下文信息，但不要泛泛总结上下文。

【选中内容】
{reference_text}

【上下文】
{context}

【用户问题】
{user_input}
"""

    # 调用OpenAI
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="openai.gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个专业的PDF文档助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    reply = response.choices[0].message.content
    now = datetime.now().strftime('%H:%M')
    chat_history.append({"role": "user", "content": user_input, "time": now, "reference": reference})
    chat_history.append({"role": "assistant", "content": reply, "time": now})
    session.modified = True
    return jsonify({"status": "success", "chat_history": chat_history})

@app.route('/delete_session', methods=['POST'])
def delete_session():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'status': 'error', 'msg': 'No session_id'})
    chat_sessions = session.get('chat_sessions', {})
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        session.modified = True
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'msg': 'Session not found'})

@app.route('/get_sessions', methods=['GET'])
def get_sessions():
    chat_sessions = session.get('chat_sessions', {})
    # 返回所有session及其历史
    return jsonify({'status': 'success', 'sessions': chat_sessions, 'active_session': session.get('active_session')})

@app.route('/reset', methods=['POST'])
def reset():
    session['chat_history'] = []
    session['pdf_text'] = ""
    session['pdf_summary'] = ""
    session.modified = True
    return jsonify({"status": "success"})

@app.route('/export_notes', methods=['POST'])
def export_notes():
    chat_sessions = session.get('chat_sessions', {})
    if not chat_sessions:
        session['last_note'] = ''
        return jsonify({"notes": "No Reference chat found, unable to export notes."})
    # Concatenate all session content
    notes = ""
    for idx, (sid, sess) in enumerate(chat_sessions.items(), 1):
        notes += f"Reference {idx}: {sess['reference']}\n"
        for msg in sess['chat_history']:
            if msg['role'] == 'user':
                notes += f"Q: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                notes += f"A: {msg['content']}\n"
        notes += "----\n"
    # Let AI further summarize
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="openai.gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional document note organizing assistant. Please organize the user's multi-turn Q&A history (with reference) into structured and clear notes."},
                {"role": "user", "content": notes}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        ai_notes = response.choices[0].message.content
        session['last_note'] = ai_notes
        session.modified = True
        return jsonify({"notes": ai_notes})
    except Exception as e:
        session['last_note'] = notes
        session.modified = True
        return jsonify({"notes": notes})

@app.route('/reset_reference', methods=['POST'])
def reset_reference():
    session['selected_text'] = ''
    session.modified = True
    return jsonify({'status': 'success'})

@app.route('/note_chat', methods=['GET'])
def note_chat():
    note = request.args.get('note')
    if note is not None:
        # 只有新note参数时才更新last_note
        if note != session.get('last_note', ''):
            session['last_note'] = note
            session.modified = True
        note_value = note
    else:
        note_value = session.get('last_note', '')
    note_chatbot_history = session.get('note_chatbot_history', [])
    pdf_filename = session.get('pdf_filename', '')
    has_note = bool(session.get('last_note', '').strip())
    return render_template('index.html',
        mode='note_chat',
        note=note_value,
        note_chatbot_history=note_chatbot_history,
        pdf_url=session.get('pdf_url'),
        chat_sessions=session.get('chat_sessions', {}),
        pdf_summary=session.get('pdf_summary', ''),
        selected_text=session.get('selected_text', ''),
        chat_history=[],
        pdf_filename=pdf_filename,
        has_note=has_note
    )

@app.route('/note_chat_ask', methods=['POST'])
def note_chat_ask():
    data = request.get_json()
    note = data.get('note', '')
    question = data.get('question', '')
    reference = data.get('reference', '')
    if not note or not question:
        return jsonify({'answer': 'Please enter notes and question first.'})
    now = datetime.now().strftime('%H:%M')
    system_prompt = "You are a professional note Q&A assistant."
    if reference:
        system_prompt += f"\n\nPlease prioritize answering with the following reference:\n{reference}"
    system_prompt += "\n\nIf needed, you can also refer to the notes:\n" + note
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="openai.gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=600
    )
    answer = response.choices[0].message.content
    # Key: always create a new list to avoid session tracking issues
    history = list(session.get('note_chatbot_history', []))
    history = history + [
        {'role': 'user', 'content': question, 'time': now, 'reference': reference},
        {'role': 'assistant', 'content': answer, 'time': now}
    ]
    session['note_chatbot_history'] = history
    session['last_note'] = note
    session.modified = True
    return jsonify({'answer': answer, 'history': history})

@app.route('/get_note_chat_history', methods=['GET'])
def get_note_chat_history():
    return jsonify({'history': session.get('note_chatbot_history', [])})

@app.route('/workspace')
def workspace():
    pdf_filename = session.get('pdf_filename', '')
    last_note = session.get('last_note', '')
    note_tags = extract_tags(last_note) if last_note else ''
    has_note = bool(last_note.strip())
    if pdf_filename:
        welcome_msg = f"""Hi Zonglin! Welcome back. Here's what I found from your last session:<br>
– You worked mainly on <a href='#' style='color:#2196F3;text-decoration:underline'>{pdf_filename}</a>.<br>
– You last edited 1 note.<br><br>
Would you like to reopen this file, or continue where you left off? 🗂️"""
    else:
        welcome_msg = "Welcome to your workspace! Please upload your PDF document to start your intelligent learning journey 🚀<br><br>please tell me what you want to study?"
    return render_template('workspace.html',
        pdf_filename=pdf_filename,
        last_note=last_note,
        note_tags=note_tags,
        welcome_msg=welcome_msg,
        now=datetime.now(),
        mode='workspace',
        has_note=has_note
    )

@app.route('/knowledge_map')
def knowledge_map():
    welcome_msg = "💡 Want a deeper knowledge structure?<br>I can help you connect a new document—either from your library or one you upload now."
    return render_template('knowledge_map.html', 
        welcome_msg=welcome_msg, 
        now=datetime.now(),
        pdf_filename=session.get('pdf_filename', ''),
        has_note=bool(session.get('last_note', '').strip()),
        mode='knowledge_map'
    )

@app.route('/agent_chat', methods=['POST'])
def agent_chat():
    """处理与 agent 的对话"""
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'error': '消息不能为空'}), 400
    
    try:
        # 调用 agent 处理用户输入
        response = agent.respond(user_input)
        
        # 保存对话历史
        if 'agent_chat_history' not in session:
            session['agent_chat_history'] = []
        
        session['agent_chat_history'].append({
            'user': user_input,
            'agent': response['response'],
            'guide_question': response['guide_question'],
            'tool_used': response['tool_used']
        })
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': f'处理消息时出错：{str(e)}'}), 500

@app.route('/get_agent_history')
def get_agent_history():
    """获取 agent 对话历史"""
    return jsonify(session.get('agent_chat_history', []))

@app.route('/agent_autorun', methods=['POST'])
def agent_autorun():
    data = request.get_json()
    user_goal = data.get('goal', '')
    if not user_goal:
        return jsonify({'error': '目标不能为空'}), 400
    steps = agent.autonomous_run(user_goal)
    return jsonify({'steps': steps})

# 注册日志API blueprint
try:
    from agent_logger import api_logger_bp
    app.register_blueprint(api_logger_bp)
except Exception:
    pass

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 
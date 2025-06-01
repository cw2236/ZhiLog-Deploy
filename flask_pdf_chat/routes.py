from flask import Flask, request, jsonify, render_template, session, url_for
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_summary(pdf_path):
    # 读取PDF文件
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    # 使用OpenAI生成摘要
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个专业的文档摘要助手。请为以下文本生成一个简洁的摘要。"},
            {"role": "user", "content": text[:4000]}  # 限制文本长度
        ]
    )
    return response.choices[0].message.content

def chunk_text(text, chunk_size=1000, overlap=200):
    """将文本分成重叠的块，并记录每个chunk的起止位置"""
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
        start = end - overlap
    return chunks

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return redirect(request.url)
        file = request.files['pdf_file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 读取PDF并分块
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            # 将文本分块
            chunks = chunk_text(text)
            
            # 存储到session
            session['pdf_chunks'] = chunks
            session['pdf_text'] = text  # 新增，便于后续查找offset
            session['pdf_filename'] = filename
            session['pdf_url'] = url_for('static', filename=f'uploads/{filename}')
            
            # 生成摘要
            summary = generate_summary(filepath)
            session['pdf_summary'] = summary
            
            return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question')
    selected_text = data.get('selected_text', '')
    selected_offset = data.get('selected_offset', None)  # 前端可传
    
    chunks = session.get('pdf_chunks', [])
    pdf_text = session.get('pdf_text', '')
    context = ""
    window_size = 1  # 前后各取1个chunk

    if selected_text:
        offset = None
        if selected_offset is not None:
            try:
                offset = int(selected_offset)
            except Exception:
                offset = None
        if offset is None and selected_text and pdf_text:
            offset = pdf_text.find(selected_text)
        chunk_idx = -1
        if offset is not None and offset >= 0:
            for i, chunk in enumerate(chunks):
                if chunk['start'] <= offset < chunk['end']:
                    chunk_idx = i
                    break
        if chunk_idx != -1:
            # 取前后 window_size 个 chunk
            start = max(0, chunk_idx - window_size)
            end = min(len(chunks), chunk_idx + window_size + 1)
            context = ''.join([c['content'] for c in chunks[start:end]])
        # fallback: 用内容查找
        if not context:
            for i, chunk in enumerate(chunks):
                if selected_text in chunk['content']:
                    start = max(0, i - window_size)
                    end = min(len(chunks), i + window_size + 1)
                    context = ''.join([c['content'] for c in chunks[start:end]])
                    break
    
    # 构建提示
    prompt = f"基于以下上下文回答问题：\n\n{context}\n\n问题：{question}"
    
    # 调用OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个专业的PDF文档助手。请基于提供的上下文回答问题。"},
            {"role": "user", "content": prompt}
        ]
    )
    
    return jsonify({
        'answer': response.choices[0].message.content,
        'context': context
    })

if __name__ == '__main__':
    app.run(debug=True)
 
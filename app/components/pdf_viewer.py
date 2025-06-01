import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import PyPDF2
import io
import base64

def extract_pdf_text(pdf_data):
    """从 PDF 数据中提取文本"""
    try:
        # 将 base64 数据转换为二进制
        pdf_bytes = base64.b64decode(pdf_data)
        
        # 使用 PyPDF2 读取 PDF
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # 提取所有页面的文本
        full_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        return full_text
    except Exception as e:
        st.error(f"提取文本时出错：{str(e)}")
        return None

def render_pdf_viewer():
    """渲染PDF查看器"""
    if "current_file" not in st.session_state or not st.session_state["current_file"]:
        st.warning("请先上传 PDF 文件")
        return

    # 获取当前文件的base64数据
    current_file = st.session_state["current_file"]
    if "pdf_files" not in st.session_state or current_file not in st.session_state.pdf_files:
        st.error("PDF文件数据丢失，请重新上传")
        return
        
    pdf_data = st.session_state.pdf_files[current_file]["data"]
    
    # 提取 PDF 文本
    if "pdf_text" not in st.session_state:
        with st.spinner("正在提取 PDF 文本..."):
            pdf_text = extract_pdf_text(pdf_data)
            if pdf_text:
                st.session_state["pdf_text"] = pdf_text
    
    # 创建一个空的占位符用于显示状态
    status_placeholder = st.empty()
    
    # 创建PDF查看器的HTML模板
    viewer_html = f"""
    <div style="width: 100vw; height: 800px; position: relative; margin: 0; padding: 0;">
        <div id="viewerContainer" style="width: 100%; height: 100%; overflow: auto; margin: 0; padding: 0;">
            <div id="viewer" class="pdfViewer" style="margin: 0; padding: 0;"></div>
        </div>
        <button id="confirmButton" style="
            position: fixed;
            display: none;
            padding: 8px 16px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            z-index: 1000;
        ">确认选择</button>
        <div id="debugInfo" style="
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            display: none;
        "></div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.min.js"></script>
    <script>
    // 配置PDF.js worker
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.worker.min.js';

    // 初始化变量
    let selectedText = '';
    let confirmButton = document.getElementById('confirmButton');
    let debugInfo = document.getElementById('debugInfo');
    let lastMouseUpEvent = null;

    // 调试函数
    function debug(message) {{
        console.log(message);
        debugInfo.textContent = message;
        debugInfo.style.display = 'block';
        setTimeout(() => {{
            debugInfo.style.display = 'none';
        }}, 3000);
    }}

    async function loadPDF() {{
        try {{
            debug('开始加载PDF...');
            // 从base64加载PDF
            const pdfData = atob('{pdf_data}');
            const loadingTask = pdfjsLib.getDocument({{data: pdfData}});
            const pdf = await loadingTask.promise;
            debug('PDF加载成功，共 ' + pdf.numPages + ' 页');
            
            // 渲染所有页面
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {{
                const page = await pdf.getPage(pageNum);
                const viewport = page.getViewport({{scale: 1.5}});
                
                // 创建页面容器
                const pageContainer = document.createElement('div');
                pageContainer.className = 'page';
                pageContainer.style.position = 'relative';
                pageContainer.style.width = viewport.width + 'px';
                pageContainer.style.height = viewport.height + 'px';
                pageContainer.style.margin = '10px auto';
                pageContainer.style.backgroundColor = 'white';
                pageContainer.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                document.getElementById('viewer').appendChild(pageContainer);
                
                // 创建canvas
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.width = viewport.width;
                canvas.height = viewport.height;
                pageContainer.appendChild(canvas);
                
                // 渲染PDF页面到canvas
                await page.render({{
                    canvasContext: context,
                    viewport: viewport
                }}).promise;
                
                // 创建文本层
                const textContent = await page.getTextContent();
                const textLayer = document.createElement('div');
                textLayer.className = 'textLayer';
                textLayer.style.width = viewport.width + 'px';
                textLayer.style.height = viewport.height + 'px';
                pageContainer.appendChild(textLayer);
                
                // 渲染文本层
                pdfjsLib.renderTextLayer({{
                    textContent: textContent,
                    container: textLayer,
                    viewport: viewport,
                    textDivs: []
                }});
            }}
            debug('PDF渲染完成');
        }} catch (error) {{
            console.error('Error loading PDF:', error);
            debug('PDF加载失败: ' + error.message);
            document.getElementById('viewer').innerHTML = '<div style="color: red; text-align: center; padding: 20px;">PDF加载失败，请刷新页面重试</div>';
        }}
    }}

    // 处理文本选择
    document.addEventListener('mouseup', (event) => {{
        const selection = window.getSelection();
        selectedText = selection.toString().trim();
        lastMouseUpEvent = event;
        
        if (selectedText) {{
            debug('选中文本: ' + selectedText.substring(0, 50) + '...');
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            confirmButton.style.display = 'block';
            confirmButton.style.left = (rect.left + rect.width/2 - 50) + 'px';
            confirmButton.style.top = (rect.bottom + 10) + 'px';
        }} else {{
            confirmButton.style.display = 'none';
        }}
    }});

    // 处理确认按钮点击
    confirmButton.addEventListener('click', () => {{
        if (selectedText) {{
            debug('发送选中文本到Streamlit...');
            // 设置全局变量
            window.confirmedText = selectedText;
            // 清除选择
            window.getSelection().removeAllRanges();
            confirmButton.style.display = 'none';
            selectedText = '';
        }}
    }});

    // 点击其他区域时隐藏确认按钮
    document.addEventListener('mousedown', (event) => {{
        if (event.target !== confirmButton && event.target !== lastMouseUpEvent?.target) {{
            confirmButton.style.display = 'none';
        }}
    }});

    // 加载PDF
    loadPDF();
    </script>

    <style>
    #viewerContainer {{
        background-color: #f5f5f5;
        padding: 0;
        margin: 0;
        width: 100%;
        height: 100%;
        overflow-x: auto;
    }}
    .textLayer {{
        position: absolute;
        left: 0;
        top: 0;
        right: 0;
        bottom: 0;
        overflow: hidden;
        opacity: 0.2;
        line-height: 1.0;
        pointer-events: auto;
    }}
    .textLayer > span {{
        color: transparent;
        position: absolute;
        white-space: pre;
        cursor: text;
        transform-origin: 0% 0%;
    }}
    .textLayer .highlight {{
        margin: -1px;
        padding: 1px;
        background-color: rgb(180, 0, 170);
        border-radius: 4px;
    }}
    .textLayer .highlight.selected {{
        background-color: rgb(0, 100, 0);
    }}
    </style>
    """
    
    # 显示PDF查看器
    st.components.v1.html(viewer_html, height=800) 
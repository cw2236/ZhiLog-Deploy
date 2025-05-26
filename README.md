# 📄 Flask PDF Chat & Agent Application

This project is a modern PDF chat/note/agent application. It supports PDF Q&A, note editing, citation, multi-step reasoning, agent operation flow visualization, and more. The backend is based on Flask, the frontend UI is highly similar to ChatGPT, and it supports Perplexity API for agent capabilities.

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2️⃣ Install Dependencies

Python 3.9+ is recommended. It is best to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 📦 Dependency Details

All dependencies are listed in `requirements.txt`. **It is highly recommended to install them all at once:**

| Package             | Purpose/Description                | Install Command                      |
|---------------------|------------------------------------|--------------------------------------|
| Flask               | Web framework                      | `pip install Flask`                  |
| FlaREMOVED_KEYSession       | Session persistence                | `pip install FlaREMOVED_KEYSession`          |
| PyPDF2              | PDF text extraction                | `pip install PyPDF2`                 |
| python-dotenv       | Load .env environment variables    | `pip install python-dotenv`          |
| requests            | HTTP requests                      | `pip install requests`               |
| beautifulsoup4      | HTML parsing                       | `pip install beautifulsoup4`         |
| duckduckgo-search   | DuckDuckGo search API              | `pip install duckduckgo-search`      |
| werkzeug            | Flask dependency, file upload      | `pip install werkzeug`               |
| Pillow              | Image processing (if used)         | `pip install Pillow`                 |
| streamlit*          | (Optional, for some features)      | `pip install streamlit`              |

> You can add or remove packages according to your actual `requirements.txt`.

To install all dependencies at once:

```bash
pip install -r requirements.txt
```

Or, to install individually:

```bash
pip install Flask FlaREMOVED_KEYSession PyPDF2 python-dotenv requests beautifulsoup4 duckduckgo-search werkzeug Pillow
```

---

### 3️⃣ Configure API Key

This project requires a Perplexity API Key ([Get one here](https://www.perplexity.ai/)).

1. Create a `.env` file in the project root directory with the following content:

    ```
    PPLX_API_KEY=your_perplexity_api_key
    ```

2. The `.env` file is already in `.gitignore` and will not be uploaded.

---

### 4️⃣ Start the Service

```bash
cd flask_pdf_chat
python app.py --port=5004
```

- Default port is 5003. You can specify another port with `--port=xxxx`.

---

### 5️⃣ Access the App

Open your browser and visit [http://localhost:5004](http://localhost:5004)  
You can now enjoy PDF chat, note-taking, multi-step agent reasoning, and more.

---

## ✨ Main Features

- **PDF Q&A**: Upload PDFs, select text, and get precise answers based on the cited content.
- **Note Editing & Q&A**: Rich text note editing and Q&A based on your notes.
- **Multi-step Agent Reasoning**: Automatically chain tools like web_search, summarize, add_note to accomplish complex goals.
- **Agent Operation Flow Visualization**: Visualize all agent tool calls, with refresh, scroll, and color highlights.
- **ChatGPT-like UI**: Sidebar, PDF viewer, chatbot, note area, and more for a smooth experience.
- **API Key Security**: All sensitive info is managed via `.env` for security and compliance.

---

## 🛠️ Project Structure

```
flask_pdf_chat/
    app.py                # Flask main app
    agent.py              # Agent and toolchain logic
    agent_logger.py       # Operation flow logger
    templates/            # Frontend HTML templates
    static/               # Frontend static assets
    ...
requirements.txt          # Dependency list
.env                      # API Key (local only, not uploaded)
```

---

## 📝 FAQ

- **API Key Error**: Make sure `.env` is correctly filled and in the project root, and `PPLX_API_KEY` is valid.
- **Dependency Issues**: If you encounter missing packages, run `pip install -r requirements.txt`.
- **Port Conflict**: Use `python app.py --port=xxxx` to specify another port.

---

## 👥 Contribution

PRs, issues, and suggestions are welcome!

 

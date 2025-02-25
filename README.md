# 📌 INFO-5940

## RAG Chatbot

Welcome to the INFO-5940 RAG Chatbot repository! This chatbot is a Retrieval-Augmented Generation (RAG) system powered by OpenAI models and LangChain. It enables users to upload documents (PDF and TXT) and retrieve relevant information from them using semantic search and conversational AI. The chatbot is implemented using Streamlit for the user interface and ChromaDB for vector storage.

---

## 🛠️ Prerequisites

Before starting, ensure you have the following installed on your system:

- Docker (Ensure Docker Desktop is running)
- VS Code
- VS Code Remote - Containers Extension
- Git
- OpenAI API Key

---

## 🚀 Setup Guide

### 1️⃣ Clone the Repository

Open a terminal and run:

```sh
git clone https://github.com/cw2236/INFO-5940.git
cd INFO-5940
```

### 2️⃣ Configure OpenAI API Key

Since `docker-compose.yml` expects environment variables, follow these steps:

#### ➤ Option 1: Set the API Key in `.env` (Recommended)

Inside the project folder, create a `.env` file:

```sh
touch .env
```

Add your API key and base URL:

```plaintext
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.ai.it.cornell.edu/
TZ=America/New_York
```

Make sure the `docker-compose.yml` include this `.env` file:

```yaml
version: '3.8'
services:
  devcontainer:
    container_name: info-5940-devcontainer
    build:
      dockerfile: Dockerfile
      target: devcontainer
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - TZ=${TZ}
    volumes:
      - '$HOME/.aws:/root/.aws'
      - '.:/workspace'
    env_file:
      - .env
```

Restart the container:

```sh
docker-compose up --build
```

Now, your API key will be automatically loaded inside the container.

---
### 3️⃣ Open in VS Code with Docker

1. Open VS Code and navigate to the project folder.
2. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac) and search for:
   ```
   Remote-Containers: Rebuild and Reopen in Container"
   ```
3. Select this option. VS Code will build and open the project inside the container.

📌 **Note:** If you don’t see this option, ensure that the Remote - Containers extension is installed.

---



### 4️⃣ Install Additional Libraries (If Needed)

```sh
pip install -U langchain-chroma
pip install pdfminer.six
```

---

### 5️⃣ Running the Chatbot

Once the setup is complete, run the chatbot with the following command:

```
streamlit run Chatbot_A1.py
```

---

## 📌 Features

- Upload and process PDF and TXT documents.
- Store document embeddings using ChromaDB.
- Retrieve relevant document sections using similarity search.
- Generate responses using OpenAI's GPT-4o model.
- Maintain conversation history within a session.

---

## 📂 File Upload Processing

- Uploaded files are saved in the `uploaded_docs` directory.
- Documents are split into chunks for efficient retrieval.
- Chunks are stored in ChromaDB for similarity search.

---

## 📌 RAG Pipeline

1. **Document Upload:** Users upload PDF/TXT files.
2. **Text Processing:** Extracted text is chunked using `RecursiveCharacterTextSplitter`.
3. **Vector Storage:** Chunks are embedded and stored in ChromaDB.
4. **Retrieval:** Similar document chunks are retrieved based on user queries.
5. **Generation:** Retrieved content is used to generate an answer using GPT-4o.

---

## 📝 Documentation of Configuration Changes

- Added `.env` file for managing API keys securely.
- Configured `docker-compose.yml` to load environment variables from `.env`.
- Used `ChromaDB` for efficient vector storage and retrieval.
- Implemented `Streamlit` for an interactive user interface.

---

## 🙏 Acknowledgement

This project is developed as part of INFO-5940 at Cornell University.

 
import streamlit as st
from openai import OpenAI
from os import environ
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PDFMinerLoader, TextLoader 
from langchain.chains import ConversationalRetrievalChain

st.title("RAG Chatbot")
st.caption("Powered by INFO-5940")

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Initialize OpenAI embedding
embedding_model = OpenAIEmbeddings(model="openai.text-embedding-3-large")
vector_store = Chroma(embedding_function=embedding_model, persist_directory='chroma_db')

# File Upload
st.sidebar.header("Upload Documents")
uploaded_files = st.sidebar.file_uploader("Upload your documents", type=["txt", "pdf"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        # Process PDF and TXT
        if uploaded_file.name.endswith(".pdf"):
            loader = PDFMinerLoader(file_path) 
        else:
            loader = TextLoader(file_path)

        documents = loader.load()

        # Semantic Chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        
        # Save to ChromaDB
        vector_store.add_documents(chunks)

    st.sidebar.success("Files uploaded and processed successfully!")

if prompt := st.chat_input():
    client = OpenAI(api_key=environ['OPENAI_API_KEY'])
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # RAG
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    llm = ChatOpenAI(model="openai.gpt-4o", temperature=0.2)

    template = """
        You are an assistant for question-answering tasks. Use the following retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        
        Question: {question} 
        
        Context: {context} 
        
        Answer:
    """
    prompt_template = PromptTemplate.from_template(template)

    rag_chain = (
        {"context": retriever | (lambda docs: "\n\n".join(doc.page_content for doc in docs)), "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    # Stream the message for better user experience
    with st.chat_message("assistant"):
        stream = rag_chain.stream(prompt) 
        response = st.write_stream(stream)  

    st.session_state.messages.append({"role": "assistant", "content": response})
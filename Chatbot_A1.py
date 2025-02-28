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

        # Add metadata (source file name) to each document
        for doc in documents:
            doc.metadata["source"] = uploaded_file.name  # Store document source

        # Semantic Chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)

        # Ensure each chunk carries metadata before storing
        for chunk in chunks:
            chunk.metadata["source"] = uploaded_file.name  # Attach source file name to each chunk

        # Save to ChromaDB
        vector_store.add_documents(chunks)  # Store with metadata

    st.sidebar.success("Files uploaded and processed successfully!")

if prompt := st.chat_input():
    client = OpenAI(api_key=environ['OPENAI_API_KEY'])
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # RAG - Retrieve relevant chunks with metadata
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})
    llm = ChatOpenAI(model="openai.gpt-4o", temperature=0.0)

    # Generate formatted context with source information
    def format_documents(docs):
        formatted_texts = []
        sources = set()  # Track sources to mention in response
        for doc in docs:
            source = doc.metadata.get("source", "Unknown Source")
            sources.add(source)
            formatted_texts.append(f"📄 Source: {source}\n{doc.page_content}")
        
        formatted_context = "\n\n".join(formatted_texts)
        return formatted_context, sources  # Return context + sources

    retrieved_docs = retriever.invoke(prompt)
    context, sources = format_documents(retrieved_docs)

    # Build LLM prompt template
    # Prompt tailored for answering domain-specific questions (but give flexibility to answer other questions with special notification to users)
    template = """

        You are an assistant for question-answering tasks. Follow these steps to answer the question:


            First, check the provided context below, and try to answer the question based only on the context provided.

            then if the context does not help or is empty :
                try to answer it with your own knowledge
                say: The provided context does not contain relevant information about the question, so I answered it by my previous knowledge
            else:
                say: I don't know. 


        Question: {question} 
        
        Context: {context} 
        
        Answer:
    """
    prompt_template = PromptTemplate.from_template(template)

    rag_chain = (
        {"context": lambda _: context, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    # Generate response
    with st.chat_message("assistant"):
        response = rag_chain.invoke(prompt)

        # Append document sources at the end of the response
        if sources:
            response += f"\n\n(Source: {', '.join(sources)})"

        st.write(response)

    # Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

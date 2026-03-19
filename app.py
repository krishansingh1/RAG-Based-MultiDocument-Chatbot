# app.py
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

from extractors import extract_text
from llm_provider import get_llm, list_models

# Load environment variables
load_dotenv()


# ── 1. Text Extraction (now supports all file types) ──

def get_document_text(uploaded_files):
    """Extract text from all uploaded files regardless of type."""
    all_text = ""
    for file in uploaded_files:
        try:
            text = extract_text(file)
            # Tag the text with source filename for traceability
            all_text += f"\n\n--- Source: {file.name} ---\n{text}"
        except ValueError as e:
            st.warning(f"Skipped {file.name}: {e}")
    return all_text


# ── 2. Chunking ──

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=1000,
    )
    return splitter.split_text(text)


# ── 3. Vector Store ──

def build_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


# ── 4. QA Chain with Multi-LLM support ──

def get_qa_chain(model_key):
    prompt_template = """
    You are a helpful assistant that answers questions ONLY using the
    provided context from uploaded documents. Follow these rules strictly:

    1. Answer the question as detailed as possible from the provided context.
    2. If the answer is NOT in the context, say: "This information is not
       available in the uploaded documents."
    3. NEVER make up information or use knowledge outside the context.
    4. If relevant, mention which source document the information comes from.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    model = get_llm(model_key)
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
    )
    return prompt | model | StrOutputParser()


# ── 5. Handle User Question ──

def handle_question(user_question, model_key):
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    db = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )

    docs = db.similarity_search(user_question, k=5)
    context = "\n\n".join(doc.page_content for doc in docs)
    chain = get_qa_chain(model_key)
    return chain.invoke({"context": context, "question": user_question})


# ── 6. Streamlit UI ──

def main():
    st.set_page_config(
        page_title="Multi-Doc RAG Agent",
        page_icon="",
        layout="wide",
    )
    st.header("Multi-Document RAG Agent")
    st.caption("Upload PDFs, Word docs, PowerPoints, or Excel files — then ask questions about them.")

    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "docs_processed" not in st.session_state:
        st.session_state.docs_processed = False

    # ── Sidebar ──
    with st.sidebar:
        st.title("Settings")

        # LLM selector
        models = list_models()
        selected_model = st.selectbox(
            "Choose LLM",
            options=list(models.keys()),
            format_func=lambda k: models[k],
        )

        st.divider()
        st.title("Upload Documents")

        uploaded_files = st.file_uploader(
            "Supported: PDF, DOCX, PPTX, XLSX",
            accept_multiple_files=True,
            type=["pdf", "docx", "pptx", "xlsx"],
        )

        if st.button("Submit & Process", type="primary"):
            if not uploaded_files:
                st.warning("Please upload at least one file.")
            else:
                with st.spinner("Extracting text..."):
                    raw_text = get_document_text(uploaded_files)

                if not raw_text.strip():
                    st.error("No text could be extracted from the uploaded files.")
                else:
                    with st.spinner("Chunking text..."):
                        chunks = get_text_chunks(raw_text)

                    with st.spinner(f"Building vector index ({len(chunks)} chunks)..."):
                        build_vector_store(chunks)

                    st.session_state.docs_processed = True
                    st.session_state.chat_history = []
                    st.success(f" Processed {len(uploaded_files)} file(s) into {len(chunks)} chunks!")

        st.divider()
        if st.button("Clear Chat"):
            st.session_state.chat_history = []

    # ── Chat Area ──
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        if not st.session_state.docs_processed:
            st.warning("Please upload and process documents first.")
        else:
            # Show user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and show assistant response
            with st.chat_message("assistant"):
                with st.spinner("Searching documents..."):
                    response = handle_question(prompt, selected_model)
                st.markdown(response)

            st.session_state.chat_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
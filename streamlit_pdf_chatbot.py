# streamlit_chatbot.py - This file runs in your web browser using Streamlit

import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.Youtubeing import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Helper Functions (Identical to the terminal version, but included here for completeness) ---

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    return splitter.split_text(text)

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index") # This will create/update 'faiss_index' folder

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context.
    If the answer is not in the context, just say "Answer is not available in the context."
    Do not make up any answer.

    Context:\n{context}\n
    Question:\n{question}\n
    Answer:
    """
    # Note: You used 'gemini-pro' here, in terminal you used 'chat-bison-001'. Choose one or keep as is.
    model = ChatGoogleGenerativeAI(model="models/gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def process_user_question_streamlit(user_question): # Renamed for clarity in this file
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    try:
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        st.write("🤖 Reply:", response["output_text"])
    except Exception as e:
        st.error(f"Error processing question: {e}. Make sure a PDF has been processed and a vector store created.")


# --- STREAMLIT UI CODE - This is the main function that builds your web page ---
def main_streamlit_app():
    st.set_page_config(page_title="Chat with PDF using Gemini", layout="wide")
    st.header("📄 Chat with your PDF using Gemini")

    # Sidebar for PDF upload and processing
    with st.sidebar:
        st.title("Upload PDFs")
        pdf_docs = st.file_uploader("Upload your PDF files", type=["pdf"], accept_multiple_files=True)
        if st.button("Submit & Process"):
            if pdf_docs:
                with st.spinner("🔄 Processing..."):
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    get_vector_store(text_chunks) # This creates the faiss_index
                    st.success("✅ Processing complete!")
                st.info("Now you can ask questions about the uploaded PDF(s) in the main chat area.")
            else:
                st.warning("⚠️ Please upload at least one PDF.")

    # Main area for user interaction (question input)
    user_question = st.text_input("💬 Ask a question from the PDF:")
    if user_question:
        process_user_question_streamlit(user_question) # Calls the Streamlit-specific input function

if __name__ == "__main__":
    main_streamlit_app() # This is the entry point when you run `streamlit run this_file.py`
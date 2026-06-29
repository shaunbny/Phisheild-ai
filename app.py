import os
from dotenv import load_dotenv
load_dotenv()
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

prompt = ChatPromptTemplate.from_template(
    """You are an elite, empathetic cybersecurity incident advisor. 
Analyze the user's suspicious content using ONLY the verified threat database below.

Database Context:
{context}

Suspicious User Content to Analyze: {question}

Provide a structured response:
1. VERDICT: State clearly if it is a Scam/Phishing/Safe and name the threat category.
2. THREAT REASONING: Explain exactly why it looks like a scam based on the indicators.
3. ACTION STEPS: Give the victim clear, ordered steps on what to do right now.
4. HELP PORTAL: Provide the official reporting channels mentioned in the context.

Answer:"""
)

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)
def analyze_threat_rag(normalized_user_text):
    """
    Takes a clean text string (from text box, OCR, or Whisper voice),
    queries the local FAISS database, and generates the AI security response.
    """
    try:
        with open("cyber_threat_db.txt", "r", encoding="utf-8") as f:
            raw_text = f.read()
        documents = [Document(page_content=raw_text)]
    except Exception as e:
        return f"Error loading database file. Ensure cyber_threat_db.txt is in this folder. Details: {str(e)}"
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    store = FAISS.from_documents(chunks, embeddings)
    retriever = store.as_retriever(search_kwargs={"k": 2})

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain.invoke(normalized_user_text)



import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain Core Imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")

# 1. Initialize FastAPI Application Wrapper
app = FastAPI(title="PhishShield AI Core Engine")

# 2. Configure Strict Cybersecurity RAG System Prompt
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

# 3. Establish Vector Database Retrieval Brain
try:
    with open("cyber_threat_db.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()
    documents = [Document(page_content=raw_text)]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    store = FAISS.from_documents(chunks, embeddings)
    retriever = store.as_retriever(search_kwargs={"k": 2})
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}

        | prompt | llm | StrOutputParser()
    )
except Exception as e:
    print(f"CRITICAL: Failed to initialize RAG core dependencies: {str(e)}")

# 4. API Request Schema Definition
class ThreatQuery(BaseModel):
    text: str

# 5. Define Secure API Routing Endpoint
@app.post("/api/analyze")
async def analyze_endpoint(query: ThreatQuery):
    if not query.text.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
    try:
        verdict = rag_chain.invoke(query.text)
        return {"status": "success", "analysis": verdict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference Failure: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    try:
        uvicorn.run(app, host=host, port=port)
    except OSError as exc:
        if getattr(exc, "errno", None) == 10048:
            print(f"ERROR: Port {port} is already in use. Set PORT to a free port or stop the service using it.")
            sys.exit(1)
        raise

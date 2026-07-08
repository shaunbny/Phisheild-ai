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

# 2. Configure Balanced Cybersecurity RAG System Prompt
# ─── THE FINAL ACCURATE CYBERSECURITY PROMPT ───
prompt = ChatPromptTemplate.from_template(
    """You are an elite, objective, and deeply analytical cybersecurity incident advisor. 
Analyze the user's suspicious content using the verified threat database below.

CRITICAL EVALUATION PROTOCOLS:
1. MAJOR BRAND RULE: Global brands (such as Netflix, Amazon, Google, Microsoft, or major banks) use perfect, automated system templates. If an incoming message claims to be from a major brand but uses generic greetings (like "Hi Dear", "Dear Customer"), contains grammar/spelling errors, or uses informal phrasing (like "Your friends at Netflix"), you must immediately classify it as a SCAM / PHISHING attempt. Major brands never communicate this way.
2. DISCIPLINED VERDICT MATRIX: Classify content as LEGITIMATE/SAFE only if it is entirely free of high-pressure demands, unprompted links, or unsolicited 2FA codes. If it demands urgent billing updates via an immediate link or button, it is a phishing trap.
3. If it matches a documented attack scenario in your database (e.g., tech support scam, fake bank hold, crypto extraction, courier fee trap), classify it as SCAM or PHISHING.

Database Context:
{context}

Suspicious User Content to Analyze: {question}

Provide a structured response using clear markdown fields:
1. VERDICT: State clearly if it is a [Scam], [Phishing], or [Legitimate/Safe Alert] along with the calculated threat category.
2. THREAT REASONING: Explain your objective breakdown. Highlight the specific markers (like generic greetings, forced urgency, informal sign-offs, or suspicious links) that indicate an attack.
3. ACTION STEPS: Give the user clear, prioritized steps on what to do right now (e.g., do NOT click links; log in natively via the official website to check status).
4. HELP PORTAL: Provide the official reporting channels or corporate safety links mentioned in the context (e.g., cybercrime.gov.in).

Answer:"""
)



def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

# Global tracking placeholder definition to prevent structural scope errors
rag_chain = None

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
    
    # Unified chain pipeline configuration
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}

        | prompt | llm | StrOutputParser()
    )
    print("💡 SUCCESS: Balanced RAG core pipeline built successfully!")
except Exception as e:
    print(f"CRITICAL: Failed to initialize RAG core dependencies: {str(e)}")

# 4. API Request Schema Definition
class ThreatQuery(BaseModel):
    text: str

# 5. Define Secure API Routing Endpoint
@app.post("/api/analyze")
async def analyze_endpoint(query: ThreatQuery):
    global rag_chain
    if not query.text.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
        
    if rag_chain is None:
        raise HTTPException(
            status_code=500, 
            detail="The RAG pipeline variable is uninitialized. Check backend terminal for startup download blocks."
        )
        
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

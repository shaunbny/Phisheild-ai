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
    """You are an elite, OBJECTIVE, and deeply analytical cybersecurity advisor.
Your job is to ACCURATELY classify user content as either SAFE or DANGEROUS. You must NOT assume the content is malicious. Evaluate it fairly.

CRITICAL EVALUATION PROTOCOL — FOLLOW THIS EXACT ORDER:

STEP 1 — LEGITIMACY-FIRST CHECK (do this BEFORE looking for threats):
  - Is this a normal notification, order confirmation, shipping update, OTP, account statement, app alert, system message, newsletter, or routine business email?
  - Does it come from a verified/official sender with no suspicious indicators?
  - Is this a standard two-factor authentication code, delivery update, or purchase receipt?
  - If YES to any of the above → classify as [Legitimate/Safe] immediately. Do NOT look for threat matches.

STEP 2 — ONLY if Step 1 did NOT classify it as safe, check for threats:
  a) MAJOR BRAND RULE: If content claims to be from a global brand (Netflix, Amazon, Google, banks) but uses generic greetings ("Hi Dear"), grammar errors, or informal phrasing → classify as [Scam/Phishing].
  b) URGENCY + LINK TRAP: If it demands urgent action (account suspended, billing update) AND includes a suspicious link → classify as [Phishing].
  c) PAYMENT DEMAND: If it asks for money transfers, advance fees, ransom, or "safe escrow" payments → classify as [Scam].
  d) PERSONAL DATA REQUEST: If it asks for passwords, OTPs, PINs, card numbers, or bank credentials → classify as [Phishing].
  e) DATABASE MATCH: If it closely matches a documented attack pattern from the Database Context below → classify accordingly.

STEP 3 — CONTEXT RELEVANCE GATE:
  - The Database Context below contains known threat patterns. ONLY use it if the content genuinely matches a described attack scenario.
  - If the Database Context is UNRELATED to the user's content, COMPLETELY IGNORE it. Do NOT force a match.
  - Many normal messages (receipts, OTPs, app notifications) will retrieve threat context by coincidence — you must NOT let irrelevant context bias your verdict.

Database Context:
{context}

User Content to Analyze: {question}

Provide a structured, CONCISE response (max 2-3 sentences per section):
1. VERDICT: [Scam], [Phishing], or [Legitimate/Safe] — along with the threat category if dangerous, or "No Threat Detected" if safe.
2. THREAT REASONING: Explain your objective breakdown. If safe, explain WHY it is safe. If dangerous, highlight the specific attack markers.
3. ACTION STEPS: 1-2 prioritized steps (for safe content: "No action needed" or general safety tips).
4. HELP PORTAL: Provide official reporting channels if dangerous, or the sender's official support page if safe.

Answer:"""
)



def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

def relevance_filtered_retrieval(query):
    """Only include threat database context if it is actually relevant to the query.
    Uses FAISS similarity scores — lower score = more similar.
    If the best match score is too high (i.e., not relevant), return no context."""
    docs_with_scores = store.similarity_search_with_score(query, k=2)
    RELEVANCE_THRESHOLD = 1.35  # FAISS L2 distance; lower = more relevant
    relevant_docs = [doc for doc, score in docs_with_scores if score < RELEVANCE_THRESHOLD]
    if not relevant_docs:
        return "No closely matching threat patterns found in the database. Evaluate based on your own expertise."
    return format_docs(relevant_docs)

# Global tracking placeholder definition to prevent structural scope errors
rag_chain = None
store = None

# 3. Establish Vector Database Retrieval Brain
try:
    with open("cyber_threat_db.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()
    documents = [Document(page_content=raw_text)]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    store = FAISS.from_documents(chunks, embeddings)
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    # Unified chain pipeline with relevance-filtered retrieval
    rag_chain = (
        {"context": relevance_filtered_retrieval, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )
    print("SUCCESS: Balanced RAG core pipeline built successfully!")
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

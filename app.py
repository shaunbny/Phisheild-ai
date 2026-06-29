import os
import gradio as gr
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from groq import Groq

# LangChain Packaged Imports (Person 1's Backend Infrastructure)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Environment and Key Variable Initializations
load_dotenv()

# Secure fallback lookup mapping for your Groq API Key
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")

# Set up global models and client instances
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Optional Windows Tesseract path mapping override fix if needed:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# 2. Strict Expert Cybersecurity System Prompt
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


# 3. Person 1 Work: Core RAG Vector Storage & Pipeline Execution Engine
def run_rag_pipeline(normalized_user_text):
    # Step A: Load your custom threat text database natively
    try:
        with open("cyber_threat_db.txt", "r", encoding="utf-8") as f:
            raw_text = f.read()
        documents = [Document(page_content=raw_text)]
    except Exception as e:
        return f"Error loading database file. Ensure cyber_threat_db.txt is in this folder. Details: {str(e)}"
    
    # Step B: Segment database into crisp semantic blocks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    
    # Step C: Turn chunks into vector values using a free local embedder mapping model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    store = FAISS.from_documents(chunks, embeddings)
    retriever = store.as_retriever(search_kwargs={"k": 2})

    # Step D: Construct the operational LangChain Expression pipeline layout
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain.invoke(normalized_user_text)


# 4. Person 2 Work: Multimodal Input Preprocessor Logic
def process_multimodal_inputs(text_msg, screenshot, voice_msg):
    combined_content = []

    if text_msg and text_msg.strip():
        combined_content.append(f"[User Description]: {text_msg.strip()}")

    if screenshot is not None:
        try:
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(screenshot)

            extracted_text = pytesseract.image_to_string(screenshot)

            if extracted_text and extracted_text.strip():
                combined_content.append(f"[Extracted from Screenshot]:\n{extracted_text.strip()}")
            else:
                combined_content.append("[Extracted from Screenshot]:\n(No readable text found in the image.)")

        except pytesseract.TesseractNotFoundError:
            combined_content.append(
                "[Screenshot OCR Scanner Error]: Tesseract is not installed or not found in PATH. "
                "Install Tesseract OCR or set pytesseract.pytesseract.tesseract_cmd correctly."
            )
        except Exception as e:
            combined_content.append(f"[Screenshot OCR Scanner Error]: {str(e)}")

    if voice_msg is not None:
        if groq_client is None:
            combined_content.append("[Audio Transcription Error]: GROQ_API_KEY is not configured yet, so audio transcription is disabled.")
        else:
            try:
                with open(voice_msg, "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3"
                    )

                transcribed_text = getattr(transcription, "text", "").strip()

                if transcribed_text:
                    combined_content.append(f"[Transcribed Audio Message]:\n{transcribed_text}")
                else:
                    combined_content.append("[Transcribed Audio Message]:\n(No speech was detected in the audio.)")
            except Exception as e:
                combined_content.append(f"[Audio Transcription Error]: {str(e)}")

    if not combined_content:
        return "No input provided. Please enter text, upload a screenshot, or record a voice note."

    return "\n\n".join(combined_content)


# 5. Connecting Intermediary Execution Bridge
def run_ui_advisor(text_msg, screenshot, voice_msg):
    normalized_input = process_multimodal_inputs(text_msg, screenshot, voice_msg)

    if normalized_input.startswith("No input provided"):
        return normalized_input

    # Passes clean unified text directly to Person 1's functioning backend pipeline
    return run_rag_pipeline(normalized_input)


# 6. Styling Layout System Configuration
custom_css = """
body {
    background: 
        radial-gradient(circle at top left, rgba(59,130,246,0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(124,58,237,0.18), transparent 30%),
        linear-gradient(135deg, #0b1220, #111827, #1f2937) !important;
}
.gradio-container { max-width: 1120px !important; margin: 0 auto !important; padding-top: 36px !important; padding-bottom: 36px !important; }
.main-title { text-align: center !important; font-size: 2.4rem !important; font-weight: 800 !important; letter-spacing: 0.2px !important; margin-bottom: 8px !important; }
.sub-title { text-align: center !important; color: #cbd5e1 !important; font-size: 1.02rem !important; margin-bottom: 28px !important; }
.main-card { background: rgba(255, 255, 255, 0.07) !important; border: 1px solid rgba(255, 255, 255, 0.11) !important; border-radius: 26px !important; backdrop-filter: blur(18px) !important; -webkit-backdrop-filter: blur(18px) !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35) !important; padding: 26px !important; }
.left-panel, .right-panel { background: rgba(255, 255, 255, 0.045) !important; border: 1px solid rgba(255, 255, 255, 0.10) !important; border-radius: 20px !important; padding: 20px !important; min-height: 100% !important; }
.section-title { text-align: center !important; font-size: 1.15rem !important; font-weight: 700 !important; margin-bottom: 14px !important; }
.primary-btn button { background: linear-gradient(135deg, #2563eb, #7c3aed) !important; color: white !important; border: none !important; border-radius: 14px !important; font-weight: 700 !important; padding: 12px 18px !important; box-shadow: 0 10px 24px rgba(59, 130, 246, 0.35) !important; }
.primary-btn button:hover { filter: brightness(1.08) !important; transform: translateY(-1px) !important; transition: all 0.2s ease !important; }
.output-box { background: rgba(15, 23, 42, 0.58) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; padding: 18px !important; min-height: 420px !important; }
textarea, input { border-radius: 14px !important; }
@media (max-width: 768px) { .gradio-container { padding-left: 14px !important; padding-right: 14px !important; } .main-title { font-size: 1.9rem !important; } }
"""

with gr.Blocks(title="PhishShield AI", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("# 🛡️ PhishShield AI", elem_classes="main-title")
    gr.Markdown("Cyber-Attack & Scam Incident Advisor for suspicious messages, screenshots, and voice notes.", elem_classes="sub-title")

    with gr.Column(elem_classes="main-card"):
        with gr.Row():
            with gr.Column(scale=1, elem_classes="left-panel"):
                gr.Markdown("### Input Center", elem_classes="section-title")
                input_text = gr.Textbox(label="Option 1: Paste Suspicious Text", placeholder="Paste suspicious messages, emails, or alerts here...", lines=4)
                input_image = gr.Image(label="Option 2: Upload Screenshot Image", type="pil")
                input_audio = gr.Audio(label="Option 3: Upload / Record Voice Note", type="filepath")
                submit_btn = gr.Button("Analyze Security Legitimacy", elem_classes="primary-btn")

            with gr.Column(scale=1, elem_classes="right-panel"):
                gr.Markdown("### Advisor Evaluation", elem_classes="section-title")
                output_verdict = gr.Markdown(value="Your AI-generated security review will appear here.", elem_classes="output-box")

    submit_btn.click(
        fn=run_ui_advisor,
        inputs=[input_text, input_image, input_audio],
        outputs=output_verdict
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)

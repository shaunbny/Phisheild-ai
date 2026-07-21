import os
import gradio as gr
import requests
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from groq import Groq
import easyocr

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Backend Server Port Connection Address
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/analyze")

# Global OCR reader cache
ocr_reader = None
def get_ocr_reader():
    global ocr_reader
    if ocr_reader is None:
        ocr_reader = easyocr.Reader(['en'])
    return ocr_reader

def analyze_url(url):
    """Quick heuristic URL legitimacy check."""
    import re
    from urllib.parse import urlparse
    flags = []
    try:
        parsed = urlparse(url if url.startswith("http") else "http://" + url)
        domain = parsed.netloc.lower()

        # HTTPS check
        if not url.lower().startswith("https"):
            flags.append("Does NOT use HTTPS (insecure connection)")

        # Suspicious TLDs
        suspicious_tlds = [".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".club", ".work", ".click", ".loan", ".online"]
        if any(domain.endswith(t) for t in suspicious_tlds):
            flags.append(f"Uses a high-risk TLD: {domain.split('.')[-1]}")

        # IP address as domain
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain.split(':')[0]):
            flags.append("Uses an IP address instead of a domain name (common in phishing)")

        # Excessively long domain
        if len(domain) > 50:
            flags.append(f"Unusually long domain name ({len(domain)} chars)")

        # Multiple subdomains
        if domain.count('.') > 3:
            flags.append("Contains multiple subdomains (possible spoofing)")

        # Brand typosquatting check
        brands = ["paypal", "amazon", "netflix", "google", "microsoft", "apple", "facebook", "instagram", "bank", "sbi", "hdfc", "icici"]
        for brand in brands:
            if brand in domain and not domain.endswith(f"{brand}.com"):
                flags.append(f"Domain contains '{brand}' but may not be the official site")

        # Special chars or hyphens abuse
        if domain.count('-') > 3:
            flags.append("Excessive hyphens in domain (potential spoofing technique)")

        # URL shorteners
        shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "rebrand.ly", "is.gd"]
        if any(s in domain for s in shorteners):
            flags.append("Uses a URL shortener â€” actual destination is hidden")

        verdict = "HIGH RISK" if len(flags) >= 3 else "SUSPICIOUS" if flags else "APPEARS SAFE"
        summary = f"URL Legitimacy Check for: {url}\nVerdict: {verdict}\n"
        if flags:
            summary += "Red flags detected:\n" + "\n".join(f"  - {f}" for f in flags)
        else:
            summary += "No major red flags detected in URL structure."
        return summary
    except Exception as e:
        return f"URL Analysis Error: {str(e)}"


def process_multimodal_inputs(text_msg, url_msg, screenshot, voice_msg):
    combined_content = []

    if url_msg and url_msg.strip():
        combined_content.append(analyze_url(url_msg.strip()))
        combined_content.append(f"[URL to analyze]: {url_msg.strip()}")

    if text_msg and text_msg.strip():
        combined_content.append(f"[User Description]: {text_msg.strip()}")

    if screenshot is not None:
        try:
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(screenshot)
            
            img_np = np.array(screenshot)
            reader = get_ocr_reader()
            result = reader.readtext(img_np, detail=0)
            extracted_text = " ".join(result)

            if extracted_text and extracted_text.strip():
                combined_content.append(f"[Extracted from Screenshot]:\n{extracted_text.strip()}")
            else:
                combined_content.append("[Extracted from Screenshot]:\n(No readable text found in image.)")
        except Exception as e:
            combined_content.append(f"[Screenshot OCR Error]: {str(e)}")

    if voice_msg is not None:
        if groq_client is None:
            combined_content.append("[Audio Error]: GROQ_API_KEY is not configured.")
        else:
            try:
                with open(voice_msg, "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=audio_file, model="whisper-large-v3"
                    )
                transcribed_text = getattr(transcription, "text", "").strip()
                if transcribed_text:
                    combined_content.append(f"[Transcribed Audio]:\n{transcribed_text}")
            except Exception as e:
                combined_content.append(f"[Audio Error]: {str(e)}")

    if not combined_content:
        return "No input provided. Please enter a URL, text, upload a screenshot, or record a voice note."
    return "\n\n".join(combined_content)

def run_ui_advisor(text_msg, url_msg, screenshot, voice_msg):
    normalized_input = process_multimodal_inputs(text_msg, url_msg, screenshot, voice_msg)
    if normalized_input.startswith("No input provided"):
        return normalized_input

    # Secure Connection Bridge: Send normalized string to Backend API
    try:
        response = requests.post(BACKEND_URL, json={"text": normalized_input}, timeout=180)
        if response.status_code == 200:
            return response.json().get("analysis", "Error parsed from endpoint handler.")
        else:
            return f"Backend Communication Failure (Status {response.status_code}): {response.text}"
    except requests.exceptions.ConnectionError:
        return "CRITICAL ERROR: Could not connect to backend server. Make sure backend.py is running on port 8000!"
    except Exception as e:
        return f"Frontend Pipeline Interface Error: {str(e)}"

# Custom Styling Engine Configuration
custom_css = """
/* â•â•â•â•â•â•â• WARM DARK + CORAL/ORANGE THEME (MindMerge Style) â•â•â•â•â•â•â• */

/* Canvas & Reset */
body, .gradio-container, grad-app {
    background: #000000 !important;
    background-image: radial-gradient(circle at 50% 20%, rgba(0, 200, 83, 0.06) 0%, #000000 70%) !important;
    color: #b8f5c8 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Container limits */
.gradio-container {
    max-width: 1280px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 24px !important;
}

/* App container Row */
.app-container {
    display: flex !important;
    flex-direction: row !important;
    background: #000000 !important;
    border: 1px solid #0a3d1a !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 40px rgba(34, 197, 94, 0.05) !important;
    min-height: 850px !important;
}

/* â”€â”€â”€ Sidebar â”€â”€â”€ */
.sidebar {
    background: #050d08 !important;
    border-right: 1px solid #0a3d1a !important;
    padding: 24px !important;
    display: flex !important;
    flex-direction: column !important;
}

.sidebar-header {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    margin-bottom: 24px !important;
}

.sidebar-logo {
    font-size: 24px !important;
}

.sidebar-logo-wrap {
    width: 34px !important;
    height: 34px !important;
    background: #052e12 !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    border: 1px solid #0f5a26 !important;
}

.sidebar-title {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #22c55e !important;
    letter-spacing: -0.5px !important;
}

/* Feature card icon wrapper */
.feature-icon {
    width: 38px !important;
    height: 38px !important;
    background: #052e12 !important;
    border: 1px solid #0a3d1a !important;
    border-radius: 10px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-bottom: 12px !important;
}

/* Hero logo wrapper */
.hero-logo {
    width: 72px !important;
    height: 72px !important;
    background: #052e12 !important;
    border: 1.5px solid #0f5a26 !important;
    border-radius: 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto 16px auto !important;
    box-shadow: 0 0 24px rgba(34, 197, 94, 0.12) !important;
}

/* Search input in sidebar */
.sidebar-search textarea, .sidebar-search input {
    background: #000000 !important;
    border: 1px solid #0f5a26 !important;
    color: #a3e6b5 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    width: 100% !important;
}
.sidebar-search textarea::placeholder, .sidebar-search input::placeholder {
    color: #1a6e35 !important;
}
.sidebar-search textarea:focus, .sidebar-search input:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px #22c55e !important;
}

.sidebar-section-title {
    font-size: 11px !important;
    text-transform: uppercase !important;
    color: #166534 !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    margin-top: 24px !important;
    margin-bottom: 10px !important;
}

.sidebar-item {
    padding: 8px 12px !important;
    border-radius: 6px !important;
    color: #4ade80 !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    margin-bottom: 4px !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.sidebar-item:hover {
    background: #052e12 !important;
    color: #86efac !important;
}

.sidebar-item.active {
    background: #052e12 !important;
    color: #22c55e !important;
    font-weight: 600 !important;
    border-left: 3px solid #22c55e !important;
}

/* New Scan green button */
.new-scan-btn button, button.new-scan-btn {
    background: #22c55e !important;
    border: none !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    margin-top: auto !important;
    display: block !important;
    width: 100% !important;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.25) !important;
}

.new-scan-btn button:hover {
    background: #4ade80 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(34, 197, 94, 0.35) !important;
}

/* ─── Main Panel (full page, no sidebar) ─── */
.main-panel {
    background: #000000 !important;
    padding: 32px 48px !important;
    display: flex !important;
    flex-direction: column !important;
    max-width: 960px !important;
    margin: 0 auto !important;
    width: 100% !important;
    min-height: 100vh !important;
}

.main-header {
    text-align: center !important;
    padding: 28px 0 4px 0 !important;
    margin-bottom: 4px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.main-header-title {
    font-size: 22px !important;
    font-weight: 800 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #22c55e !important;
    font-family: 'Inter', sans-serif !important;
}

/* Strip Gradio container box from the header HTML block */
.main-panel > .gradio-column > div:first-child,
.main-panel > div:first-child .block,
.main-panel .block:has(.main-header) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.chat-title {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #d1fae5 !important;
}

.version-badge {
    background: rgba(34, 197, 94, 0.1) !important;
    color: #22c55e !important;
    border: 1px solid #0f5a26 !important;
    border-radius: 4px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 2px 8px !important;
}

/* â”€â”€â”€ Hero â”€â”€â”€ */
.helper-hero {
    text-align: center !important;
    margin-bottom: 32px !important;
}

.hero-logo {
    font-size: 48px !important;
    color: #22c55e !important;
    margin-bottom: 12px !important;
}

.hero-title {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: -0.5px !important;
    margin-bottom: 8px !important;
}

.hero-desc {
    font-size: 15px !important;
    color: #34d399 !important;
    max-width: 600px !important;
    margin: 0 auto !important;
}

/* ─── Feature Cards ─── */
.feature-cards-row {
    display: flex !important;
    gap: 16px !important;
    margin-bottom: 32px !important;
    align-items: stretch !important;
}

/* Propagate height through Gradio wrappers */
.feature-cards-row > .block,
.feature-cards-row > div {
    display: flex !important;
    flex-direction: column !important;
}

.feature-cards-row .html-container,
.feature-cards-row .prose {
    display: flex !important;
    flex-direction: column !important;
    flex-grow: 1 !important;
}

.feature-card {
    flex: 1 !important;
    background: #030a05 !important;
    border: 1px solid #0a3d1a !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex-grow: 1 !important;
    box-sizing: border-box !important;
}

.feature-card:hover {
    border-color: #22c55e !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.1) !important;
}

.feature-icon {
    font-size: 20px !important;
    margin-bottom: 10px !important;
}

.feature-card h3 {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #4ade80 !important;
    margin: 0 0 6px 0 !important;
}

.feature-card p {
    font-size: 12px !important;
    color: #166534 !important;
    margin: 0 !important;
    line-height: 1.4 !important;
}

/* â”€â”€â”€ Inputs Card â”€â”€â”€ */
.inputs-card {
    background: #030a05 !important;
    border: 1px solid #0a3d1a !important;
    border-radius: 16px !important;
    padding: 24px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4) !important;
}

/* Form inputs */
textarea, input, .uploader, .file-preview, .audio-container, .block, .w-full {
    background-color: #000000 !important;
    background: #000000 !important;
    color: #a3e6b5 !important;
    border: 1px solid #0a3d1a !important;
}

.input-field textarea, .input-field input, .input-field-image, .input-field-audio, .input-field-image .block, .input-field-audio .block {
    background-color: #000000 !important;
    border: 1px solid #0a3d1a !important;
    color: #a3e6b5 !important;
    border-radius: 8px !important;
}

.input-field textarea:focus, .input-field input:focus,
textarea:focus, input:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px #22c55e !important;
    outline: none !important;
}

textarea::placeholder, input::placeholder {
    color: #0f5a26 !important;
}

/* Label badges */
div[class*="block-label"], .block label span, .form label span, .gradio-container label span {
    background-color: #052e12 !important;
    background: #052e12 !important;
    color: #34d399 !important;
    border: 1px solid #0a3d1a !important;
    border-radius: 4px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* Primary Action Button */
.primary-btn button, button.primary-btn {
    background: #22c55e !important;
    border: none !important;
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    padding: 14px 28px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.25) !important;
    width: 100% !important;
}

.primary-btn button:hover {
    background: #4ade80 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(34, 197, 94, 0.35) !important;
}

/* â”€â”€â”€ URL Scanner Field â”€â”€â”€ */
.url-input-row {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    background: #0a1a10 !important;
    border: 1px solid #14432a !important;
    border-radius: 12px !important;
    padding: 8px 12px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

.url-icon {
    font-size: 18px !important;
    flex-shrink: 0 !important;
}

.url-field textarea, .url-field input {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #d7f5e2 !important;
    font-size: 14px !important;
    font-family: 'Inter', monospace !important;
}

.url-field textarea::placeholder, .url-field input::placeholder {
    color: #3d6b4d !important;
    font-style: italic !important;
}

.url-check-btn button, button.url-check-btn {
    background: #22c55e !important;
    border: none !important;
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 3px 10px rgba(34, 197, 94, 0.2) !important;
    flex-shrink: 0 !important;
}

.url-check-btn button:hover {
    background: #4ade80 !important;
    transform: translateY(-1px) !important;
}

.url-result-box {
    background: #11281a !important;
    border: 1px solid #1c5234 !important;
    border-radius: 8px !important;
    padding: 10px 15px !important;
    margin-bottom: 16px !important;
    color: #d7f5e2 !important;
    font-size: 14px !important;
}

/* â”€â”€â”€ Custom File Upload & Output â”€â”€â”€ */

/* Output Verdict */
.output-box {
    background: #020805 !important;
    border: 1px solid #0a3d1a !important;
    border-left: 4px solid #22c55e !important;
    border-radius: 8px !important;
    padding: 20px !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    min-height: 120px !important;
    margin-top: 16px !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.6) !important;
}

.output-box, 
.output-box .prose p, 
.output-box .prose li, 
.output-box .prose span,
.output-box p,
.output-box li,
.output-box strong {
    color: #e2e8f0 !important;
}

.output-box h1, .output-box h2, .output-box h3,
.output-box .prose h1, .output-box .prose h2, .output-box .prose h3 {
    color: #4ade80 !important;
    margin-top: 12px !important;
    margin-bottom: 8px !important;
}

/* Footer */
.footer-note {
    text-align: center !important;
    font-size: 11px !important;
    color: #166534 !important;
    margin-top: 20px !important;
    padding-top: 24px !important;
}

/* â”€â”€â”€ Gradio Blue â†’ Green Component Overrides â”€â”€â”€ */

/* Override Gradio theme CSS variables at root level */
:root {
    --block-border-color: #0a3d1a !important;
    --border-color-primary: #0a3d1a !important;
    --panel-border-color: #0a3d1a !important;
    --input-border-color: #0a3d1a !important;
    --block-label-background-fill: #052e12 !important;
    --block-label-text-color: #22c55e !important;
    --block-label-border-color: #0a3d1a !important;
    --color-accent: #22c55e !important;
    --color-accent-soft: #052e12 !important;
    --primary-50:  #052e12 !important;
    --primary-100: #052e12 !important;
    --primary-200: #0a3d1a !important;
    --primary-300: #14532d !important;
    --primary-400: #16a34a !important;
    --primary-500: #22c55e !important;
    --primary-600: #16a34a !important;
    --primary-700: #15803d !important;
    --primary-800: #166534 !important;
    --primary-900: #14532d !important;
    --color-blue-50:  #052e12 !important;
    --color-blue-100: #052e12 !important;
    --color-blue-200: #0a3d1a !important;
    --color-blue-300: #14532d !important;
    --color-blue-400: #16a34a !important;
    --color-blue-500: #22c55e !important;
    --color-blue-600: #16a34a !important;
    --color-blue-700: #15803d !important;
}

/* Target the exact Svelte-scoped label selector Gradio uses */
label.svelte-19djge9,
label[data-testid="block-label"],
[data-testid="block-label"] {
    background: #052e12 !important;
    background-color: #052e12 !important;
    color: #22c55e !important;
    border-color: #0a3d1a !important;
}

/* Upload drop zone text */
.upload-container p, .upload-container span,
[data-testid="image"] p, [data-testid="image"] span,
[data-testid="audio"] p, [data-testid="audio"] span,
.wrap > p, .wrap > span,
.empty.small > p { color: #22c55e !important; }

/* Upload and audio SVG icons */
.upload-container svg path, .upload-container svg polyline,
[data-testid="image"] svg path, [data-testid="image"] svg rect,
[data-testid="audio"] svg path, [data-testid="audio"] svg circle,
.icon-wrap svg, .icon-wrap svg path,
.toolbar svg, .toolbar svg path,
button[aria-label] svg, button[aria-label] svg path {
    stroke: #22c55e !important;
    fill: none !important;
}

/* Drop zone borders */
.upload-container, [data-testid="image"] .wrap, [data-testid="audio"] .wrap,
.uploader, .wrap.svelte-1n4qh1h { border-color: #0a3d1a !important; }

/* "Click to Upload" link text */
a, .link, [class*="link"] { color: #22c55e !important; }

/* â”€â”€â”€ EXACT FIX: Gradio Soft Theme Blue Label Override â”€â”€â”€ */
/* The Soft theme sets --block-label-background-fill: #e0e7ff (blue-indigo) */
/* We override both the variable AND the direct property with max specificity */
gradio-app, :root {
    --block-label-background-fill: #052e12 !important;
    --block-label-text-color: #22c55e !important;
    --block-label-border-color: #0a3d1a !important;
    --block-label-margin: 0 !important;
}

label.svelte-19djge9,
label.svelte-19djge9.float,
gradio-app label[data-testid="block-label"],
.gradio-container label[data-testid="block-label"],
gradio-app label.svelte-19djge9 {
    background: #052e12 !important;
    background-color: #052e12 !important;
    color: #22c55e !important;
    border-color: #0a3d1a !important;
    border: 1px solid #0a3d1a !important;
}

/* The icon SVG inside the label badge */
label.svelte-19djge9 svg,
label.svelte-19djge9 svg path,
label.svelte-19djge9 svg rect,
label.svelte-19djge9 svg circle,
label.svelte-19djge9 svg polyline {
    stroke: #22c55e !important;
}

/* ─── Hide Gradio Built-in Footer Bar ─── */
footer,
.gradio-container footer,
.gradio-container > .wrap > footer,
footer.svelte-zxu34v,
.show-api,
.built-with {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}

/* ─── Global Overrides ─── */
* { scrollbar-color: #0a3d1a #000000 !important; }
::-webkit-scrollbar { width: 8px !important; }
::-webkit-scrollbar-track { background: #000000 !important; }
::-webkit-scrollbar-thumb { background: #0a3d1a !important; border-radius: 4px !important; }
::-webkit-scrollbar-thumb:hover { background: #22c55e !important; }
"""

with gr.Blocks(title="PhiShield AI", theme=gr.themes.Base(), css=custom_css) as demo:
    with gr.Column(elem_classes="main-panel"):
        gr.HTML("""
            <div class="main-header">
                <span class="main-header-title">PhiShield AI</span>
            </div>
        """)


        with gr.Column(elem_classes="center-container"):
            gr.HTML("""
                <div class="helper-hero">
                    <div class="hero-logo">
                        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 2L3 6.5V12c0 5 3.6 9.7 9 11 5.4-1.3 9-6 9-11V6.5L12 2z" fill="#22c55e"/>
                          <path d="M9 12l2 2 4-4" stroke="#000" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <h1 class="hero-title">How can I protect you today?</h1>
                    <p class="hero-desc">Analyze emails, text messages, screenshot attachments, or voice notes to identify security threats.</p>
                </div>
            """)

            with gr.Row(elem_classes="feature-cards-row"):
                gr.HTML("""
                    <div class="feature-card">
                        <div class="feature-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                              <polyline points="14 2 14 8 20 8"/>
                              <line x1="16" y1="13" x2="8" y2="13"/>
                              <line x1="16" y1="17" x2="8" y2="17"/>
                            </svg>
                        </div>
                        <h3>Text Inspection</h3>
                        <p>Analyze links, generic greetings, and high-pressure text templates.</p>
                    </div>
                """)
                gr.HTML("""
                    <div class="feature-card">
                        <div class="feature-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                              <rect x="3" y="3" width="18" height="18" rx="2"/>
                              <circle cx="8.5" cy="8.5" r="1.5"/>
                              <polyline points="21 15 16 10 5 21"/>
                            </svg>
                        </div>
                        <h3>OCR Screenshot Scanner</h3>
                        <p>Upload screenshots to scan for malicious terms and brand warnings.</p>
                    </div>
                """)
                gr.HTML("""
                    <div class="feature-card">
                        <div class="feature-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                              <line x1="12" y1="19" x2="12" y2="23"/>
                              <line x1="8" y1="23" x2="16" y2="23"/>
                            </svg>
                        </div>
                        <h3>Audio Fraud Detection</h3>
                        <p>Transcribe and verify unsolicited audio or deepfake voice notes.</p>
                    </div>
                """)
                gr.HTML("""
                    <div class="feature-card">
                        <div class="feature-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                            </svg>
                        </div>
                        <h3>Link Verification</h3>
                        <p>Detect phishing URLs, spoofed domains, suspicious TLDs, and URL shortener traps.</p>
                    </div>
                """)

            with gr.Column(elem_classes="inputs-card"):
                with gr.Row(elem_classes="url-input-row"):
                    gr.HTML("""
                        <span class="url-icon">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                            </svg>
                        </span>
                    """)
                    input_url = gr.Textbox(
                        show_label=False,
                        placeholder="Paste a suspicious URL to check legitimacy (e.g. http://paypa1-login.xyz/verify)",
                        lines=1,
                        container=False,
                        elem_classes="url-field",
                        scale=8
                    )
                    url_check_btn = gr.Button("Check URL", elem_classes="url-check-btn", scale=0)
                
                url_result_box = gr.Markdown(visible=False, elem_classes="url-result-box")

                input_text = gr.Textbox(
                    label="Suspicious Text Content",
                    placeholder="Paste suspicious SMS, email body, or warning message text here...",
                    lines=3,
                    elem_classes="input-field"
                )

                with gr.Row():
                    input_image = gr.Image(
                        label="Upload Screenshot Image",
                        type="pil",
                        elem_classes="input-field-image"
                    )
                    input_audio = gr.Audio(
                        label="Record or Upload Voice Note",
                        type="filepath",
                        elem_classes="input-field-audio"
                    )

                with gr.Row():
                    new_scan_btn = gr.Button("Clear / New Scan", elem_classes="new-scan-btn", scale=1)
                    submit_btn = gr.Button("Analyze Security Legitimacy", elem_classes="primary-btn", scale=3)

            output_verdict = gr.Markdown(
                value="Your AI-generated security advisory will appear here.",
                elem_classes="output-box"
            )

        gr.HTML("""
            <div class="footer-note">
                PhishShield AI can make mistakes. Verify critical financial or legal alerts directly with official institution channels.
            </div>
        """)

    # Function mappings
    scroll_to_output_js = """
    function(...args) {
        setTimeout(function() {
            var output = document.querySelector('.output-box');
            if (output) {
                output.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        }, 100);
        return args;
    }
    """

    submit_btn.click(fn=run_ui_advisor, inputs=[input_text, input_url, input_image, input_audio], outputs=output_verdict, js=scroll_to_output_js)
    url_check_btn.click(fn=run_ui_advisor, inputs=[input_text, input_url, input_image, input_audio], outputs=output_verdict, js=scroll_to_output_js)
    input_url.submit(fn=run_ui_advisor, inputs=[input_text, input_url, input_image, input_audio], outputs=output_verdict, js=scroll_to_output_js)

    def clear_inputs():
        return "", "", None, None, "Your AI-generated security advisory will appear here.", gr.update(visible=False)

    new_scan_btn.click(fn=clear_inputs, inputs=[], outputs=[input_text, input_url, input_image, input_audio, output_verdict, url_result_box])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)


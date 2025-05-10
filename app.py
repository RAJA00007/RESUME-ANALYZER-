import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
import pdfplumber

# Load environment variables
load_dotenv()
GOOGLE_api = os.getenv("GOOGLE_api")
if not GOOGLE_api:
    st.error("GOOGLE_api not found in environment variables.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GOOGLE_api)

# PDF text extraction
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        if text.strip():
            return text.strip()
    except Exception as e:
        print("Text extraction failed:", e)

    # Fallback to OCR
    try:
        images = convert_from_path(file_path)
        for img in images:
            text += pytesseract.image_to_string(img)
    except Exception as e:
        print("OCR failed:", e)

    return text.strip()

# AI analysis
def analyze_resume(text, job_description=None):
    if not text:
        return "❌ Resume content is empty."

    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an HR expert. Analyze the following resume and provide:
    - Suitability for roles in AI/ML, Data Science, or Software Engineering.
    - Skills already present and missing.
    - Courses or improvements to make the resume better.
    Resume:
    {text}
    """
    if job_description:
        prompt += f"\nAlso match it against the following job description:\n{job_description}"

    response = model.generate_content(prompt)
    return response.text.strip()

# Streamlit UI
st.set_page_config(page_title="Resume Analyzer", layout="wide")
st.title("📄 AI Resume Analyzer")
st.write("Upload your resume and optionally a job description. Get feedback from Gemini AI.")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
with col2:
    job_desc = st.text_area("Paste Job Description (optional)")

if uploaded_file:
    st.success("✅ Resume uploaded!")
    with open("temp_resume.pdf", "wb") as f:
        f.write(uploaded_file.read())

    if st.button("Analyze Resume"):
        with st.spinner("🔍 Analyzing..."):
            resume_text = extract_text_from_pdf("temp_resume.pdf")
            if not resume_text:
                st.error("❌ Could not extract text from resume.")
            else:
                try:
                    result = analyze_resume(resume_text, job_desc)
                    st.markdown("### 🧠 Gemini AI Analysis")
                    st.write(result)
                except Exception as e:
                    st.error(f"❌ Gemini API failed: {e}")
else:
    st.warning("👆 Please upload a resume to begin.")

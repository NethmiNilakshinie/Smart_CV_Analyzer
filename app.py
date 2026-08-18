import streamlit as st
import google.generativeai as genai
import PyPDF2
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
import re

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

generation_config = {
    "temperature": 0.7,
}

model = genai.GenerativeModel(
    "gemini-3.6-flash", generation_config=generation_config
)

# Page Config
st.set_page_config(page_title="ResumeForge AI", layout="wide")

def load_lottie_url(url):
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None

lottie_rocket = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_pqaxtuxc.json")

def get_pdf_text(pdf):
    reader = PyPDF2.PdfReader(pdf)
    return " ".join([p.extract_text() for p in reader.pages])

# Session State Initialization
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {
        "General": [], "ATS": [], "Summary": [], "Keywords": [], "Interview": []
    }
if "current_feature" not in st.session_state:
    st.session_state.current_feature = "General"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 28px; margin-top: -50px;'>🤖 ResumeForge AI</h1>", unsafe_allow_html=True)
    st.header("Upload Center")
    uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    st.divider()

    st.markdown("""
        <style>
        div[role="radiogroup"] { display: flex; flex-direction: column; gap: 10px; }
        div[role="radiogroup"] > label { background-color: #262730; padding: 10px; border-radius: 8px; border: 1px solid #555; transition: 0.3s; cursor: pointer; }
        div[role="radiogroup"] > label:has(input:checked) { border: 2px solid #3498db !important; background-color: #1e3a5a !important; }
        </style>
    """, unsafe_allow_html=True)

    feature = st.radio("Select Feature:", ["ATS Score", "Professional Summary", "ATS Keyword Check", "Mock Interview"], label_visibility="collapsed")
    mapping = {"ATS Score": "ATS", "Professional Summary": "Summary", "ATS Keyword Check": "Keywords", "Mock Interview": "Interview"}
    st.session_state.current_feature = mapping[feature]
    st.divider()
    st.write(f"**Mode:** {st.session_state.current_feature}")

st.markdown("""<style>div[data-testid="stSuccess"] { background-color: #2e7d32 !important; color: white !important; }</style>""", unsafe_allow_html=True)

if uploaded_file:
    cv_text = get_pdf_text(uploaded_file)
    if lottie_rocket: st_lottie(lottie_rocket, height=150)
    st.success(f"CV Processed! Active Mode: {st.session_state.current_feature}")

    if st.button(f"Generate {st.session_state.current_feature} Result"):
        prompt_map = {
        "ATS": (
            "You are an extremely strict and critical ATS resume expert. "
            "Analyze the CV thoroughly. DO NOT give a generic or default score like 58. "
            "You MUST evaluate harshly based strictly on formatting, section completeness, "
            "and keyword optimization. Give a wide and varied score from 10 to 95 "
            "(if the CV has major flaws, give a low score like 25-45; if it's exceptionally good, "
            "give 85-95). You MUST start your response with 'Score: [number]' where [number] "
            "is a unique calculated score for this specific CV, followed by your detailed feedback:"
        ),
        "Summary": "Write a professional summary for this CV:",
        "Keywords": "List the missing ATS keywords for this CV:",
        "Interview": "Generate mock interview questions based on this CV:",
    }
        res = model.generate_content(f"{prompt_map[st.session_state.current_feature]} {cv_text[:5000]}")
        st.session_state.last_result = {"type": st.session_state.current_feature, "content": res.text}

    if st.session_state.last_result:
        res = st.session_state.last_result
        if res["type"] == "ATS":
            content = res["content"]
            
            # Smart Regex to extract 'Score: XX' accurately
            score_match = re.search(r'Score:\s*(\d+)', content, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
            else:
                numbers = re.findall(r'\d+', content)
                score = int(numbers[0]) if numbers else 70

            if score > 100: score = 100
            if score < 0: score = 0

            fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text': "ATS Score"}))
            st.plotly_chart(fig)
            st.write("### ATS Feedback & Analysis:")
            st.info(content)
        else:
            st.info(res["content"])
    
    st.divider()
    
    # Chat History Display
    current_chat = st.session_state.chat_histories[st.session_state.current_feature]
    for msg in current_chat:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
    # Input Area 
    prompt = st.chat_input(f"Ask about {st.session_state.current_feature}...")
    
    if prompt:
        current_chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            res = model.generate_content(f"Context: {st.session_state.current_feature}\nCV: {cv_text[:5000]}\n\nQ: {prompt}")
            st.markdown(res.text)
            current_chat.append({"role": "assistant", "content": res.text})
            st.rerun()

else:
    st.markdown("""<style>@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-15px); } 100% { transform: translateY(0px); } } .animated-text { text-align: center; font-size: 24px; font-weight: bold; color: #3498db; animation: float 3s ease-in-out infinite; margin-top: 100px; } </style><div class="animated-text">Please Upload Your CV to Start the Journey!</div>""", unsafe_allow_html=True)
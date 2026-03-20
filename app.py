import os
import tempfile
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Student Help Desk AI", page_icon="🎓")

# 🎨 COLORS
PRIMARY_PURPLE = "#7B5CFF"
PINK = "#E85BBE"
ORANGE = "#FF8A5B"
BG = "#F3F4F6"
TEXT = "#1F2937"
WHITE = "#FFFFFF"
MUTED = "#6B7280"
LIGHT_PURPLE = "#EDE9FE"
LIGHT_CARD = "#FFFFFF"

# -----------------------------
# SIMPLE STYLING
# -----------------------------
st.markdown(f"""
<style>
.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

h1, h2 {{
    font-weight: 700;
}}

section[data-testid="stSidebar"] {{
    background-color: {LIGHT_CARD};
    border-right: 1px solid {LIGHT_PURPLE};
}}

[data-testid="stChatMessage"] {{
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 12px;
}}

[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {{
    background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK});
    color: white;
}}

[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {{
    background: {WHITE};
    border: 1px solid {LIGHT_PURPLE};
}}

.stChatInput {{
    border-radius: 12px !important;
    border: 1px solid {LIGHT_PURPLE} !important;
}}

button {{
    background-color: {PRIMARY_PURPLE} !important;
    color: white !important;
    border-radius: 8px !important;
}}

button:hover {{
    background-color: {PINK} !important;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# GEMINI CONFIG
# -----------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-2.5-flash"

client = None
api_ready = False

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    api_ready = True

# -----------------------------
# FAQ
# -----------------------------
FAQ_KB = {
    "exam": "You can ask about exam dates, timetable, and results.",
    "course": "Ask about subjects, modules, and schedules.",
    "assignment": "Ask about deadlines and submissions.",
    "fees": "Ask about tuition fees and payments."
}

def detect_topic(msg):
    msg = msg.lower()
    for key in FAQ_KB:
        if key in msg:
            return FAQ_KB[key]
    return ""

# -----------------------------
# RESPONSE
# -----------------------------
def generate_response(user_message):
    if not api_ready:
        return "⚠️ API key not set."

    context = detect_topic(user_message)

    prompt = f"""
Context:
{context}

User:
{user_message}

Answer clearly as a student help desk assistant.
"""

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7),
        )
        return response.text
    except:
        return "❌ Error generating response"

# -----------------------------
# PDF
# -----------------------------
def upload_pdf(file):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file.getbuffer())
            return client.files.upload(file=tmp.name)
    except:
        return None

# -----------------------------
# SESSION
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf" not in st.session_state:
    st.session_state.pdf = None

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK});
        padding: 16px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    ">
        <b>🎓 Help Desk AI</b><br>
        <small>Student support chatbot</small>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

    if uploaded_file:
        st.session_state.pdf = upload_pdf(uploaded_file)
        st.success("PDF uploaded")

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# HEADER
# -----------------------------
st.markdown(f"""
<div style="
    background: linear-gradient(90deg, {PRIMARY_PURPLE}, {PINK});
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 20px;
">
    <h2 style="color:white; margin:0;">
        🎓 Student Help Desk AI
    </h2>
    <p style="color:rgba(255,255,255,0.9); font-size:14px;">
        Smart chatbot for student support
    </p>
</div>
""", unsafe_allow_html=True)

if not api_ready:
    st.warning("Set GEMINI_API_KEY in secrets.toml")

# -----------------------------
# CHAT DISPLAY
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# INPUT
# -----------------------------
prompt = st.chat_input("Ask your question...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
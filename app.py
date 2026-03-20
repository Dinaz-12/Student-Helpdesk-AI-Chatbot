import tempfile
import streamlit as st
from google import genai
from google.genai import types

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Student Help Desk AI", page_icon="🎓")

# 🎨 THEME
PRIMARY_PURPLE = "#7B5CFF"
PINK = "#E85BBE"
BG = "#F3F4F6"
TEXT = "#1F2937"
WHITE = "#FFFFFF"
LIGHT_PURPLE = "#EDE9FE"

# -----------------------------
# STYLE
# -----------------------------
st.markdown(f"""
<style>

.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

/* Chat spacing */
[data-testid="stChatMessage"] {{
    margin-bottom: 16px;
}}

/* USER bubble */
[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {{
    background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK});
    color: white;
    padding: 12px;
    border-radius: 14px;
    margin-left: 20%;
}}

/* BOT bubble */
[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {{
    background: {WHITE};
    border: 1px solid {LIGHT_PURPLE};
    padding: 12px;
    border-radius: 14px;
    margin-right: 20%;
}}

/* Avatar colors */
[data-testid="chatAvatarIcon-user"] {{
    background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK}) !important;
    color: white !important;
}}

[data-testid="chatAvatarIcon-assistant"] {{
    background: {LIGHT_PURPLE} !important;
    color: {PRIMARY_PURPLE} !important;
}}

/* Input */
.stChatInput {{
    border-radius: 12px !important;
    border: 1px solid {LIGHT_PURPLE} !important;
}}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# GEMINI
# -----------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-2.5-flash"

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# -----------------------------
# RESPONSE FUNCTION
# -----------------------------
def generate_response(user_message):
    if not client:
        return "⚠️ API key not set."

    prompt = f"""
You are a helpful student support assistant.

User: {user_message}

Give a clear, friendly, structured answer.
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
# SESSION
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

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
        <small>Student chatbot</small>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

    if uploaded_file:
        st.success("PDF uploaded (basic demo)")

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

    # Typing animation
    with st.chat_message("assistant"):

        st.markdown(f"""
        <div style="display:flex; gap:5px; padding:10px;">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>

        <style>
        .dot {{
            width:8px;
            height:8px;
            background:{PRIMARY_PURPLE};
            border-radius:50%;
            animation: blink 1.4s infinite;
        }}

        .dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .dot:nth-child(3) {{ animation-delay: 0.4s; }}

        @keyframes blink {{
            0% {{ opacity:0.2; }}
            20% {{ opacity:1; }}
            100% {{ opacity:0.2; }}
        }}
        </style>
        """, unsafe_allow_html=True)

        response = generate_response(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
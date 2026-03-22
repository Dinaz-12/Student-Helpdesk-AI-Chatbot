import tempfile
import streamlit as st
import google.generativeai as genai
import PyPDF2

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Student Help Desk AI", page_icon="🎓")

# 🎨 BRAND COLORS
PRIMARY_PURPLE = "#7B5CFF"
PINK = "#E85BBE"
LIGHT_PURPLE = "#EDE9FE"

# -----------------------------
# STYLE (theme-aware)
# -----------------------------
st.markdown(f"""
<style>

.stApp {{
    background-color: var(--background-color);
    color: var(--text-color);
}}

[data-testid="stChatMessage"] {{
    margin-bottom: 14px;
}}

[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {{
    background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK});
    color: white;
    padding: 12px;
    border-radius: 14px;
    margin-left: 20%;
}}

[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {{
    background: var(--secondary-background-color);
    border: 1px solid rgba(120,120,120,0.2);
    color: var(--text-color);
    padding: 12px;
    border-radius: 14px;
    margin-right: 20%;
}}

[data-testid="stChatInput"] > div {{
    background-color: var(--secondary-background-color) !important;
    border: 1px solid rgba(120,120,120,0.2) !important;
    border-radius: 14px !important;
}}

[data-testid="stChatInput"] > div:focus-within {{
    border: 1px solid {PRIMARY_PURPLE} !important;
    box-shadow: 0 0 0 1px {PRIMARY_PURPLE} !important;
}}

button[kind="secondary"] {{
    background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK}) !important;
    color: white !important;
    border-radius: 10px !important;
}}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# GEMINI
# -----------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-1.5-flash"

client = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# -----------------------------
def extract_pdf_text(uploaded_file):
    text = ""
    reader = PyPDF2.PdfReader(uploaded_file)

    for page in reader.pages:
        text += page.extract_text() or ""

    return text

# -----------------------------
# PDF UPLOAD FUNCTION
# -----------------------------
def upload_pdf_to_gemini(uploaded_file):
    if uploaded_file is None:
        return None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        gemini_file = client.files.upload(file=temp_path)
        return gemini_file

    except Exception as e:
        return None

# -----------------------------
# RESPONSE FUNCTION
# -----------------------------
def generate_response(user_message):
    if not client:
        return "⚠️ API key not set."

    prompt = f"""
You are a helpful student assistant.

User: {user_message}
"""

    try:
        # 🔥 First try (fast & free)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        try:
            # 🔁 Fallback model
            response = client.models.generate_content(
                model="gemini-1.5-pro",
                contents=prompt
            )
            return response.text
        except:
            if "429" in str(e):
                return "⚠️ Too many requests. Please wait and try again."
            return "❌ Error generating response"

# -----------------------------
# SESSION
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None

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

    st.info(f"💬 Chats: {len(st.session_state.messages)}")



    # -----------------------------
    # 📄 PDF STATUS
    # -----------------------------
    if st.session_state.pdf_file:
        st.success("📄 Gemini PDF loaded")

    if st.session_state.pdf_text:
        st.success("📄 Text PDF loaded")

    # -----------------------------
    # 📄 UPLOAD
    # -----------------------------
    uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

    if uploaded_file:
        if st.button("Use PDF", use_container_width=True):
            with st.spinner("Uploading PDF..."):
                gemini_file = upload_pdf_to_gemini(uploaded_file)

                if gemini_file:
                    st.session_state.pdf_file = gemini_file
                    st.success("PDF ready ✅")

    # Clear Chat
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pdf_file = None
        st.session_state.pdf_text = ""
        st.rerun()
        

        # 🔥 SIMPLE TEXT EXTRACT (NEW)
        pdf_text = extract_pdf_text(uploaded_file)
        st.session_state.pdf_text = pdf_text
        st.success("PDF text extracted ✅")




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
        Smart chatbot with PDF support
    </p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# EMPTY STATE (ADD HERE 🔥)
# -----------------------------
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div style="text-align:center; margin-top:40px; opacity:0.7;">
        <h4>Try asking:</h4>
        <p>• Exam timetable</p>
        <p>• Assignment deadlines</p>
        <p>• Course details</p>
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

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
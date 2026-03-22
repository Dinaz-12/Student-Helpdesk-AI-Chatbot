import streamlit as st
import google.generativeai as genai
import PyPDF2

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Student Help Desk AI", page_icon="🎓")

PRIMARY_PURPLE = "#7B5CFF"
PINK = "#E85BBE"

# -----------------------------
# STYLE
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
    padding: 12px;
    border-radius: 14px;
    margin-right: 20%;
}}

[data-testid="stChatInput"] > div {{
    border-radius: 14px !important;
}}

button[kind="secondary"] {{
    background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK}) !important;
    color: white !important;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# GEMINI SETUP (FIXED ✅)
# -----------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# -----------------------------
# PDF TEXT EXTRACT
# -----------------------------
def extract_pdf_text(uploaded_file):
    text = ""
    reader = PyPDF2.PdfReader(uploaded_file)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# -----------------------------
# RESPONSE FUNCTION (FIXED MODEL ✅)
# -----------------------------
def generate_response(user_message):
    if not GEMINI_API_KEY:
        return "⚠️ API key not set."

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")  # ✅ WORKING MODEL

        response = model.generate_content(
            f"You are a helpful student assistant.\nUser: {user_message}"
        )

        return response.text

    except Exception as e:
        return f"❌ Error: {str(e)}"

# -----------------------------
# SESSION
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:

    st.markdown("### 🎓 Help Desk AI")

    uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

    if uploaded_file:
        st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("PDF loaded ✅")

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.session_state.pdf_text = ""
        st.rerun()

# -----------------------------
# HEADER
# -----------------------------
st.markdown(f"""
<div style="background: linear-gradient(90deg, {PRIMARY_PURPLE}, {PINK});
padding: 18px; border-radius: 12px; margin-bottom: 20px;">
<h2 style="color:white;">🎓 Student Help Desk AI</h2>
<p style="color:white;">Smart chatbot with PDF support</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# EMPTY STATE
# -----------------------------
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div style="text-align:center; opacity:0.7;">
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

    # Include PDF context if exists
    full_prompt = prompt
    if st.session_state.pdf_text:
        full_prompt = f"{prompt}\n\nPDF Content:\n{st.session_state.pdf_text[:2000]}"

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(full_prompt)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
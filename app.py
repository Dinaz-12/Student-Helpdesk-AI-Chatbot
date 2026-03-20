import os
import time
import tempfile
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Student Help Desk AI",
    page_icon="🎓",
    layout="wide",
)

# -------------------------------------------------
# GEMINI CONFIG
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Recommended current fast model for general chat use
DEFAULT_MODEL = "gemini-2.5-flash"

client = None
api_ready = False
api_error_message = ""

try:
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        api_ready = True
    else:
        api_error_message = "GEMINI_API_KEY not found. Please set your environment variable."
except Exception as e:
    api_error_message = f"Gemini client error: {str(e)}"

# -------------------------------------------------
# COLOR PALETTE
# -------------------------------------------------
PRIMARY_PURPLE = "#7B5CFF"
PINK = "#E85BBE"
ORANGE = "#FF8A5B"
BG = "#F3F4F6"
TEXT = "#1F2937"
WHITE = "#FFFFFF"
MUTED = "#6B7280"
LIGHT_PURPLE = "#EDE9FE"
LIGHT_CARD = "#FFFFFF"

# -------------------------------------------------
# FAQ KNOWLEDGE BASE
# -------------------------------------------------
FAQ_KB = {
    "exam": {
        "title": "Exam Information",
        "content": (
            "Students can ask about exam dates, exam timetable, hall allocation, exam instructions, "
            "and result guidance. When exact subject or semester details are missing, ask the student "
            "to provide the course name, subject, semester, or exam title."
        ),
    },
    "course": {
        "title": "Course Support",
        "content": (
            "Students can ask about module registration, course schedules, subjects, prerequisites, "
            "semester details, and class timing. If details are missing, ask for course/program name and semester."
        ),
    },
    "assignment": {
        "title": "Assignment Help",
        "content": (
            "Students can ask about assignment deadlines, submissions, project requirements, and formatting support. "
            "If details are missing, ask for subject name, assignment title, and deadline."
        ),
    },
    "fees": {
        "title": "Fees and Payments",
        "content": (
            "Students can ask about tuition fees, payment deadlines, installment plans, receipts, and finance office guidance."
        ),
    },
    "library": {
        "title": "Library Services",
        "content": (
            "Students can ask about opening hours, borrowing books, overdue books, membership access, and digital resources."
        ),
    },
    "hostel": {
        "title": "Hostel / Accommodation",
        "content": (
            "Students can ask about hostel availability, room allocation, accommodation rules, facilities, and related payments."
        ),
    },
    "timetable": {
        "title": "Timetable",
        "content": (
            "Students can ask about weekly class timetable, exam timetable, semester schedules, room allocations, and schedule conflicts."
        ),
    },
}

KEYWORD_MAP = {
    "exam": ["exam", "test", "paper", "result", "hall", "invigilator"],
    "course": ["course", "subject", "module", "class", "program", "semester"],
    "assignment": ["assignment", "deadline", "submission", "project", "report"],
    "fees": ["fee", "fees", "payment", "tuition", "installment", "receipt"],
    "library": ["library", "book", "borrow", "overdue", "digital resource"],
    "hostel": ["hostel", "accommodation", "room", "boarding"],
    "timetable": ["timetable", "schedule", "time table", "class time"],
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def current_time() -> str:
    return datetime.now().strftime("%I:%M %p")


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "time": current_time(),
        }
    )


def safe_markdown(text: str) -> str:
    """Basic HTML-safe text for custom bubble rendering."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )


def detect_faq_topics(user_message: str) -> list[str]:
    text = user_message.lower()
    matches = []
    for topic, keywords in KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            matches.append(topic)
    return matches


def build_faq_context(user_message: str) -> str:
    topics = detect_faq_topics(user_message)
    if not topics:
        topics = ["course", "exam", "assignment", "fees"]

    parts = []
    for topic in topics[:4]:
        item = FAQ_KB.get(topic)
        if item:
            parts.append(f"{item['title']}: {item['content']}")
    return "\n\n".join(parts)


def build_history_for_prompt(max_turns: int = 8) -> str:
    history = st.session_state.messages[-max_turns:]
    lines = []
    for msg in history:
        role = "Student" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def upload_pdf_to_gemini(uploaded_file):
    """Upload PDF to Gemini Files API using a temp file path."""
    if not api_ready or client is None or uploaded_file is None:
        return None, None

    try:
        suffix = os.path.splitext(uploaded_file.name)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            temp_path = tmp.name

        gemini_file = client.files.upload(file=temp_path)
        return gemini_file, None
    except Exception as e:
        return None, str(e)


def generate_response(user_message: str) -> str:
    if not api_ready or client is None:
        return (
            "Gemini API is not connected yet.\n\n"
            "Please set your `GEMINI_API_KEY` and run the app again."
        )

    faq_context = build_faq_context(user_message)
    history_text = build_history_for_prompt()
    uploaded_doc = st.session_state.get("uploaded_gemini_file")

    system_instruction = (
        "You are Student Help Desk AI, a smart, professional, friendly assistant for students. "
        "Answer clearly and helpfully. Keep answers practical and well-structured. "
        "Use short paragraphs and bullet points only when useful. "
        "If the student has not given enough detail, ask one short clarifying question. "
        "If a PDF document is provided, prioritize that document for exact details such as timetable, notices, rules, or deadlines. "
        "If the answer is not in the provided context or PDF, say so honestly and then give the best general guidance."
    )

    prompt_text = f"""
Student FAQ context:
{faq_context}

Recent conversation:
{history_text}

Current student message:
{user_message}

Please answer as a student help desk assistant.
""".strip()

    try:
        contents = [prompt_text]
        if uploaded_doc is not None:
            contents = [uploaded_doc, prompt_text]

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            ),
        )

        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()

        return "I could not generate a response right now. Please try again."
    except Exception as e:
        return f"Gemini API error: {str(e)}"


def handle_quick_action(action_text: str) -> None:
    add_message("user", action_text)
    response = generate_response(action_text)
    add_message("assistant", response)
    st.session_state.chat_count += 1


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I’m your **Student Help Desk AI** 🎓\n\n"
                "I can help with:\n"
                "- exam information\n"
                "- course support\n"
                "- assignment deadlines\n"
                "- fee guidance\n"
                "- library / hostel / timetable questions\n\n"
                "You can also upload a PDF timetable or notice and ask questions from it."
            ),
            "time": current_time(),
        }
    ]

if "chat_count" not in st.session_state:
    st.session_state.chat_count = 1

if "uploaded_gemini_file" not in st.session_state:
    st.session_state.uploaded_gemini_file = None

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

# -------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{
            background: linear-gradient(180deg, {BG} 0%, #fafafb 100%);
            color: {TEXT};
            font-family: "Inter", "Segoe UI", sans-serif;
        }}

        .block-container {{
            padding-top:  2rem;
            padding-bottom: 1rem;
            max-width: 1200px;
        }}

        header[data-testid="stHeader"] {{
            height: auto;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(
                180deg,
                rgba(123,92,255,0.08),
                rgba(232,91,190,0.06),
                rgba(255,138,91,0.05)
            );
            border-right: 1px solid rgba(123,92,255,0.08);
        }}

        .hero {{
            background: linear-gradient(135deg, {PRIMARY_PURPLE} 0%, {PINK} 60%, {ORANGE} 100%);
            border-radius: 0 0 28px 28px;
            padding: 26px 30px;
            color: white;
            box-shadow: 0 18px 40px rgba(123, 92, 255, 0.18);
            margin-bottom: 20px;
        }}

        .hero-title {{
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 10px;
            letter-spacing: -0.4px;
        }}

        .hero-subtitle {{
            font-size: 1rem;
            opacity: 0.96;
            line-height: 1.7;
            margin: 0;
        }}

        .glass-card {{
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(255,255,255,0.6);
            backdrop-filter: blur(14px);
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 10px 28px rgba(31,41,55,0.05);
        }}

        .stat-card {{
            background: white;
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 8px 22px rgba(31,41,55,0.05);
            border: 1px solid rgba(123,92,255,0.08);
        }}

        .stat-label {{
            color: {MUTED};
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 6px;
        }}

        .stat-value {{
            color: {TEXT};
            font-size: 1.35rem;
            font-weight: 800;
        }}

        .section-title {{
            font-size: 1rem;
            font-weight: 800;
            color: {TEXT};
            margin-bottom: 8px;
        }}

        .mini-note {{
            color: {MUTED};
            font-size: 0.92rem;
            line-height: 1.6;
        }}

        .quick-card {{
            background: linear-gradient(
                135deg,
                rgba(123,92,255,0.08),
                rgba(232,91,190,0.08),
                rgba(255,138,91,0.08)
            );
            border: 1px solid rgba(123,92,255,0.10);
            border-radius: 18px;
            padding: 14px;
            min-height: 95px;
        }}

        .quick-title {{
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 6px;
        }}

        .quick-desc {{
            font-size: 0.88rem;
            color: {MUTED};
            line-height: 1.5;
        }}

        .chat-shell {{
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(255,255,255,0.65);
            border-radius: 26px;
            padding: 14px;
            box-shadow: 0 16px 35px rgba(31,41,55,0.05);
            backdrop-filter: blur(14px);
        }}

        .chat-heading {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 6px 6px 12px 6px;
            border-bottom: 1px solid rgba(123,92,255,0.08);
        }}

        .chat-heading-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .avatar-circle {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, {PRIMARY_PURPLE}, {PINK}, {ORANGE});
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            box-shadow: 0 10px 20px rgba(123,92,255,0.18);
        }}

        .online-badge {{
            background: {LIGHT_PURPLE};
            color: {PRIMARY_PURPLE};
            font-size: 0.82rem;
            padding: 8px 12px;
            border-radius: 999px;
            font-weight: 700;
        }}

        .chat-title {{
            font-size: 1rem;
            font-weight: 800;
            color: {TEXT};
            margin: 0;
        }}

        .chat-subtitle {{
            font-size: 0.88rem;
            color: {MUTED};
            margin-top: 2px;
        }}

        .msg-wrap {{
            margin-bottom: 12px;
            margin-top: 12px;
        }}

        .msg-time {{
            font-size: 0.75rem;
            color: {MUTED};
            margin-top: 4px;
            padding-left: 4px;
        }}

        .user-time {{
            text-align: right;
            padding-right: 4px;
        }}

        .assistant-bubble {{
            background: white;
            color: {TEXT};
            border: 1px solid rgba(123,92,255,0.08);
            border-radius: 18px 18px 18px 6px;
            padding: 14px 16px;
            box-shadow: 0 8px 22px rgba(31,41,55,0.04);
            max-width: 82%;
            width: fit-content;
            line-height: 1.65;
        }}

        .user-bubble {{
            background: linear-gradient(135deg, {PRIMARY_PURPLE} 0%, {PINK} 70%, {ORANGE} 100%);
            color: white;
            border-radius: 18px 18px 6px 18px;
            padding: 14px 16px;
            box-shadow: 0 10px 24px rgba(123,92,255,0.14);
            max-width: 82%;
            width: fit-content;
            margin-left: auto;
            line-height: 1.65;
        }}

        .typing-box {{
            background: white;
            border: 1px solid rgba(123,92,255,0.08);
            border-radius: 18px 18px 18px 6px;
            padding: 14px 16px;
            display: inline-flex;
            gap: 6px;
            align-items: center;
            box-shadow: 0 8px 22px rgba(31,41,55,0.04);
            margin-top: 6px;
        }}

        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {PRIMARY_PURPLE};
            display: inline-block;
            animation: blink 1.4s infinite both;
        }}

        .dot:nth-child(2) {{
            animation-delay: 0.2s;
        }}

        .dot:nth-child(3) {{
            animation-delay: 0.4s;
        }}

        @keyframes blink {{
            0% {{ opacity: 0.2; transform: translateY(0); }}
            20% {{ opacity: 1; transform: translateY(-2px); }}
            100% {{ opacity: 0.2; transform: translateY(0); }}
        }}

        .footer-text {{
            text-align: center;
            color: {MUTED};
            font-size: 0.9rem;
            margin-top: 12px;
        }}

        div.stButton > button {{
            border-radius: 14px !important;
            border: 1px solid rgba(123,92,255,0.12) !important;
            background: white !important;
            color: {TEXT} !important;
            font-weight: 600 !important;
            padding: 0.7rem 1rem !important;
            box-shadow: 0 6px 16px rgba(31,41,55,0.04);
        }}

        div.stButton > button:hover {{
            border: 1px solid rgba(123,92,255,0.24) !important;
            color: {PRIMARY_PURPLE} !important;
        }}

        .stChatInput > div {{
            border-radius: 18px !important;
            border: 1px solid rgba(123,92,255,0.14) !important;
            box-shadow: 0 10px 24px rgba(31,41,55,0.06);
            background: white !important;
        }}

        .stChatInput input {{
            color: {TEXT} !important;
        }}

        @media (max-width: 768px) {{
            .hero-title {{
                font-size: 1.6rem;
            }}
            .assistant-bubble, .user-bubble {{
                max-width: 100%;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">Student Help Desk AI</div>
            <div class="mini-note">
                Gemini-powered student chatbot with FAQ support, chat memory, and PDF document understanding.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if api_ready:
        st.success("Gemini API connected")
    else:
        st.error(api_error_message or "Gemini API not connected")

    st.write("")

    uploaded_pdf = st.file_uploader(
        "Upload PDF timetable / notice",
        type=["pdf"],
        accept_multiple_files=False,
    )

    if uploaded_pdf is not None:
        if st.button("Use This PDF", use_container_width=True):
            with st.spinner("Uploading PDF to Gemini..."):
                gemini_file, err = upload_pdf_to_gemini(uploaded_pdf)
                if err:
                    st.error(f"PDF upload failed: {err}")
                else:
                    st.session_state.uploaded_gemini_file = gemini_file
                    st.session_state.uploaded_filename = uploaded_pdf.name
                    st.success(f"PDF ready: {uploaded_pdf.name}")

    if st.session_state.uploaded_filename:
        st.info(f"Current PDF: {st.session_state.uploaded_filename}")
        if st.button("Remove PDF", use_container_width=True):
            st.session_state.uploaded_gemini_file = None
            st.session_state.uploaded_filename = None
            st.rerun()

    st.write("")

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Chat cleared successfully.\n\n"
                    "How can I help you now?"
                ),
                "time": current_time(),
            }
        ]
        st.session_state.chat_count = 1
        st.rerun()

    st.write("")

    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">Support Areas</div>
            <div class="mini-note">
                Exams, courses, assignments, fees, library services, hostel support, and timetable guidance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------
# HERO SECTION
# -------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🎓 Student Help Desk AI Chatbot</div>
        <div class="hero-subtitle">
            Modern, professional, and smart student support with Gemini AI, FAQ memory, and PDF understanding.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# TOP SUMMARY
# -------------------------------------------------
left_col, right_col = st.columns([2.1, 1], gap="large")

with left_col:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">Welcome</div>
            <div class="mini-note">
                Ask about exams, courses, deadlines, fees, library, hostel, and timetables.
                You can also upload a PDF and ask questions from that document.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    a, b = st.columns(2)
    with a:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Chats</div>
                <div class="stat-value">{st.session_state.chat_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">PDF</div>
                <div class="stat-value">{"Ready" if st.session_state.uploaded_filename else "None"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

# -------------------------------------------------
# QUICK ACTIONS
# -------------------------------------------------
st.markdown(
    """
    <div class="section-title">Quick Actions</div>
    """,
    unsafe_allow_html=True,
)

q1, q2, q3, q4 = st.columns(4, gap="small")

with q1:
    st.markdown(
        """
        <div class="quick-card">
            <div class="quick-title">Exam Info</div>
            <div class="quick-desc">Get help with exam dates, halls, and timetable details.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Ask Exam Info", use_container_width=True):
        handle_quick_action("I need help with exam information")
        st.rerun()

with q2:
    st.markdown(
        """
        <div class="quick-card">
            <div class="quick-title">Course Support</div>
            <div class="quick-desc">Ask about modules, registration, and class schedules.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Ask Course Support", use_container_width=True):
        handle_quick_action("I need help with my course and subjects")
        st.rerun()

with q3:
    st.markdown(
        """
        <div class="quick-card">
            <div class="quick-title">Assignment Help</div>
            <div class="quick-desc">Check deadlines, submissions, and assignment guidance.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Ask Assignment Help", use_container_width=True):
        handle_quick_action("I need help with assignment deadlines")
        st.rerun()

with q4:
    st.markdown(
        """
        <div class="quick-card">
            <div class="quick-title">Timetable / PDF</div>
            <div class="quick-desc">Ask questions using your uploaded timetable or notice PDF.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Ask About Uploaded PDF", use_container_width=True):
        handle_quick_action("Please summarize the uploaded PDF and tell me the key student details.")
        st.rerun()

st.write("")

# -------------------------------------------------
# CHAT CONTAINER
# -------------------------------------------------
st.markdown(
    """
    <div class="chat-shell">
        <div class="chat-heading">
            <div class="chat-heading-left">
                <div class="avatar-circle">AI</div>
                <div>
                    <div class="chat-title">Live Student Support</div>
                    <div class="chat-subtitle">Gemini AI + FAQ context + chat history + PDF support</div>
                </div>
            </div>
            <div class="online-badge">● Online</div>
        </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# CUSTOM CHAT DISPLAY
# -------------------------------------------------
for message in st.session_state.messages:
    role = message["role"]
    content = safe_markdown(message["content"])
    msg_time = message.get("time", "")

    if role == "assistant":
        st.markdown(
            f"""
            <div class="msg-wrap">
                <div class="assistant-bubble">{content}</div>
                <div class="msg-time">{msg_time}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="msg-wrap">
                <div class="user-bubble">{content}</div>
                <div class="msg-time user-time">{msg_time}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# CHAT INPUT
# -------------------------------------------------
prompt = st.chat_input("Type your question here...")

if prompt:
    add_message("user", prompt)
    st.session_state.chat_count += 1

    st.markdown(
        """
        <div class="typing-box">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.7)

    response = generate_response(prompt)
    add_message("assistant", response)
    st.rerun()

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown(
    """
    <div class="footer-text">
        Built with Gemini AI and a modern purple-pink-orange professional student support interface
    </div>
    """,
    unsafe_allow_html=True,
)
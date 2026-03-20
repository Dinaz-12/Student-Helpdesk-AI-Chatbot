# 🎓 Student Help Desk AI Chatbot

A modern AI-powered student support chatbot built using **Streamlit** and **Google Gemini AI**.
This system helps students get quick answers about exams, courses, assignments, and more — with optional **PDF document understanding**.

---

## 🚀 Live Demo

👉 https://student-appdesk-ai-chatbot-i6ddaj6jqjcazjkfq86e97.streamlit.app/

---

## ✨ Features

* 🤖 AI-powered chatbot using Gemini
* 📄 Upload PDF and ask questions from documents
* 🧠 Context-aware responses (chat + document)
* 💬 Clean and modern chat UI
* 🌗 Light/Dark mode support
* 📊 Sidebar with chat stats and document status
* 🔐 Secure API key handling using Streamlit secrets

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** Python
* **AI Model:** Google Gemini API
* **PDF Processing:** PyPDF2
* **Deployment:** Streamlit Cloud

---

## 📂 Project Structure

```
student-helpdesk-chatbot/
│
├── app.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── secrets.toml (not included in repo)
```

---

## ⚙️ Installation (Run Locally)

### 1. Clone the repository

```
git clone https://github.com/Dinaz-12/Student-Helpdesk-AI-Chatbot.git
cd Student-Helpdesk-AI-Chatbot
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Add your API key

Create a file:

```
.streamlit/secrets.toml
```

Add:

```
GEMINI_API_KEY = "your_api_key_here"
```

### 4. Run the app

```
streamlit run app.py
```

---

## 🔐 Security Note

* Do NOT upload your API key to GitHub
* Always use `.streamlit/secrets.toml`
* Add this to `.gitignore`:

```
.streamlit/secrets.toml
```

---

## 🧠 How It Works

1. User enters a question
2. Chat history + PDF content (if available) is added as context
3. Gemini AI generates a response
4. Answer is displayed in a clean chat UI

---

## 📄 PDF Support

* Upload any PDF (timetable, notice, etc.)
* The system extracts text
* AI answers questions based on document content

---

## 🎯 Future Improvements

* 🔍 Advanced RAG (semantic search)
* 🎤 Voice-based chatbot
* 📊 Admin dashboard
* 🌐 Multi-user support
* 📚 Knowledge base integration

---

## 👨‍💻 Author

**Kavidu Keshan**
Data Science Undergraduate

---

## ⭐ Acknowledgements

* Google Gemini AI
* Streamlit
* Open-source community

---

## 📌 Notes

This project was built as a beginner-to-intermediate level AI application to demonstrate:

* Prompt engineering
* AI integration
* UI/UX design
* Deployment skills

---

## ⭐ Give a Star

If you like this project, give it a ⭐ on GitHub!

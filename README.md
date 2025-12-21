# 📘 Syllabus Smart Search

Syllabus Smart Search is an AI-assisted academic web application that helps students find **exact textbook definitions and diagrams** for syllabus topics from uploaded textbooks.

Unlike chatbots, this system ensures that **only textbook content** is shown, making it ideal for exams and academic validation.

---

## 🚀 Features

- 🔐 User authentication (Login & Register)
- 📂 Per-user textbook uploads (privacy protected)
- 📄 PDF text & diagram extraction
- 🧠 AI-powered semantic topic matching
- 📚 Exact textbook definitions (no hallucination)
- 🖼️ Related diagrams from correct pages
- 📊 Confidence score for accuracy
- 🗑️ Delete uploaded PDFs
- 🎨 Clean, responsive UI

---

## 🧠 How It Works

1. User enters a syllabus topic
2. AI generates a **hidden reference definition**
3. Reference is converted to a semantic vector
4. Textbook paragraphs are compared semantically
5. Closest matching textbook definition is selected
6. Diagrams from the same page are displayed
7. Only textbook content is shown to the user

---

## 🛠️ Tech Stack

| Layer    | Technology            |
| -------- | --------------------- |
| Backend  | Django (Python)       |
| Database | SQLite                |
| AI       | Gemini API            |
| ML       | SentenceTransformers  |
| Frontend | HTML, CSS, JavaScript |
| Auth     | Django Authentication |

---

## ⚙️ Installation

python -m venv venv
venv\Scripts\activate # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

```

```

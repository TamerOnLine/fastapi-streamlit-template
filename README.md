# 🧾 fastapi-streamlit-templale

An interactive **Resume Builder** built with **FastAPI** (backend) and **Streamlit** (frontend).  
Generates modern, two-column resumes with full **Arabic (RTL)** support, dynamic themes, and editable sections.

---

## ✨ Key Features

- ⚡ **FastAPI Backend** — Generates PDF resumes dynamically using ReportLab.  
- 🎨 **Streamlit Frontend** — Simple, tab-based interface to edit profile details.  
- 🧱 **Modular PDF Blocks** — Header, photo, projects, education, skills, languages, and more.  
- 🌍 **Multilingual Support** — Arabic, English, German.  
- 🖼️ **Themes System** — Multiple ready-made styles (default, bold header, modern, clean white…).  
- 💾 **Profiles & History** — Auto-save and re-use user profiles and generated files.  

---

## 🚀 Quick Start

```bash
# 1️⃣ Install dependencies
pip install -r requirements.txt

# 2️⃣ Run backend (FastAPI)
uvicorn api.main:app --reload

# 3️⃣ Run frontend (Streamlit)
streamlit run streamlit/app.py
```

- FastAPI docs → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- Streamlit UI → [http://localhost:8501](http://localhost:8501)

---

## 📂 Project Structure

```
fastapi-streamlit-templet/
├── api/                 # FastAPI backend (PDF generation)
│   ├── pdf_utils/       # Fonts, icons, blocks, and themes loader
│   ├── routes/          # API endpoints
│   └── utils/           # Helper parsers
├── streamlit/           # Frontend tabs & UI logic
├── themes/              # Theme configuration files (.json)
├── outputs/             # Generated PDFs
├── profiles/            # Saved user profiles
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 📜 License

Licensed under the [MIT License](LICENSE) — © 2025 **Tamer Hamad Faour**

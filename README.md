# TalentLens | AI Candidate Ranking & Recruiter Console

TalentLens is an AI-powered candidate evaluation, ranking, and explanation engine designed for the **Redrob Data & AI Challenge**. It is a locally-run application that parses candidate profiles, performs dense semantic similarity searches against job descriptions, applies rule-based filtering (for experience tenure and educational degrees), penalizes hidden keyword stuffing (honeypot detection), and utilizes Groq LLMs (Llama 3.3) to draft structured recruiter fit cards and interview questions.

---

## Architecture & System Design

1. **Streaming Candidate Ingestion**: Built with a memory-efficient streaming generator parsing JSONL resume datasets in $O(1)$ RAM overhead.
2. **Hybrid Composite Scoring**:
   * **Semantic Similarity**: Vector embeddings generated locally using `sentence-transformers/all-MiniLM-L6-v2` (90 MB, 384 dimensions) index candidates via FAISS flat inner-product search.
   * **Honeypot keyword Penalty**: Detects and penalizes candidates trying to manipulate search rankings by stuffing repeated keywords in hidden profile summaries.
   * **Hard Disqualifiers**: Employs Regex boundaries to filter out candidates who do not meet mandatory criteria (e.g. minimum years of experience, target degrees).
   * **Core Criteria Matchers**: Scores candidates across skills inventories, behavioral action verbs (leadership, delivery, teamwork), and educational pedigree.
3. **AI Explanations**: Integrates with Groq API (Llama-3.3-70b-versatile) to dynamically compile fit evaluations, highlights, concerns, and interview questions. Fully supports local rule-based template fallbacks if the LLM backend is offline or rate-limited.
4. **Recruiter Console**: React and Vite dashboard containing job creation modals, upload panels, dynamic leaderboards, SVG score distribution charts, detail drawers, and ranked CSV exporter.

---

## Local Development Setup

### 1. Prerequisites
Ensure you have the following installed on your local system:
* **Python 3.10+**
* **Node.js 18+**

---

### 2. Backend Server Setup

All commands should be executed from the **root directory** of the project repository.

1. **Create Virtual Environment**:
   ```powershell
   python -m venv .venv
   ```

2. **Activate Virtual Environment**:
   * **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     source .venv/bin/activate
     ```

3. **Install Dependencies**:
   ```powershell
   pip install -r backend/requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file inside the `backend/` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   DATABASE_URL=sqlite:///./talentlens.db
   ```
   *(Note: The database will be created automatically at `backend/talentlens.db` during server startup).*

5. **Start FastAPI Backend Server**:
   Run the following command from the project root:
   ```powershell
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend API will run at `http://127.0.0.1:8000/`. You can view the interactive Swagger docs at `http://127.0.0.1:8000/docs`.

---

### 3. Frontend App Setup

1. **Navigate to the Frontend Directory**:
   ```powershell
   cd frontend
   ```

2. **Install Dependencies**:
   ```powershell
   npm install
   ```

3. **Start the React Dev Server**:
   ```powershell
   npm run dev
   ```
   The frontend console dashboard will run at `http://localhost:5173/`. Open it in your web browser to start recruiting.

---

### 4. Running Backend Test Suites

We have implemented a comprehensive test suite (24 passing tests) covering ingestion parser safety, JD extractors, vector embeddings, scoring systems, database pipelines, and FastAPI endpoints.

To run the automated tests, execute from the **root directory** of the repository:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

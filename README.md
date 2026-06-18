# TalentLens | AI Candidate Ranking & Recruiter Console

An AI-powered candidate evaluation, ranking, and explanation engine designed for the **Redrob Data & AI Challenge**. TalentLens parses candidate resumes, computes dense semantic similarities against job descriptions, identifies honeypot keyword-stuffing, evaluates candidate tenure growth, soft skills, and academic alignments, and uses Groq AI (Llama 3.3) to generate recruiter summaries and screening questions.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/LAXMAN7795/TalentLens-redrob-ai-challenge)

---

## Key Features

1. **Memory-Efficient Parsing**: Streams candidate JSONL files line-by-line using an $O(1)$ memory footprint to handle datasets up to 100,000+ records.
2. **Hybrid Scoring Engine**:
   * **Semantic Search**: Uses `BAAI/bge-large-en-v1.5` embeddings and Flat Inner Product FAISS indices to perform semantic matching.
   * **Honeypot Penalty**: Detects and penalizes hidden keyword stuffing (e.g. repeating keywords like `Python` in invisible sections) and timelines manipulation.
   * **Mandatory Disqualifiers**: Employs Regex word-boundary filtering to filter out candidates who do not meet minimum experience years or degree qualifications.
   * **Custom Criteria Scorers**: Evaluates core skills inventories, role stability, behavioral verbs (leadership, delivery, teamwork), and education GPA bonuses.
3. **AI Recruiter Drawer Cards**: Queries Groq (Llama 3.3) to compile fit summaries, candidate strengths, gaps/concerns, and custom screening questions.
4. **Interactive Console**: Built with React, Vite, and Tailwind CSS. Features role creation, progress polling, dynamic leaderboards, score distribution charts, and client-side CSV downloads.

---

## One-Click Deployment (Render)

Click the **Deploy to Render** button above. Render will read our [render.yaml](render.yaml) blueprint and provision:
1. **FastAPI Web Service**: Compiles the backend container, downloads/caches the BGE model, and serves the API. *(Configured on the **Starter** instance type to provide the 2 GB RAM required for ML models).*
2. **React Static Site**: Builds the React frontend and connects it dynamically to your backend service.

During deployment, Render will prompt you for your `GROQ_API_KEY`. Simply input your key and the build will execute automatically!

---

## Local Development Setup

### 1. Prerequisites
Ensure you have the following installed:
* Python 3.10+
* Node.js 18+

### 2. Backend Server Setup
1. Navigate to `backend/` and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend/` folder and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   DATABASE_URL=sqlite:///talentlens.db
   ```
4. Start the FastAPI server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```

### 3. Frontend App Setup
1. Navigate to the `frontend/` folder:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite server:
   ```bash
   npm run dev
   ```
3. Open your browser and navigate to `http://localhost:5173/`.

### 4. Running Tests
To run the full suite of backend unit and performance tests, run the following command in the root workspace:
```bash
$env:PYTHONPATH="."  # Set pythonpath
.venv\Scripts\pytest
```

# TalentLens Deployment Guide

This guide outlines instructions for deploying the **TalentLens Candidate Ranking Engine & Recruiter Console** to cloud environments.

---

## Technical Constraints & Requirements
* **RAM Allocation**: The backend uses the `BAAI/bge-large-en-v1.5` SentenceTransformer model (approx. 1.34 GB on disk). In production, the backend requires a minimum of **2 GB RAM** (4 GB recommended) to avoid Out Of Memory (OOM) crashes during startup or retrieval.
* **API Dependencies**: A valid `GROQ_API_KEY` is required. The model configured is `llama-3.3-70b-versatile` in JSON mode.

---

## 1. Backend Deployment (FastAPI)

### Option A: Render.com (Docker Web Service)
Render can compile the backend using the pre-configured `backend/Dockerfile` automatically.
1. Sign in to [Render](https://render.com/).
2. Create a new **Web Service** and connect your GitHub repository: `TalentLens-redrob-ai-challenge`.
3. Set the following settings:
   * **Language**: `Docker`
   * **Docker Command**: Leave default (Docker will execute the instructions in `backend/Dockerfile`)
   * **Instance Type**: **Starter** (2 GB RAM) or higher. *Do not use the Free tier (512 MB) as it will crash due to the size of the transformer model.*
4. Add the following **Environment Variables** in the dashboard:
   * `GROQ_API_KEY`: `your_groq_api_key_here`
   * `DATABASE_URL`: `sqlite:///app/backend/talentlens.db` (or a PostgreSQL connection string if you provision a database on Render)
   * `PYTHONPATH`: `/app`
5. Click **Deploy Web Service**. Render will build the container, download and cache the embedding model, and launch the API server.

---

### Option B: Railway.app (Docker Web Service)
Railway is highly recommended for Dockerized FastAPI servers.
1. Sign in to [Railway](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo** -> Select `TalentLens-redrob-ai-challenge`.
3. Go to the service **Variables** tab and add:
   * `GROQ_API_KEY`: `your_groq_api_key_here`
   * `DATABASE_URL`: `sqlite:///app/backend/talentlens.db`
   * `PYTHONPATH`: `/app`
4. Railway will read `backend/Dockerfile` in the repository, build the image, and serve the API.

---

### Option C: Virtual Private Server (VPS) via Docker Compose
If deploying on a Linux VM (AWS EC2, DigitalOcean Droplet, Linode, etc.), copy the following `docker-compose.yml` into your server directory:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=your_groq_api_key_here
      - DATABASE_URL=sqlite:///app/backend/talentlens.db
      - PYTHONPATH=/app
    volumes:
      - backend-data:/app/backend/outputs

  frontend:
    image: node:18-alpine
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://<YOUR_SERVER_IP>:8000/api
    command: sh -c "npm install && npm run dev -- --host"

volumes:
  backend-data:
```

---

## 2. Frontend Deployment (React + Vite)

The React frontend should be deployed as a static site. The best and free platform for this is **Vercel**.

### Deploying on Vercel
1. Sign in to [Vercel](https://vercel.com/).
2. Click **Add New** -> **Project** -> Connect your GitHub repository: `TalentLens-redrob-ai-challenge`.
3. Configure the build settings:
   * **Framework Preset**: `Vite`
   * **Root Directory**: `frontend`
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist`
4. Add the following **Environment Variables**:
   * `VITE_API_URL`: The public URL of your deployed backend (e.g. `https://your-backend.onrender.com/api` or `https://your-backend.railway.app/api`).
5. Click **Deploy**. Vercel will build and serve your static React application on a global CDN.

---

## 3. Database Schema Initialization

FastAPI uses an `asynccontextmanager` lifecycle hook in `backend/main.py` that automatically triggers `init_db()` upon container startup.
* When the backend boots up, it will check if `talentlens.db` exists.
* If it does not exist, it will auto-create all database tables and relational models.
* No manual migration commands are required for SQLite deployments!

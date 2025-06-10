# 🤖 AZIA: AI Global Search Agent

<div align="center">
  <img src="AZIA cover.png" alt="Logo de AZIA" width="600"/>
</div>

AZIA is the AI platform for company analysis, developed in collaboration with [Azvalor Asset Management](https://www.azvalor.com/en/). It offers a suite of intelligent agents designed to enhance financial research and decision-making:
- 🌐**RAG Agent:**  Searches and analyzes the documents you upload (such as financial reports or company filings) to extract relevant insights that you request for investment analysis.
- 🔍**Web Search Agent:** Gathers real-time information and screening reports from the Internet, helping you stay updated on industries, companies and individuals.
- 🤖**Global Agent:** Combines both document and web search capabilities, being able to search both locally and externally in parallel.

All agents feature **in-conversation memory**, allowing them to retain context across interactions and progressively refine their responses based on your inputs.
---

## 🗂️ Project Structure

```
AZIA/
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/
│   │   ├── app.py
│   │   ├── .env
│   │   ├── processed_files/
│   │   ├── uploaded_files/
│   │   └── routes/
│   │       ├── global_agent.py
│   │       ├── rag_agent.py
│   │       └── web_search_agent.py
│   ├── services/
│   │   ├── chat_service.py
│   │   ├── file_processor.py
│   │   ├── vector_db.py
│   │   ├── vector_db_utils.py
│   │   └── agents/
│   │       └── vectorstore_chromadb_automatic/
│   │           └── chroma.sqlite3
│   └── .gitignore
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── ...
│   ├── .gitignore
│   ├── app/
│   │   ├── globals.css
│   │   ├── icon.ico
│   │   ├── icon.png
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── agent-interface.tsx
│   │   ├── chat-interface.tsx
│   │   ├── conversation-panel.tsx
│   │   ├── file-upload.tsx
│   │   ├── global-agent.tsx
│   │   ├── home-screen.tsx
│   │   ├── markdown-message.tsx
│   │   ├── rag-agent.tsx
│   │   ├── theme-provider.tsx
│   │   ├── web-search-agent.tsx
│   │   └── ui/
│   │       ├── ... (múltiples componentes UI reutilizables)
│   ├── hooks/
│   │   ├── use-mobile.tsx
│   │   └── use-toast.ts
│   ├── lib/
│   │   ├── api-service.ts
│   │   ├── conversation-store.ts
│   │   └── utils.ts
│   ├── public/
│   │   ├── placeholder-logo.png
│   │   ├── ...
│   └── styles/
│       └── globals.css
│
├── docker-compose.yml
├── .dockerignore
├── .env
├── .gitignore
├── .npmrc
└── README.md
```

---

## ⚙️ Prerequisites

- Docker and Docker Compose (if using option 1)
- Node.js (v20+) and npm (only if using option 2)
- Python 3.12+ and pip (only if using option 2)
- API Keys: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `LLAMA_CLOUD_API_KEY`

---

## 📥 Download the code

1. **Clone the repository**  
   Open a terminal and execute:
   ```powershell
   git clone https://github.com/Albertogf4/AZIA_Agents.git
   cd AZIA_Agents

   Or download the zip.

## 🚀 Option 1: Setup with Docker Compose (Recommended)

1. **Set up your environment variables**  
    Create a `.env` file at the project root with your keys:
    ```env
    OPENAI_API_KEY=your_key
    TAVILY_API_KEY=your_key
    LLAMA_CLOUD_API_KEY=your_key
    ```

2. **Start the services**  
    Open a terminal at the project root and run:
    ```powershell
    docker-compose up --build
    ```
    This will start both the backend (Flask, port 5328) and the frontend (Next.js, port 3000).

3. **Access the application**  
    Go to [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🛠️ Option 2: Manual Setup (Frontend and Backend separately)

### 🔙 Backend

1. **Create and activate a virtual environment (optional but recommended)**
    ```powershell
    cd backend
    python -m venv venv
    .\venv\Scripts\activate
    ```

2. **Install dependencies**
    ```powershell
    pip install -U langgraph==0.3.34
    pip install -r requirements.txt
    ```

3. **Set up environment variables**  
    You can use a `.env` file or export them in your terminal:
    ```powershell
    $env:OPENAI_API_KEY="your_key"
    $env:TAVILY_API_KEY="your_key"
    $env:LLAMA_CLOUD_API_KEY="your_key"
    ```

4. **Start the backend**
    ```powershell
    cd backend/api
    flask run --host=127.0.0.1 --port=5328
    ```

### 🖥️ Frontend

1. **Install dependencies**
    ```powershell
    cd frontend
    npm install
    ```

2. **Set up environment variable**  
    Create a `.env.local` file in `frontend/`:
    ```env
    NEXT_PUBLIC_API_BASE_URL=http://localhost:5328
    ```

3. **Start the frontend**
    ```powershell
    npm run dev
    ```
    Access [http://localhost:3000](http://localhost:3000).

---

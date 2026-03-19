# AutoGuru

A car manual Q&A application that uses a LangGraph ReAct agent with AWS Bedrock to answer questions about specific vehicles by searching their owner's manuals. Users select a car, ask questions in a chat interface, and get markdown-formatted answers with source page references.

To see a demo of the original version, click [here](https://www.youtube.com/watch?v=09DRVQz9MmQ)

## Architecture

### Backend (Python / FastAPI)

- **`app.py`** — FastAPI server with CORS. Endpoints:
  - `POST /chat` — Streams agent responses as SSE events (`token`, `sources`, `done`, `error`)
  - `GET /vehicles` — Dynamically scans the `vectordbs/` directory to return all available vehicles
  - `POST /upload` — Accepts a PDF link + make/model/year, downloads the PDF, and creates vector databases for it
  - `GET /health` — Health check
- **`agent.py`** — Creates a LangGraph ReAct agent using `ChatBedrockConverse` (AWS Bedrock) with a `search_vehicle_manual` tool that queries ChromaDB. The agent autonomously decides when and how many times to search the manual before answering.
- **`vectorstore.py`** — Loads ChromaDB vector stores (`full_db` and `sum_db`) for a given vehicle. Uses a singleton `HuggingFaceEmbeddings` instance (`all-mpnet-base-v2`).
- **`vectordb_util/pdf_to_vectordb.py`** — Pipeline to convert a PDF manual into two ChromaDB vector databases: one with full chunked text and one with chunks summarized via an AWS Bedrock LLM. Entry point: `create_vectordbs_from_pdf(file_path, output_folder, embedding_path)`.
- **`vectordb_util/pdf_util.py`** — PDF text extraction using PyMuPDF, outputs one `.txt` file per page.
- **`vectordbs/`** — Pre-built and user-added ChromaDB databases organized as `{make}/{model}/{year}/{full_db|sum_db}`. Each vehicle folder may contain a `meta.json` with the PDF link for source references.

### Frontend (React / Vite)

- Vite + React 19 + Mantine UI v7 + react-router-dom v7
- **`src/Pages/Home.jsx`** — Vehicle selection page (brand → model → year dropdowns), populated dynamically from the backend's `GET /vehicles` endpoint. Includes an "Add Manual" button that opens a modal to add a new vehicle by providing a PDF link and make/model/year.
- **`src/Pages/Chat.jsx`** — Full-height chat interface with message history, streaming markdown responses, and per-message source page links.
- **`src/Controllers/api_interactions.js`** — API client: SSE streaming for chat, vehicle list fetching, and manual submission.
- **`src/Controllers/select_controller.js`** — Helpers for populating vehicle selection dropdowns from the vehicle data returned by the backend.

## Setup

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

AWS credentials are required (env vars or AWS CLI profile):
```bash
export AWS_REGION=us-east-1
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # Vite dev server on http://localhost:3000
npm run build  # Production build to dist/
```

## Adding a New Vehicle

From the frontend home page, click **Add Manual** and provide:
1. A direct link to the PDF owner's manual
2. The vehicle's make, model, and year

The backend will download the PDF, extract text, generate summaries using an AWS Bedrock model, create the vector databases, and save the PDF link for source references. The new vehicle will immediately appear in the selection dropdowns.

## Background

I had the idea for this project when I was driving from Austin to Dallas and got stuck with a flat tire in a random McDonald's parking lot. I'd never changed a tire before, and in that moment I realized how helpful it would be if I could ask someone specific things about my car, like where the reinforced areas are, or how strong of a jack I needed. That thought led me to creating this website, which allows a user to select their car's make and model, and ask specific questions about it.

The project originally used a local google flan-t5-large model with a simple prompt chain and a local bart-large-cnn model for summarization. It has since been rebuilt to use AWS Bedrock LLMs with a LangGraph ReAct agent architecture, and the summarization pipeline now also uses a Bedrock model instead of running locally.

import json
import os
import re
import tempfile

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent import create_autoguru_agent
from vectordb_util.pdf_to_vectordb import create_vectordbs_from_pdf

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTORDBS_DIR = os.path.join(os.path.dirname(__file__), "vectordbs")
EMBEDDING_DIR = os.path.join(os.path.dirname(__file__), "embedding")

# Cache agents by db_id to avoid re-creating per request
_agents: dict = {}


def get_agent(db_id: str):
    if db_id not in _agents:
        vectordbs_root = os.path.join(VECTORDBS_DIR, db_id)
        if not os.path.isdir(vectordbs_root):
            raise HTTPException(status_code=404, detail=f"No vector DB found for '{db_id}'")
        _agents[db_id] = create_autoguru_agent(db_id)
    return _agents[db_id]


class ChatRequest(BaseModel):
    input_text: str
    db_id: str


@app.post("/chat")
async def chat_stream(req: ChatRequest):
    """Single endpoint: streams the agent's response as SSE events."""
    agent = get_agent(req.db_id)

    async def event_generator():
        try:
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": req.input_text}]},
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    content = chunk.content
                    # Handle content as string or list of content blocks
                    if isinstance(content, str) and content:
                        yield {
                            "event": "token",
                            "data": json.dumps({"token": content}),
                        }
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                                yield {
                                    "event": "token",
                                    "data": json.dumps({"token": block["text"]}),
                                }

                elif kind == "on_tool_end":
                    tool_output = event["data"].get("output", "")
                    pages = re.findall(r"\[Page (\d+)\]", str(tool_output))
                    if pages:
                        yield {
                            "event": "sources",
                            "data": json.dumps({"pages": sorted(set(pages))}),
                        }

            yield {"event": "done", "data": "{}"}

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator())


@app.get("/vehicles")
async def list_vehicles():
    """Scan vectordbs/ directory and return all available vehicles."""
    vehicles = {}
    if not os.path.isdir(VECTORDBS_DIR):
        return vehicles
    for make in sorted(os.listdir(VECTORDBS_DIR)):
        make_path = os.path.join(VECTORDBS_DIR, make)
        if not os.path.isdir(make_path) or make.startswith("."):
            continue
        vehicles[make] = {}
        for model in sorted(os.listdir(make_path)):
            model_path = os.path.join(make_path, model)
            if not os.path.isdir(model_path) or model.startswith("."):
                continue
            vehicles[make][model] = {}
            for year in sorted(os.listdir(model_path)):
                year_path = os.path.join(model_path, year)
                if not os.path.isdir(year_path) or year.startswith("."):
                    continue
                # Only include if it has full_db or sum_db
                if os.path.isdir(os.path.join(year_path, "full_db")):
                    entry = {"db_id": f"{make}/{model}/{year}"}
                    meta_path = os.path.join(year_path, "meta.json")
                    if os.path.isfile(meta_path):
                        with open(meta_path) as f:
                            entry.update(json.load(f))
                    vehicles[make][model][year] = entry
            if not vehicles[make][model]:
                del vehicles[make][model]
        if not vehicles[make]:
            del vehicles[make]
    return vehicles


class AddManualRequest(BaseModel):
    link: str
    make: str
    model: str
    year: str


@app.post("/upload")
async def add_manual(req: AddManualRequest):
    """Download a PDF manual from a link and create vector databases for it."""
    make = req.make.strip().lower()
    model = req.model.strip().lower()
    year = req.year.strip()
    link = req.link.strip()

    db_id = f"{make}/{model}/{year}"
    output_folder = os.path.join(VECTORDBS_DIR, db_id)

    if os.path.isdir(output_folder) and os.path.isdir(os.path.join(output_folder, "full_db")):
        raise HTTPException(status_code=409, detail=f"Vector DB already exists for '{db_id}'")

    # Download the PDF to a temp file
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
            resp = await client.get(link)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    try:
        create_vectordbs_from_pdf(tmp_path, output_folder, EMBEDDING_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vector DB: {e}")
    finally:
        os.unlink(tmp_path)

    # Save the link in meta.json so it's available for source references
    with open(os.path.join(output_folder, "meta.json"), "w") as f:
        json.dump({"link": link}, f)

    # Clear cached agent if it existed
    _agents.pop(db_id, None)

    return {"status": "ok", "db_id": db_id}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

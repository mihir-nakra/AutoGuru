import json
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent import create_autoguru_agent

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache agents by db_id to avoid re-creating per request
_agents: dict = {}


def get_agent(db_id: str):
    if db_id not in _agents:
        vectordbs_root = os.path.join(os.path.dirname(__file__), "vectordbs", db_id)
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


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

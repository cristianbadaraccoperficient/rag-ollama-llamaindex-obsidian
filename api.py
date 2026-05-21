from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from query import build_query_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validate(create_dirs=False)
    app.state.query_engine = build_query_engine()
    yield


app = FastAPI(title="RAG Obsidian API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class QueryRequest(BaseModel):
    question: str


class SourceNote(BaseModel):
    title: str
    score: float | None
    tags: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceNote]


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    response = app.state.query_engine.query(req.question)

    sources = [
        SourceNote(
            title=n.node.metadata.get("note_title") or n.node.metadata.get("file_name", "unknown"),
            score=round(n.score, 4) if n.score is not None else None,
            tags=n.node.metadata.get("tags", ""),
        )
        for n in response.source_nodes
    ]

    return QueryResponse(answer=str(response), sources=sources)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)

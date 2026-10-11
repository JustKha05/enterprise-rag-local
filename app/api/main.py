import logging
from typing import Literal
from pathlib import Path
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import settings
from app.rag.pipeline import RAGPipeline


logger = logging.getLogger(__name__)

DATASETS = {
    "nist": {
        "title": "NIST Cybersecurity Framework 2.0",
        "collection": "nist_csf2_minilm_v1",
    },
    "kubernetes": {
        "title": "Kubernetes Deployments",
        "collection": "kubernetes_minilm_v1",
    },
}

class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=6, ge=1, le=6)

    dataset: Literal["nist", "kubernetes"] = "nist"

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query must not be blank")
        return value


class SourceResponse(BaseModel):
    label: str
    document_id: str | None
    title: str | None
    version: str | None
    chunk_id: str | None
    source: str | None
    source_url: str | None
    pdf_page: int | None
    score: float
    content: str


class AskResponse(BaseModel):
    query: str
    model: str
    collection: str
    answer: str
    sources: list[SourceResponse]
    retrieval_seconds: float
    generation_seconds: float
    done_reason: str | None
    dataset: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline = RAGPipeline()
    app.state.pipeline = pipeline
    app.state.ask_lock = Lock()

    try:
        yield
    finally:
        pipeline.close()


app = FastAPI(
    title="Enterprise RAG Local",
    version="0.1.0",
    lifespan=lifespan,
)

WEB_FILE = (
    Path(__file__).resolve().parents[1]
    / "web"
    / "index.html"
)


@app.get("/", response_class=FileResponse, include_in_schema=False)
def home():
    return FileResponse(WEB_FILE, media_type="text/html")

@app.get("/health")
def health(request: Request):
    return {
        "status": "ok",
        "model": request.app.state.pipeline.model_name,
        "datasets": DATASETS,
    }


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request):
    lock = request.app.state.ask_lock

    if not lock.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail="A question is being processed. Try again later.",
            headers={"Retry-After": "10"},
        )

    try:
        pipeline = request.app.state.pipeline
        collection_name = DATASETS[body.dataset]["collection"]
        result = pipeline.ask(
            query=body.query,
            top_k=body.top_k,
            collection_name=collection_name,
        )

        sources = []

        for index, item in enumerate(result.sources, start=1):
            metadata = item.document.metadata

            sources.append(
                SourceResponse(
                    label=f"S{index}",
                    document_id=metadata.get("document_id"),
                    title=metadata.get("title"),
                    version=metadata.get("version"),
                    chunk_id=metadata.get("chunk_id"),
                    source=metadata.get("source"),
                    source_url=metadata.get("source_url"),
                    pdf_page=metadata.get("pdf_page"),
                    score=item.score,
                    content=item.document.page_content,
                )
            )

        return AskResponse(
            query=body.query,
            model=pipeline.model_name,
            dataset=body.dataset,
            collection=collection_name,
            answer=result.answer,
            sources=sources,
            retrieval_seconds=result.retrieval_seconds,
            generation_seconds=result.generation_seconds,
            done_reason=result.done_reason,
        )

    except Exception:
        logger.exception("RAG request failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question. Check server logs.",
        ) from None

    finally:
        lock.release()
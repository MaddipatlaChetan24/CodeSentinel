"""FastAPI backend for the CodeSentinel web dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from codesentinel.providers import first_available, get_provider
from codesentinel.review import review_source
from codesentinel.rules import RuleConfig
from codesentinel.web import db

app = FastAPI(title="CodeSentinel Code Review")

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


class ReviewRequest(BaseModel):
    code: str
    language: str = "python"
    target: str = "<dashboard submission>"
    provider: str | None = None
    use_llm: bool = True


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


@app.post("/api/review")
def api_review(req: ReviewRequest) -> dict:
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="code must not be empty")

    provider = None
    if req.use_llm:
        provider = get_provider(req.provider) if req.provider else first_available()

    result = review_source(
        req.code,
        language=req.language,
        target=req.target,
        provider=provider,
        rule_config=RuleConfig.load(),
    )
    db.save_review(result)
    return result.to_dict()


@app.get("/api/history")
def api_history(limit: int = 50) -> list[dict]:
    return db.list_reviews(limit=limit)


@app.get("/api/history/{review_id}")
def api_history_detail(review_id: int) -> dict:
    result = db.get_review(review_id)
    if result is None:
        raise HTTPException(status_code=404, detail="review not found")
    return result


@app.get("/api/providers")
def api_providers() -> dict:
    names = ["openai", "anthropic", "ollama"]
    return {name: get_provider(name).is_available() for name in names}

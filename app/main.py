import json
import logging
import secrets
import time
import uuid
import asyncio

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse

from app.config import settings
from app.schemas import ChatCompletionRequest
from app.services.sessions import SessionManager
from app.runtime.claude_code import ClaudeCodeRuntime

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

security = HTTPBearer()

sessions = SessionManager(settings.data_dir)
runtime = ClaudeCodeRuntime()


async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not secrets.compare_digest(credentials.credentials, settings.gateway_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}


@app.get("/v1/models")
async def list_models(authenticated: bool = Depends(authenticate)):
    discovered = await asyncio.to_thread(runtime.models)

    return {
        "object": "list",
        "data": [
            {
                "id": model["id"],
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            }
            for model in discovered
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest, authenticated: bool = Depends(authenticate)
):
    if request.model not in settings.models:
        raise HTTPException(status_code=404, detail=f"Unknown model: {request.model}")

    session_id = sessions.create()

    messages = [message.model_dump() for message in request.messages]

    options = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    if request.stream:

        async def event_stream():
            completion_id = f"chatcmpl-{uuid.uuid4().hex}"

            try:
                async for item in runtime.stream(
                    model=request.model,
                    messages=messages,
                    session_id=session_id,
                    max_tokens=request.max_tokens,
                    tools=request.tools,
                    tool_choice=request.tool_choice,
                    top_p=request.top_p,
                    stop=request.stop,
                    extra_body=request.extra_body,
                    response_format=request.response_format,
                ):
                    chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": item["delta"],
                            "finish_reason": item["finish_reason"],
                        }]
                    }

                    if item.get("usage"):
                        chunk["usage"] = item["usage"]

                    yield f"data: {json.dumps(chunk)}\n\n"

                yield "data: [DONE]\n\n"

            except Exception as exc:
                logger.exception("Claude streaming failed")

                yield f"data: {json.dumps({'error': {'message': str(exc), 'type': 'server_error'}})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        result = await runtime.generate(
            model=request.model, messages=messages, session_id=session_id, **options
        )

    except NotImplementedError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": result["message"],
            "finish_reason": "stop"
        }],
        "usage": result["usage"]
    }

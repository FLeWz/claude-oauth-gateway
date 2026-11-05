from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    # Keep tool_call_id, tool_calls, name, etc. so tool round-trips reach the runtime.
    model_config = ConfigDict(extra="allow")

    role: str
    content: Any


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]

    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    user: Optional[str] = None
    tools: Optional[list[dict]] = None

    tool_choice: Optional[Any] = None
    top_p: Optional[float] = None
    stop: Optional[Any] = None
    stream_options: Optional[dict] = None
    extra_body: Optional[dict] = None
    reasoning_effort: Optional[str] = None
    response_format: Optional[dict] = None


class ModelObject(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "claude"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


import asyncio
from typing import AsyncIterator

from app.runtime.vendor.claude_directsdk.directsdk import Client
from app.runtime.vendor.claude_directsdk.directsdk_setup import (
    setup_status,
    discover_models,
)
from app.runtime.vendor.claude_directsdk.model_catalog import (
    native_model,
    MODEL_METADATA,
)


ALIASES = {
    "claude-sonnet": "sonnet",
    "claude-opus": "opus",
    "claude-haiku": "haiku",
}


def resolve_model(model: str) -> str:
    return native_model(ALIASES.get(model, model))


class ClaudeCodeRuntime:

    def status(self):
        return setup_status()

    def models(self):
        discovered = discover_models()

        if discovered:
            return discovered

        return [
            {"id": model, "label": model, "note": "catalog"}
            for model in MODEL_METADATA
        ]

    async def generate(
        self,
        model,
        messages,
        session_id=None,
        **options,
    ):
        client = Client()

        try:
            result = await asyncio.to_thread(
                client.chat.completions.create,
                model=resolve_model(model),
                messages=messages,
                stream=False,
                **options,
            )

            data = result.model_dump()

            return {
                "message": data["choices"][0]["message"],
                "content": data["choices"][0]["message"].get("content"),
                "usage": data.get("usage", {}),
            }

        finally:
            client.close()

    async def stream(
        self,
        model,
        messages,
        session_id=None,
        **options,
    ) -> AsyncIterator[dict]:

        client = Client()

        try:
            stream = await asyncio.to_thread(
                client.chat.completions.create,
                model=resolve_model(model),
                messages=messages,
                stream=True,
                **options,
            )

            def advance():
                try:
                    return True, next(stream)
                except StopIteration:
                    return False, None

            while True:
                present, chunk = await asyncio.to_thread(advance)

                if not present:
                    break

                data = chunk.model_dump()
                choices = data.get("choices", [])

                if not choices:
                    continue

                choice = choices[0]

                yield {
                    "delta": choice.get("delta", {}),
                    "finish_reason": choice.get("finish_reason"),
                    "usage": data.get("usage"),
                }

        finally:
            if "stream" in locals():
                await asyncio.to_thread(stream.close)

            await asyncio.to_thread(client.close)

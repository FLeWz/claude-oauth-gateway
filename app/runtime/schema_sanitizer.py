"""Minimal stand-in for Hermes core's tools.schema_sanitizer, which the vendored SDK imports."""
from typing import Any

_UNION_KEYS = ("anyOf", "oneOf")


def _is_null_branch(item: Any) -> bool:
    return isinstance(item, dict) and item.get("type") == "null"


def strip_nullable_unions(schema: Any, *, keep_nullable_hint: bool = True) -> Any:
    """Collapse anyOf/oneOf nullable unions to the single non-null branch (Anthropic rejects null)."""
    if isinstance(schema, list):
        return [strip_nullable_unions(item, keep_nullable_hint=keep_nullable_hint) for item in schema]
    if not isinstance(schema, dict):
        return schema

    out = {k: strip_nullable_unions(v, keep_nullable_hint=keep_nullable_hint) for k, v in schema.items()}

    for key in _UNION_KEYS:
        variants = out.get(key)
        if not isinstance(variants, list):
            continue
        kept = [v for v in variants if not _is_null_branch(v)]
        if len(kept) == len(variants) or len(kept) != 1 or not isinstance(kept[0], dict):
            continue
        outer = {k: v for k, v in out.items() if k != key}
        replacement = dict(kept[0])
        for meta_key, value in outer.items():
            if meta_key not in replacement and not (meta_key == "default" and "$ref" in replacement):
                replacement[meta_key] = value
        if keep_nullable_hint:
            replacement["nullable"] = True
        out = replacement
        break

    type_value = out.get("type")
    if isinstance(type_value, list) and "null" in type_value:
        rest = [t for t in type_value if t != "null"]
        if len(rest) == 1:
            out["type"] = rest[0]
            if keep_nullable_hint:
                out["nullable"] = True

    return out

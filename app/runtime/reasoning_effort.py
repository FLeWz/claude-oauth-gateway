"""Minimal stand-in for Hermes core's agent.reasoning_effort, which the vendored SDK imports."""


def clamp_effort(effort, allowed):
    """Return effort lowercased if it is one of allowed, else None (unset)."""
    if not isinstance(effort, str):
        return None
    effort = effort.strip().lower()
    return effort if effort in allowed else None

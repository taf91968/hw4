"""Append-only audit trail of agent-loop activity.

Every chat message produces a small set of records in output/audit_trail.json:
run_start → tool_call / tool_result (/ tool_retry) for each tool → run_end
(with stop reason, model requests and token usage).

Format: JSON Lines, one JSON object per line. Records are only ever appended
(the file is opened in "a" mode and never truncated), so the log survives
backend restarts and is never wiped between runs. Each line can be parsed on
its own:  [json.loads(line) for line in open("output/audit_trail.json")]

Privacy: messages and arguments are shortened, and card numbers and email
addresses are masked before anything is written. The shopper is recorded by
user id only ("guest" for guests).
"""

import functools
import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(
    os.getenv("CC_AUDIT_PATH") or Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
)
PREVIEW_CHARS = 160  # max length of any message / args / result preview

_lock = threading.Lock()  # chat requests can overlap; keep each line whole

# 13–19 digits, optionally separated by spaces or dashes: payment card numbers.
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def redact_card_numbers(text: str) -> str:
    """Replace anything that looks like a payment card number."""
    return CARD_RE.sub("[card number removed]", text)


def _mask(text: str) -> str:
    return EMAIL_RE.sub("[email]", redact_card_numbers(text))


def short(value: Any, limit: int = PREVIEW_CHARS) -> str:
    """Compact, masked, length-capped preview of any value."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = _mask(" ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def log(event: str, run_id: str | None = None, **fields: Any) -> None:
    """Append one record. Never raises: auditing must not break a chat."""
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "event": event,
        "run_id": run_id,
        **fields,
    }
    line = json.dumps(record, ensure_ascii=False, default=str)
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _lock, AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ---------- Tool wrapper ----------

def _summarize(result: Any) -> str:
    """One-line description of a tool result for the audit trail."""
    data = result.model_dump() if hasattr(result, "model_dump") else result
    if isinstance(data, dict):
        bits = []
        for key in ("match", "total_found", "size", "quantity", "status", "logged_in", "page_type"):
            if data.get(key) is not None:
                bits.append(f"{key}={data[key]}")
        for key in ("products", "items", "categories", "results_on_page"):
            if isinstance(data.get(key), list):
                names = [p.get("name") or p.get("garment_type") for p in data[key][:3] if isinstance(p, dict)]
                bits.append(f"{key}={len(data[key])} {names}")
        if "name" in data and "price" in data:
            bits.append(f"{data['name']} ${data['price']}")
        if bits:
            return short("; ".join(bits))
    return short(data)


def audited(tool):
    """Decorate an agent tool so every call, result and retry is appended to the trail.

    functools.wraps keeps the name, docstring and signature, so PydanticAI
    builds the same tool schema as for the undecorated function.
    """

    @functools.wraps(tool)
    def wrapper(ctx, *args, **kwargs):
        run_id = getattr(ctx.deps, "run_id", None)
        call_args = {**{f"arg{i}": a for i, a in enumerate(args)}, **kwargs}
        log("tool_call", run_id, tool=tool.__name__, args=short(call_args))
        started = time.perf_counter()
        try:
            result = tool(ctx, *args, **kwargs)
        except Exception as exc:  # includes ModelRetry
            log(
                "tool_retry" if type(exc).__name__ == "ModelRetry" else "tool_error",
                run_id,
                tool=tool.__name__,
                error=short(str(exc)),
                ms=round((time.perf_counter() - started) * 1000),
            )
            raise
        log(
            "tool_result",
            run_id,
            tool=tool.__name__,
            result=_summarize(result),
            ms=round((time.perf_counter() - started) * 1000),
        )
        return result

    return wrapper

"""Campus Customs shopping agent: PydanticAI wiring.

How the agent is loaded:
- System prompt: read from `prompts/prompt.md` (next to this file).
- Model: `OPENAI_MODEL` (default gpt-5.6-luna) through Portkey's OpenAI-compatible
  API, using `PORTKEY_API_KEY` from the environment or a local `.env`.
- Tools: `tools.TOOLS`; structured output: `models.AgentReply`.

The agent is built once, on the first chat message, and reused after that.
`main.py` calls `run_chat()` for every message from the website.
"""

import os
import time
from functools import lru_cache
from pathlib import Path

from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import audit
import db
from models import (
    MAX_PAGE_RESULTS,
    AgentReply,
    ChatResponse,
    ChatTurn,
    GuestTurn,
    PageContext,
    PageResults,
    ProductCard,
    ProductDetail,
    ProductSummary,
    PublicUser,
)
from tools import TOOLS, LastSearch, ShopDeps

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
DEFAULT_MODEL = "gpt-5.6-luna"

# Max model calls per chat message (each tool round trip is one call), so a
# confused agent can't loop and run up cost.
REQUEST_LIMIT = 6
# Earlier messages sent to the model as context.
HISTORY_TURNS = 12


FILTERED_REPLY = (
    "Sorry, I can't help with that. I'm here to help you find Campus Customs gear — "
    "want me to look for a hoodie, crewneck, tee or quarter-zip?"
)


class AgentNotConfigured(RuntimeError):
    """PORTKEY_API_KEY is missing, so the agent can't call the model."""


def _is_content_filter(err: ModelHTTPError) -> bool:
    text = str(err.body).lower()
    return err.status_code == 400 and ("content_filter" in text or "content management policy" in text)


def model_name() -> str:
    return os.getenv("OPENAI_MODEL") or DEFAULT_MODEL


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, AgentReply]:
    """Build the agent once: prompt file + Portkey model + tools."""
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise AgentNotConfigured("PORTKEY_API_KEY is not set.")
    model = OpenAIChatModel(
        model_name(), provider=OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=key)
    )
    agent = Agent(
        model,
        deps_type=ShopDeps,
        output_type=AgentReply,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=TOOLS,
        retries=2,
        name="campus_customs_shop_assistant",
    )

    @agent.instructions
    def shopper_context(ctx: RunContext[ShopDeps]) -> str:
        return conversation_context(ctx.deps)

    return agent


def _product_line(p: ProductDetail, position: int | None = None) -> str:
    prefix = f"{position}. " if position is not None else ""
    return f"{prefix}**{p.name}** (product_id `{p.product_id}`, ${p.price:.0f}, colors: {', '.join(p.colors)})"


def conversation_context(deps: ShopDeps) -> str:
    """Per-message facts added to the system prompt: who is chatting and what's on their screen.

    Built from ShopDeps for every message. The same facts are available
    through the get_shopper and get_current_page tools.
    """
    lines = ["## This conversation", "", "**Shopper**"]
    user = deps.user
    if user:
        lines.append(
            f"- Logged in as {user.first_name} {user.last_name} ({user.email}). "
            "Their chat history is saved and loaded above."
        )
    else:
        lines.append("- A guest (not logged in). You don't know their name or email.")

    page = deps.page
    lines += ["", "**Their screen right now**", f"- Page: `{page.path}` ({page.page_type})"]
    if page.product_id:
        p = db.get_product(page.product_id)
        if p:
            lines.append(
                "- They have this product page open. \"This\", \"it\" or \"this one\" most likely "
                "means it: " + _product_line(p)
            )
    if page.results_product_ids:
        lines.append(f"- Chat results panel on the page, \"{page.results_title or 'Results'}\", in order:")
        lines += [
            "  " + _product_line(p, i)
            for i, p in enumerate(db.get_products(page.results_product_ids[:12]), start=1)
        ]
        if len(page.results_product_ids) > 12:
            lines.append(f"  … {len(page.results_product_ids) - 12} more (call get_current_page for all)")
    if deps.products_on_screen:
        lines.append("- Product cards under your last chat reply, in order:")
        lines += ["  " + _product_line(p, i) for i, p in enumerate(db.get_products(deps.products_on_screen), start=1)]
    return "\n".join(lines)


def _to_model_history(turns: list[ChatTurn]) -> list[ModelMessage]:
    """Saved chat turns → PydanticAI message history.

    Assistant turns note which product cards were shown, so the agent can
    resolve follow-ups like "do you have this in pink?".
    """
    messages: list[ModelMessage] = []
    for t in turns[-HISTORY_TURNS:]:
        if t.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=t.content)]))
        else:
            text = t.content
            if t.products:
                text += "\n\n[Product cards shown: " + ", ".join(p.product_id for p in t.products) + "]"
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    # The model expects the history to start with a user message.
    while messages and isinstance(messages[0], ModelResponse):
        messages.pop(0)
    return messages


def guest_turns(history: list[GuestTurn]) -> list[ChatTurn]:
    """Browser-sent history for guests → ChatTurns, with cards rebuilt from the database."""
    return [
        ChatTurn(
            role=t.role,
            content=t.content,
            products=[ProductCard.model_validate(p.model_dump()) for p in db.get_products(t.product_ids)],
        )
        for t in history
    ]


async def run_chat(
    message: str,
    user: PublicUser | None,
    history: list[ChatTurn],
    page: PageContext | None = None,
) -> tuple[ChatResponse, list[ProductDetail]]:
    """Answer one chat message.

    Returns the response for the website and the full product objects shown
    (for saving to chat_messages.products_json).
    """
    last_cards = next((t.products for t in reversed(history) if t.role == "assistant"), [])
    deps = ShopDeps(
        run_id=audit.new_run_id(),
        user=user,
        page=page or PageContext(),
        products_on_screen=[p.product_id for p in last_cards],
    )
    current_product_id = deps.current_product_id
    model_history = _to_model_history(history)
    audit.log(
        "run_start",
        deps.run_id,
        shopper=f"user:{user.id}" if user else "guest",
        message=audit.short(message),
        page=deps.page.path,
        history_messages=len(model_history),
        model=model_name(),
        request_limit=REQUEST_LIMIT,
    )
    started = time.perf_counter()

    def end(stop_reason: str, **fields) -> None:
        audit.log(
            "run_end",
            deps.run_id,
            stop_reason=stop_reason,
            ms=round((time.perf_counter() - started) * 1000),
            **fields,
        )

    try:
        result = await get_agent().run(
            message,
            deps=deps,
            message_history=model_history,
            usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
        )
    except ModelHTTPError as err:
        if not _is_content_filter(err):
            end("model_error", error=audit.short(f"HTTP {err.status_code}"))
            raise
        # The model provider's safety filter blocked the message (e.g. a
        # jailbreak attempt). Answer politely instead of showing an error.
        end("content_filter")
        return ChatResponse(reply=FILTERED_REPLY, products=[]), []
    except UsageLimitExceeded as err:
        end("request_limit", error=audit.short(str(err)))
        raise
    except AgentNotConfigured:
        end("not_configured")
        raise
    except Exception as err:
        end("error", error=audit.short(f"{type(err).__name__}: {err}"))
        raise
    out: AgentReply = result.output

    # Only show cards for real products the agent actually looked up (or that
    # were already on screen), so it can't attach made-up or unrelated IDs.
    allowed = deps.seen_product_ids | set(deps.products_on_screen) | set(deps.page.results_product_ids)
    if current_product_id:
        allowed.add(current_product_id)
    card_ids = [pid for pid in out.product_ids if pid in allowed]
    if not card_ids and deps.last_similar_ids:
        # The agent offered alternatives but forgot to attach them: show the
        # find_similar results as cards so the shopper can click through.
        card_ids = deps.last_similar_ids
    shown = db.get_products(card_ids)
    cards = [ProductCard.model_validate(p.model_dump()) for p in shown]
    response = ChatResponse(
        reply=out.reply.strip(),
        products=cards,
        page_results=_page_results(out.page_title, deps.last_search),
    )
    usage = result.usage() if callable(result.usage) else result.usage  # method in v1, property in v2
    end(
        "final_result",
        model_requests=getattr(usage, "requests", None),
        tool_calls=getattr(usage, "tool_calls", None),
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        reply=audit.short(response.reply),
        cards=[p.product_id for p in cards],
        page_results=(
            f"{response.page_results.title}: {len(response.page_results.products)}/{response.page_results.total_found}"
            if response.page_results
            else None
        ),
    )
    return response, shown


def _page_results(title: str | None, search: LastSearch | None) -> PageResults | None:
    """Turn the agent's last catalogue search into product cards for the page.

    Only when the agent set page_title (the shopper is browsing a type of item)
    and the search found something. The cards come straight from the search
    results in the database, not from the model's text.
    """
    if not title or not title.strip() or search is None or not search.ranked_ids:
        return None
    products = db.get_products(search.ranked_ids[:MAX_PAGE_RESULTS])
    return PageResults(
        title=title.strip(),
        query=search.query,
        total_found=len(search.ranked_ids),
        products=[ProductSummary.model_validate(p.model_dump()) for p in products],
    )

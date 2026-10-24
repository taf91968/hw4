"""Campus Customs FastAPI backend — the file Uvicorn runs.

Problem 3: serves the product catalogue and product photos to the React frontend.
Problem 4: create account, log in, log out, and "who am I" with a session cookie.
Problem 5: chat route backed by the PydanticAI shopping agent (agent.py).

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import logging
import time
from collections import defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing modules that read settings at import time
# (auth reads SESSION_SECRET). Variables already set in the environment win.
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / ".env")

from fastapi import Cookie, FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

import agent  # noqa: E402
import audit  # noqa: E402
import auth  # noqa: E402
import db  # noqa: E402
from models import (  # noqa: E402
    ChatRequest,
    ChatResponse,
    ChatTurn,
    LoginRequest,
    ProductDetail,
    ProductSummary,
    PublicUser,
    SignupRequest,
)

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")

# The Vite dev server proxies /api and /media to this app, so CORS is only a
# fallback for calling the API straight from the browser during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Serve only the product photos folder. Mounting all of data/ would expose the
# database file (including password hashes) to anyone who guessed its URL.
app.mount("/media/products", StaticFiles(directory=db.PRODUCTS_DIR), name="product-images")


@app.exception_handler(auth.AuthError)
def auth_error(_request, exc: auth.AuthError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------- Products ----------

@app.get("/api/products", response_model=list[ProductSummary])
def products() -> list[ProductSummary]:
    """Every product in the catalogue, for the Products page."""
    return db.list_products()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def product(product_id: str) -> ProductDetail:
    """One product with stock by size, for the single-item page."""
    item = db.get_product(product_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return item


# ---------- Accounts ----------

def _start_session(response: Response, user: PublicUser) -> None:
    response.set_cookie(
        auth.SESSION_COOKIE,
        auth.make_session_token(user.id),
        max_age=auth.SESSION_SECONDS,
        httponly=True,  # page scripts can't read it
        samesite="lax",  # not sent on cross-site form posts
        secure=False,  # local development is plain http; set True behind https
        path="/",
    )


def current_user(session: str | None) -> PublicUser | None:
    """The logged-in user for a session cookie, or None."""
    user_id = auth.read_session_token(session)
    return auth.get_user(user_id) if user_id is not None else None


@app.post("/api/auth/signup", response_model=PublicUser, status_code=201)
def signup(body: SignupRequest, response: Response) -> PublicUser:
    user = auth.create_user(body.first_name, body.last_name, body.email, body.password)
    _start_session(response, user)
    return user


@app.post("/api/auth/login", response_model=PublicUser)
def login(body: LoginRequest, response: Response) -> PublicUser:
    user = auth.authenticate(body.email, body.password)
    _start_session(response, user)
    return user


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(auth.SESSION_COOKIE, path="/")


@app.get("/api/auth/me", response_model=PublicUser)
def me(cc_session: str | None = Cookie(default=None)) -> PublicUser:
    user = current_user(cc_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


# ---------- Chat ----------

@app.get("/api/chat/history", response_model=list[ChatTurn])
def chat_history(cc_session: str | None = Cookie(default=None)) -> list[ChatTurn]:
    """Saved chat for the logged-in shopper (empty for guests)."""
    user = current_user(cc_session)
    return db.load_chat(user.id) if user else []


# Chat rate limit: at most this many messages per shopper (or per browser IP
# for guests) per window, so one client can't run up model costs.
CHAT_LIMIT = 20
CHAT_WINDOW = 5 * 60
_chat_times: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(key: str) -> bool:
    now = time.time()
    times = _chat_times[key]
    while times and times[0] < now - CHAT_WINDOW:
        times.popleft()
    if len(times) >= CHAT_LIMIT:
        return True
    times.append(now)
    return False


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)
) -> ChatResponse:
    """A message from the website's chat widget → the agent's reply + product cards.

    Logged-in shoppers: history comes from, and is saved to, `chat_messages`,
    and the agent is told who they are (name, email).
    Guests: the browser sends recent history, and nothing is saved.
    `page` says what the browser is showing (product page, results panel).
    """
    # Never let a card number reach the model, the database or the audit trail.
    message = audit.redact_card_numbers(body.message.strip())
    if not message:
        raise HTTPException(status_code=422, detail="Message is empty.")
    user = current_user(cc_session)
    key = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    if _rate_limited(key):
        audit.log("rate_limited", None, shopper=key if user else "guest", limit=f"{CHAT_LIMIT} per {CHAT_WINDOW}s")
        raise HTTPException(
            status_code=429,
            detail="You're sending messages very quickly. Please wait a minute and try again.",
        )
    history = db.load_chat(user.id) if user else agent.guest_turns(body.history)
    page = body.page
    if body.current_product_id and not page.product_id:  # older clients
        page = page.model_copy(update={"product_id": body.current_product_id, "page_type": "product"})

    try:
        response, shown = await agent.run_chat(message, user, history, page)
    except agent.AgentNotConfigured:
        raise HTTPException(
            status_code=503,
            detail="The shopping assistant isn't set up yet (missing AI model API key).",
        )
    except Exception:
        # Log the details on the server; never send model or key errors to the browser.
        log.exception("Agent run failed")
        raise HTTPException(
            status_code=502,
            detail="Sorry, the shopping assistant is having trouble right now. Please try again.",
        )

    if user:
        db.save_chat_turn(user.id, message, response.reply, shown)
    return response

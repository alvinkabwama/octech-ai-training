# Week 2: A chatbot with memory, streaming and an API

Last week every call stood alone. This week you turn single calls into a **chatbot**: it
remembers the conversation, shows its answer as it's written, and sits behind an HTTP API
that any app (a web page, the mini-EDRMS, a mobile app) can call.

**Released:** Fri 20 Nov 2026 · **PR due:** Thu 26 Nov 2026 · **Assessed:** Fri 27 Nov 2026

## What you'll learn

- Why the model forgets, and how a chatbot "remembers" by resending the history.
- Why the history must be **trimmed**: cost, the context window and your 50 requests a day.
- How **sessions** keep each person's conversation separate.
- What **streaming** is and why chat apps use it.
- FastAPI basics: request and response models, status codes, a streaming response.
- Limits and safety: message length, never logging what users type, a polite fallback.

## Concepts

### The model forgets; memory is resending the history

The model keeps nothing between calls (week 1). A chatbot "remembers" only because **your
code** keeps the conversation and sends all of it every turn:

```
turn 1 sends: [system, user "I'm Amina"]
turn 2 sends: [system, user "I'm Amina", assistant "Hi Amina!", user "What's my name?"]
```

On turn 2 the model can answer "Amina" because it can see turn 1 in the messages, not
because it remembered anything.

### The history grows, so trim it

Every turn adds two messages, and all of them are sent every time. Left alone, that causes
three problems:

- **Cost and speed:** you pay for, and wait on, every token you send, on every turn.
- **Context window:** each model accepts only so many tokens. A long chat eventually fails.
- **Free tier:** your 50 requests a day go further when each one is small and quick.

The simple fix: always keep the **system prompt**, plus only the **last N turns** (we use
N = 6). A turn is one user message plus the reply to it. Cut at the start of a turn, so the
kept history never begins with a reply to a question that's no longer there.

```
before: [system, u1, a1, u2, a2, ... u9, a9, u10]
after (N=3): [system, u8, a8, u9, a9, u10]
```

Trimming forgets old details. The stretch task replaces dropped turns with a short summary.

### Sessions

Many people talk to the bot at once, so each conversation gets a **session id**: a random,
unguessable string. The server keeps `session_id -> messages` and the client sends the id
back with every message. This week the store is a Python dict, so it's lost on restart.
Real systems keep it in a database.

### Streaming

Without streaming, the user stares at a blank box until the whole answer is ready. With
`stream=True` the model sends the reply in small pieces as it writes them, so text starts
appearing within a second. The total time is the same; it just *feels* much faster.

```python
for piece in llm.chat_stream(messages):
    print(piece, end="", flush=True)
```

Two catches:

- You only have the full reply **after** the stream ends. Save the turn then.
- Once a piece has been shown, you can't quietly retry. The helper only retries a
  rate-limit (429) that happens **before** the first piece arrives.

### FastAPI in five minutes

FastAPI turns Python functions into HTTP endpoints. Pydantic models describe the body:

```python
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # unknown fields -> 422
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse: ...
```

FastAPI validates the body for you: a wrong type, a missing field or a too-long message
becomes a **422** before your code runs. Your code raises `HTTPException(status_code=404)`
for an unknown session. For streaming, return
`StreamingResponse(pieces, media_type="text/plain")`.

Use plain `def` for routes that call `llm.chat`: it blocks while it waits for the model, and
FastAPI runs plain `def` routes in a thread pool, so one slow reply doesn't freeze the server.

### Limits and safety

- **Cap the message length** (2,000 characters) and reject empty or spaces-only messages.
  They waste requests.
- **Never log or print what users type.** People paste phone numbers, IDs and complaints
  into chatbots. Logs are copied, kept and read by many people.
- **Fail politely.** If the model call fails (rate limit, empty reply), answer
  "Sorry, I couldn't answer that just now…" instead of crashing, and **don't save** the
  failed turn, so the history stays consistent and the user can just ask again.

## Code walkthrough

### The chatbot module

`starter/chatbot.py` holds all the logic. The API only calls it:

```python
session = new_session()  # SESSIONS[session] = [system message]
reply(session, "I'm Amina.")  # history + new message -> trim -> llm.chat -> save
for piece in reply_stream(session, "Who am I?"):
    print(piece, end="")  # llm.chat_stream; saves the full reply at the end
```

One turn of `reply()`:

```python
messages = trim_history([*SESSIONS[session_id], {"role": "user", "content": text}])
answer = llm.chat(messages)
SESSIONS[session_id] = trim_history([*messages, {"role": "assistant", "content": answer}])
```

`[*old, new]` builds a **new** list rather than changing the old one in place. That's safer
when other code still holds the old list.

### Check first, then stream

A function containing `yield` runs **nothing** until someone loops over it. If
`reply_stream()` were a plain generator, a bad session id would only blow up after the API
had already answered `200 OK` and started the stream. So do the checks first, then return
an inner generator:

```python
def reply_stream(session_id, text):
    # Your checks run NOW: they raise ValueError / UnknownSessionError straight away.
    messages = check_and_build(session_id, text)

    def pieces():
        # Lazy part: yield from llm.chat_stream(messages), then save the turn.
        ...

    return pieces()
```

### Running and calling the API

```bash
.venv/bin/python -m uvicorn api:app --app-dir exercises/week-2-chatbot/starter --reload
# PowerShell: .venv\Scripts\python -m uvicorn api:app --app-dir exercises\week-2-chatbot\starter --reload
```

Open <http://127.0.0.1:8000/docs> to try it in the browser, or use curl (on Windows
PowerShell, type `curl.exe`, not `curl`):

```bash
curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "Hi, I am Amina."}'
# {"session_id":"3f2a...","reply":"Hi Amina! How can I help?"}

curl -s -N -X POST http://127.0.0.1:8000/chat/stream -H "Content-Type: application/json" \
  -d '{"session_id": "3f2a...", "message": "What is my name?"}'
# Your name is Amina.          <- arrives piece by piece (-N turns off curl's buffering)
```

### How the tests fake streaming

`fake_llm.queue_stream(["Your file ", "is in ", "Registry."])` makes the next streamed
call return those pieces. The API tests use FastAPI's `TestClient`, which calls your app
in-process, so no server is started and no model is called.

## Assignment (homework)

On `trainee/<your-name>-week-2`, complete `exercises/week-2-chatbot/starter/`:

1. **`chatbot.py`**:
   - `SYSTEM_PROMPT`: the system prompt for "Octech Help".
   - `new_session()` and `end_session()`.
   - `trim_history(messages, max_turns=6)`.
   - `reply(session_id, text)`.
   - `reply_stream(session_id, text)`, which saves the full reply when the stream ends.
   - Raise `ValueError` for an empty message or one over 2,000 characters, and
     `UnknownSessionError` (a `KeyError`) for an unknown session.
2. **`api.py`**:
   - `POST /chat` with `{session_id?, message}` returns `{session_id, reply}`.
   - `POST /chat/stream` returns plain text, with an `X-Session-Id` header.
   - `DELETE /chat/{session_id}` returns 204.
   - Unknown session: 404. Bad body: 422. Unknown fields are rejected.

Then:

```bash
make check WEEK=2      # PowerShell: .venv\Scripts\python scripts\run_week.py check 2
make ci                # lint + format + main test suite
make live WEEK=2       # PowerShell: .venv\Scripts\python scripts\run_week.py live 2
```

`make live WEEK=2` runs a 3-turn conversation (3 requests). Turn 3 asks the bot your name,
which it only knows if your memory works. Then start the API and call both endpoints with
curl. Use only made-up names and numbers.

## Show your work (checkpoint)

Copy this list into your PR description and tick each item:

- [ ] PR base is `trainee/<my-name>`, compare is `trainee/<my-name>-week-2`
- [ ] `make check WEEK=2` passes (paste the last line)
- [ ] `make ci` is clean
- [ ] `make live WEEK=2` transcript pasted in the PR (all 3 turns; turn 3 shows the bot remembered)
- [ ] curl output pasted for `POST /chat` and `POST /chat/stream`
- [ ] In one sentence: why does the chatbot resend the history every turn?
- [ ] In one sentence: what breaks if you never trim the history?
- [ ] In one sentence: why stream the reply instead of waiting for all of it?

## Stretch

Pick one:

- **Summarise instead of dropping.** When a turn is trimmed, ask the model for a one-line
  summary of the dropped turns and keep it as a second system message ("Earlier: Amina
  works in registry…"). Note that this costs an extra request.
- **A tiny chat page.** One HTML file whose JavaScript posts to `/chat/stream` and appends
  each piece to the page as it arrives (`fetch` + `response.body.getReader()`). Serve it
  with FastAPI's `HTMLResponse`.

## How the real chatbot does this

> The production chatbot keeps each session (history, counters, flags) as a document in a
> **Cosmos DB** container keyed by `session_id`, so any server instance can pick up the next
> turn and a restart loses nothing. The history is **bounded** (ADR 0062): every saved turn
> trims it to the most recent entries, because only the tail is ever read. Replies **stream**
> from the model through the services to the browser as Server-Sent Events (learning module
> 14), except short pre-written answers, which arrive in one piece. A separate, long-term
> **transcript** of each turn is stored for audit, and personal data (phone numbers, emails,
> account numbers, one-time codes) is **removed from transcripts before they're saved**
> (ADR 0019). The live session stays complete so a human agent who takes over can read it.

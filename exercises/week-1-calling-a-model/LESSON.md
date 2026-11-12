# Week 1: Calling a model

You'll learn what actually happens when code "talks to an AI", and write three small
functions that use a model to explain, classify and extract. These three patterns
are most of what "adding AI to an app" means in practice.

## What you'll learn

- What a model call is: a request with messages in, text out.
- The three message roles (`system`, `user`, `assistant`) and what each one is for.
- What `temperature` and `max_tokens` change.
- Why the model has no memory, and what that means for chatbots.
- How free-tier limits and fallback models affect your code.
- Why you must **validate** everything a model returns.
- The difference between a model call, a chatbot and an agent, and why the production
  chatbot is a fixed pipeline of steps rather than one big prompt.

## Concepts

### A model call is just an HTTP request

You send a list of **messages** to a **model**; it sends back text. That's all.
OpenRouter uses the same format as OpenAI, so we use the `openai` Python SDK pointed
at OpenRouter's URL:

```
POST https://openrouter.ai/api/v1/chat/completions
{
  "model": "openrouter/free",
  "messages": [
    {"role": "system", "content": "Answer in 3 sentences or fewer."},
    {"role": "user",   "content": "What is a file plan?"}
  ],
  "temperature": 0.3
}
```

The reply text is at `choices[0].message.content`.

### Roles

| Role | Who writes it | Use it for |
|---|---|---|
| `system` | You, the developer | Rules: persona, tone, length, output format, what to refuse |
| `user` | The person (or your code on their behalf) | The question or the text to work on |
| `assistant` | The model | Its earlier replies, when you send a conversation back |

The system prompt is your main control. "Answer in 3 sentences or fewer" there works
far better than hoping the model keeps it short.

### Temperature and max_tokens

- **`temperature`** controls randomness. Use `0` when you want the same answer every
  time (classifying, extracting). Use `0.7` or more for creative text.
- **`max_tokens`** caps the reply length (a token is roughly ¾ of a word). It cuts the
  reply off; it doesn't make the model write concisely. Use the system prompt for that.

### The model has no memory

Every call is independent. The model doesn't remember your last request. A chatbot
"remembers" only because your code keeps the list of messages and sends the **whole**
list every turn. You'll build that in week 2.

### Free tier: limits and fallbacks

Free models allow **20 requests/minute and 50/day** per account, get slow at busy
times, and can disappear without notice. So the shared helper:

- sends a **fallback list** of free models; OpenRouter tries them in order;
- **waits and retries** (5s, then 10s) when it gets HTTP 429 "rate limited";
- gives up after 3 tries with a message explaining the limit.

`make check` never calls a model. Only `make live` uses your free requests.

### Never trust the output

A model is a text generator, not a function with a contract. Ask for `loan_enquiry`
and you may get `Loan_Enquiry.`, `"loan_enquiry"`, or "This is a loan enquiry". Ask
for JSON and you may get JSON wrapped in ```` ```json ```` fences, or a polite sentence
first. Your code must:

1. **Normalise** (strip spaces, quotes and full stops; lower-case).
2. **Check against an allowed list**, and fall back to a safe default (`"other"`).
3. **Parse in a try**, retry once with a clear reminder, then fail loudly (`ValueError`).

This is the most important habit in the whole programme.

### Model call vs chatbot vs agent

- **Model call:** one request, one reply. Stateless, no tools, can't look anything up.
  This week.
- **Chatbot:** a loop around model calls that keeps the conversation history. Week 2.
- **Agent:** a model call given a job, rules and **tools** (functions it can ask your
  code to run), which decides which tool to use next. Weeks 5 and 6.

One giant "do everything" prompt doesn't scale. Real systems split the work into
small, specialised steps. The production chatbot handles each customer message with
a **fixed pipeline of five steps**, always in the same order:

```
message -> 1. detect language -> 2. classify intent -> 3. retrieve knowledge
        -> 4. rerank what was found -> 5. write the reply -> answer
```

Each step is a small model call (or search) with one job, like your `classify()`.
Splitting it up has three benefits:

1. **Specialisation:** a small, cheap model is good at classifying; a bigger one writes
   better replies. Each step uses the model that suits it.
2. **Debugging:** when an answer is wrong you can see which step went wrong.
3. **Cost:** cheap steps run on every message; expensive ones only when needed.

A **pipeline** like this is a fixed workflow: *your code* decides the order. An **agent**
decides its own next step. Most features should start as a pipeline. Week 6 covers when
an agent is worth it.

## Code walkthrough

### The shared helper

`exercises/common/llm.py` hides the setup. Two functions matter:

```python
from exercises.common import llm

# One system prompt + one question:
reply = llm.ask("What is a file plan?", system="Answer in one sentence.", temperature=0)

# Full control over the message list:
reply = llm.chat(
    [
        {"role": "system", "content": "Answer in 3 sentences or fewer."},
        {"role": "user", "content": "What is a file plan?"},
    ],
    temperature=0.3,
    max_tokens=200,
)
```

Inside, `chat()` does roughly this (simplified):

```python
models = ["openrouter/free", "google/gemma-4-31b-it:free", "nvidia/nemotron-3.5-lightning:free"]
response = client.chat.completions.create(
    model=models[0],
    messages=messages,
    temperature=temperature,
    extra_body={"models": models},  # OpenRouter's fallback list
)
return response.choices[0].message.content
```

### Pattern 1: explain (system prompt controls tone and length)

```python
SYSTEM = "You are a patient teacher. Use plain words and answer in 3 sentences or fewer."
llm.ask("Explain a retention schedule to a new registry assistant.", system=SYSTEM)
```

### Pattern 2: classify (temperature 0 + validate against a list)

```python
reply = llm.ask(message, system=f"Reply with one of: {', '.join(CATEGORIES)}.", temperature=0)
label = reply.strip().strip("\"'.").lower()
return label if label in CATEGORIES else "other"
```

### Pattern 3: extract (JSON + parse + retry once)

```python
import json

raw = llm.chat(messages, temperature=0)
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    # Show the model its bad reply and ask again, once.
    messages += [
        {"role": "assistant", "content": raw},
        {"role": "user", "content": "Reply with the JSON object only."},
    ]
    data = json.loads(llm.chat(messages, temperature=0))  # raises if still bad
```

Remember that `json.JSONDecodeError` is a subclass of `ValueError`.

### How the tests fake the model

The tests never call OpenRouter. The `fake_llm` fixture swaps in a scripted model:

```python
def test_classify_normalises_reply(prompts, fake_llm):
    fake_llm.queue("Loan_Enquiry.")  # what the "model" will reply
    assert prompts.classify("I want a loan") == "loan_enquiry"
    assert fake_llm.calls[0]["temperature"] == 0  # what your code sent
```

So the tests check **your code's** behaviour (what it sends, how it handles replies),
not the model's mood that day.

## Assignment (homework)

On `trainee/<your-name>-week-1`, complete `exercises/week-1-calling-a-model/starter/prompts.py`:

1. **`explain(topic, audience) -> str`**: a system prompt that sets the tone and says
   "3 sentences or fewer"; the topic and audience go in the user message.
2. **`classify(message) -> str`**: returns exactly one of
   `("card_issue", "loan_enquiry", "mobile_banking", "complaint", "other")`. Use
   temperature 0, normalise the reply, and map anything unexpected to `"other"`.
3. **`extract(text) -> dict`**: returns
   `{"name": str | None, "phone": str | None, "issue": str, "urgency": "low" | "medium" | "high"}`.
   Strip ```` ```json ```` fences, keep only those four keys, check the urgency, retry once
   with a "reply with JSON only" reminder, then raise `ValueError`.

Then:

```bash
make check WEEK=1      # PowerShell: .venv\Scripts\python scripts\run_week.py check 1
make ci                # lint + format + main test suite
make live WEEK=1       # PowerShell: .venv\Scripts\python scripts\run_week.py live 1
```

Use only made-up names and numbers in anything you send to a model.

## Show your work (checkpoint)

Copy this list into your PR description and tick each item:

- [ ] PR base is `trainee/<my-name>`, compare is `trainee/<my-name>-week-1`
- [ ] `make check WEEK=1` passes (paste the last line)
- [ ] `make ci` is clean
- [ ] `make live WEEK=1` output pasted in the PR (explain, 3 classifications, 1 extraction)
- [ ] In one sentence: what does the system prompt do that the user message can't?
- [ ] In one sentence: why does `classify()` use temperature 0?
- [ ] In one sentence: why does the production chatbot use a 5-step pipeline instead of one prompt?

## Stretch

Compare 3 free models on the same 5 prompts (for example, 5 customer messages through
`classify()`). That's 15 requests, so watch your daily 50.

For a fair comparison, call one model at a time without fallbacks, so you know who
answered:

```python
import time

from exercises.common.llm import get_client

client = get_client()
messages = [
    {"role": "system", "content": "Reply with one of: card_issue, loan_enquiry, other."},
    {"role": "user", "content": "My card is stuck in the ATM."},
]
for model in [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-3-1.7b:free",
]:
    start = time.perf_counter()
    r = client.chat.completions.create(model=model, messages=messages, temperature=0)
    print(f"{model}: {time.perf_counter() - start:.1f}s -> {r.choices[0].message.content!r}")
```

Put a small table in your PR: model, average seconds, how many of the 5 were right,
and one sentence on which you'd pick for classification and why.

## How the real chatbot does this

> The production chatbot never makes one big call. Each customer message goes through
> the fixed five-step pipeline in its `agent_pipeline_v2` service, and every step reads
> and writes one shared state object, so the trace shows exactly which step produced
> what. Its intent step works like your `classify()`: low temperature, a fixed label
> list, and validation before anything acts on the label. Steps that need quality use a
> stronger model; cheap steps use a small one.

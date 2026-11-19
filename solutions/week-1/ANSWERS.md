# Week 1: model answers and review notes

Code: [prompts.py](prompts.py). Lesson: [LESSON.md](../../exercises/week-1-calling-a-model/LESSON.md).

## Checkpoint answers

**What does the system prompt do that the user message can't?**
It sets the rules the developer controls (role, tone, length, output format) for the whole
conversation, while the user message only carries the thing to work on and can change on
every call.

**Why does `classify()` use temperature 0?**
Temperature 0 makes the model pick its most likely answer every time, so the same message
always gets the same label, which is what you want when choosing from a fixed list.

**Why does the production chatbot use a 5-step pipeline instead of one prompt?**
Fixed code decides the order of the steps, so each small step can be tested, debugged and
given the model that suits it, and you can see exactly which step went wrong. One big
prompt hides all of that inside the model.

## The three patterns at a glance

| Function | Helper | Temperature | What makes it safe |
|---|---|---|---|
| `explain()` | `llm.ask` | default (0.3) | System prompt limits tone and length |
| `classify()` | `llm.ask` | 0 | Reply is cleaned, then checked against `CATEGORIES`; anything else is `"other"` |
| `extract()` | `llm.chat` | 0 | Fences stripped, JSON parsed, every value checked, one retry with the bad reply shown, then `ValueError` |

## Things that came up in week 1 reviews

1. **Cleaning the classify reply in two steps.** `reply.strip("\"'").rstrip(".")` misses
   `"loan_enquiry".` because the quote is still there after the full stop is removed.
   Strip quotes and punctuation in one call: `reply.strip().strip("\"'.")`.
2. **Retrying without the bad reply.** The model has no memory between calls. If the
   retry only adds "reply with JSON only", the model never sees what it got wrong. Add its
   bad reply as an `assistant` message first, then the reminder as a `user` message.
3. **Accepting `"issue": null`.** The lesson says `issue` is always a string. The tests
   don't check this, but your code should: an empty issue is useless to whoever picks up
   the ticket.
4. **Deleting the starter's docstrings.** Keep the module and function docstrings and
   replace only the `TODO` lines. They explain the function to the next reader (and to
   you in week 5, when these functions become tools).
5. **An empty "What I built".** One or two sentences on what you changed and why. It's
   the first thing a reviewer reads.

## "How do these functions hide the POST request we wrote by hand?"

In the lesson you sent an HTTP POST to `https://openrouter.ai/api/v1/chat/completions`
with an `Authorization: Bearer <key>` header and a JSON body of `model` and `messages`.
The helper in [exercises/common/llm.py](../../exercises/common/llm.py) does exactly that,
in three layers:

1. **`llm.ask(prompt, system=...)`** builds the `messages` list for you: a `system`
   message (if given) and one `user` message. Then it calls `llm.chat(messages)`.
2. **`llm.chat(messages)`** calls the OpenAI SDK:
   `get_client().chat.completions.create(model=..., messages=..., temperature=...)`.
   It also adds the list of free fallback models and, if OpenRouter answers
   `429 Too Many Requests`, waits and tries again. It returns only the reply text,
   `response.choices[0].message.content`.
3. **`get_client()`** creates the SDK client once with `base_url` set to OpenRouter and
   your key from `.env`. The SDK turns `create(...)` into the same POST you wrote: same
   URL, same header, same JSON body.

So `llm.ask("Hi")` is your hand-written POST, plus building the messages, fallbacks,
rate-limit retries and pulling the text out of the response.

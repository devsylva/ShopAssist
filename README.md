# ShopAssist — AI Customer Support Agent for Velora

ShopAssist is a production-style AI customer support agent built with Django and Claude. It powers the support chat widget for **Velora**, a fictional ecommerce brand selling home decor, wellness products, and lifestyle accessories.

This project is designed as a realistic MVP that demonstrates how AI agents work in production — including the failure modes, observability challenges, and reliability concerns that come with them.

---

## Features

- **Conversational support chat** — clean, real-time chat UI
- **Knowledge-grounded answers** — agent answers from markdown policy files, never hallucinates
- **Order lookup** — detects order IDs (SA-XXXXX) in messages and queries the database
- **Escalation detection** — flags conversations for human review when issues are complex or sensitive
- **Conversation history** — full session memory stored in SQLite
- **Structured logging** — every request, tool use, source selection, and fallback is logged
- **Admin panel** — browse sessions, messages, and orders at `/admin/`

---

## Architecture

```
Browser
  │  POST /api/chat/  (JSON)
  ▼
agent/views.py          ← request handling, session management
  │
  ▼
agent/services/agent.py ← orchestration (knowledge + order + Claude)
  ├── services/knowledge.py  ← loads markdown files, keyword scoring
  ├── services/orders.py     ← SQLite order lookup
  └── Anthropic API (Claude) ← LLM response generation
  │
  ▼
agent/models.py         ← ChatSession, ChatMessage, Order (SQLite)
```

**Knowledge retrieval** uses simple keyword overlap scoring — no vector DB. Each query scores the 6 markdown files and loads the top 3. `company_info.md` is always included.

**Escalation** is triggered by a hidden `<!-- ESCALATE -->` marker that Claude appends when it detects complex, sensitive, or unresolvable issues.

---

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd shopassist
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Set up the database

```bash
python manage.py migrate
python manage.py seed_orders
```

### 4. Create an admin user (optional)

```bash
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

Open http://localhost:8000 to use the chat.
Open http://localhost:8000/admin/ to browse the data.

---

## Environment Variables

| Variable            | Default               | Description                              |
|---------------------|-----------------------|------------------------------------------|
| `ANTHROPIC_API_KEY` | (required)            | Your Anthropic API key                   |
| `AGENT_MODEL`       | `claude-sonnet-4-6`   | Claude model to use                      |
| `AGENT_MAX_HISTORY` | `20`                  | Max conversation messages sent to Claude |
| `DEBUG`             | `True`                | Django debug mode                        |
| `SECRET_KEY`        | (insecure default)    | Django secret key — change in production |
| `ALLOWED_HOSTS`     | `localhost,127.0.0.1` | Comma-separated allowed hosts            |

---

## Mock Orders

Ten realistic orders are seeded by `python manage.py seed_orders`:

| Order ID  | Customer        | Item                        | Status      | Refund Eligible     |
|-----------|-----------------|-----------------------------|-------------|---------------------|
| SA-10001  | Marcus Williams | Linen Throw Pillow Set      | Delivered   | No (>30 days)       |
| SA-10002  | Sarah Chen      | Aromatherapy Diffuser       | In Transit  | Yes                 |
| SA-10003  | Jordan Taylor   | Bamboo Desk Organizer       | Processing  | Yes                 |
| SA-10004  | Emma Rodriguez  | Weighted Blanket            | Delivered   | Yes                 |
| SA-10005  | David Kim       | Glass Water Bottle Set      | Cancelled   | Refund processing   |
| SA-10006  | Aisha Johnson   | Ceramic Planter Set         | Delivered   | No (>30 days)       |
| SA-10007  | Tyler Brown     | Essential Oil Starter Kit   | Shipped     | Yes                 |
| SA-10008  | Priya Patel     | Minimalist Wall Clock       | Processing  | Yes                 |
| SA-10009  | Connor Walsh    | Velvet Storage Basket       | Processing  | No (payment failed) |
| SA-10010  | Lisa Nakamura   | Scented Candle Collection   | Delivered   | Yes                 |

---

## Logs

Logs are written to:
- **Console** — always, in development
- **`logs/shopassist.log`** — file-based log for all `agent` logger events

Key log events:
- `Incoming message` — user input + session
- `Order ID detected` / `Order lookup hit/miss` — tool usage
- `Knowledge selection` — which files were scored and selected
- `Claude response` — token counts, escalation flag
- `Response ready` — final result summary

---

## Demo Scenarios

Try these in the chat to exercise different code paths:

| Message | What it tests |
|---|---|
| `"What's your return policy?"` | Knowledge retrieval (refund_policy.md) |
| `"Where is order SA-10002?"` | Order lookup + in-transit status |
| `"I want a refund for SA-10001"` | Order found but refund not eligible (>30 days) |
| `"SA-10099 where is my package?"` | Order not found fallback |
| `"I'm really frustrated, this is unacceptable!!!"` | Escalation trigger |
| `"How do I reset my password?"` | Account help knowledge |
| `"What shipping options do you have?"` | Shipping policy knowledge |

---

## Future Production Improvements

- OpenTelemetry tracing on every agent step
- Latency alerting when Claude p95 > 3s
- Rate limiting per session
- Input/output token budget enforcement
- Retry logic with exponential backoff
- Evaluation pipeline for response quality
- Streaming responses (SSE)
- Human handoff queue with ticket creation

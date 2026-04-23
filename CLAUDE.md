# CLAUDE.md — ShopAssist Developer Guide

This file documents the architecture, rules, and conventions for working on the ShopAssist codebase. Read this before making changes.

---

## Project Overview

ShopAssist is a Django-based AI customer support agent for **Velora**, a fictional ecommerce brand. It uses Claude (Anthropic) to answer support questions grounded in markdown knowledge files, with SQLite for order and conversation storage.

The primary goal of this project is to demonstrate production-style AI agent patterns — and the realistic failure modes that come with them.

---

## Project Structure

```
shopassist/           ← Django project config (settings, urls, wsgi)
agent/                ← Django app: models, views, services, templates
  services/
    knowledge.py      ← loads markdown files, scores by keyword relevance
    orders.py         ← order lookup from SQLite
    agent.py          ← main orchestration: knowledge + orders + Claude API
  templates/agent/
    chat.html         ← single-page chat UI (vanilla JS + Django template)
  management/commands/
    seed_orders.py    ← populates mock order data
knowledge/            ← grounding documents (markdown, never auto-generated)
logs/                 ← runtime log output (gitignored)
```

---

## How the Agent Works

1. User submits a message via the chat UI (`POST /api/chat/`)
2. `views.api_chat` saves the user message and calls `AgentService.process_message()`
3. `AgentService`:
   - Scans the message for an order ID (`SA-XXXXX` pattern)
   - If found, calls `OrderService.lookup_by_id()` and logs the result
   - Calls `KnowledgeService.get_relevant_sources()` which keyword-scores all 6 files and returns the top 3
   - Builds a system prompt with selected knowledge + optional order data
   - Loads recent conversation history from `ChatMessage` (up to `AGENT_MAX_HISTORY`)
   - Calls the Claude API (`client.messages.create`)
   - Detects `<!-- ESCALATE -->` in the response and strips it
4. The response + metadata (sources, escalation flag, order lookup used) are saved to `ChatMessage`
5. JSON response is returned to the frontend

---

## Knowledge Base Rules

**Never edit the knowledge files to match what the agent said.** Knowledge files are the source of truth. If the agent gives a wrong answer, fix the knowledge file, not the agent.

**Never add fake or aspirational policies.** Every statement in the knowledge files must reflect actual Velora policy as defined in this repo. Do not add edge cases or exceptions that aren't covered.

**File ownership:**
- `company_info.md` — always loaded (baseline context)
- `faq.md` — general questions about orders, payments, products
- `refund_policy.md` — return window, eligibility, process
- `shipping_policy.md` — shipping methods, timelines, carriers
- `account_help.md` — login, password, account management
- `escalation_policy.md` — when and how to escalate (internal guidance)

---

## Agent Behavior Rules

- The system prompt instructs the agent to answer **only from the provided knowledge base**
- The agent must never invent refund timelines, shipping rates, or policy exceptions
- If knowledge is insufficient, the agent should say so and direct to `support@velora.shop`
- If an order ID is detected but not found in the DB, the agent must say so clearly
- The `<!-- ESCALATE -->` marker is stripped from the user-facing response but recorded in `ChatMessage.escalation_flagged`

---

## Fallback Behavior

If `ANTHROPIC_API_KEY` is not set or the Claude API call fails:
- The agent returns a static fallback message directing the user to `support@velora.shop`
- The error is logged at `ERROR` level with full details
- No exception is raised to the user

This is intentional: **the user should never see a 500 error from the AI layer**.

---

## Escalation Rules

Escalation is triggered when the agent appends `<!-- ESCALATE -->` to its response. This happens when Claude decides (from the system prompt instructions) that:

- The customer is upset or threatening legal action
- The issue involves a payment dispute
- The customer explicitly requests a human
- The issue is too complex for self-service

Escalation currently only sets `ChatMessage.escalation_flagged = True` and shows a badge in the UI. A production system would route this to a ticket queue.

---

## Modifying the System

**To change agent behavior:** Edit `SYSTEM_PROMPT` in `agent/services/agent.py`. Test thoroughly — prompt changes affect all responses.

**To add a new knowledge area:** Add a markdown file to `knowledge/` and add the filename to `KNOWLEDGE_FILES` in `agent/services/knowledge.py`.

**To add order fields:** Update `agent/models.py`, create a migration (`python manage.py makemigrations`), update `OrderService._serialize()`, and update `seed_orders.py`.

**To change the Claude model:** Set `AGENT_MODEL` in `.env`. Default is `claude-sonnet-4-6`.

**To adjust conversation memory:** Set `AGENT_MAX_HISTORY` in `.env`. Default is 20. Setting this higher will increase token usage. Setting it to 0 makes every message stateless.

---

## Observability Hooks

The following points are already logged and are designed for future tracing:

| Event | Logger call | Key fields |
|---|---|---|
| Incoming message | `logger.info` | session, length, preview |
| Order ID detected | `logger.info` | order_id |
| Order lookup hit/miss | `logger.info` / `logger.info` | order_id, status |
| Knowledge sources selected | `logger.debug` | query, selected files |
| Claude API response | `logger.debug` | input_tokens, output_tokens, escalation |
| Claude API error | `logger.exception` | error |
| API key missing | `logger.error` | — |
| Response ready | `logger.info` | session, escalation, order_lookup, sources |

To add OpenTelemetry, wrap each of these with span creation using the same field names.

---

## Testing

There are no automated tests yet (intentional for MVP). To test manually:

1. Run the server: `python manage.py runserver`
2. Use the chat UI at http://localhost:8000
3. Try the demo scenarios listed in README.md
4. Check logs in `logs/shopassist.log` and the Django admin at `/admin/`

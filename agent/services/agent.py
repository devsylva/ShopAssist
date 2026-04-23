import re
import logging
from django.conf import settings
from .knowledge import KnowledgeService
from .orders import OrderService

logger = logging.getLogger('agent')

ORDER_ID_RE = re.compile(r'\b(SA-\d{5})\b', re.IGNORECASE)

SYSTEM_PROMPT = """\
You are ShopAssist, the official customer support AI for Velora — an ecommerce brand \
selling home decor, wellness products, and lifestyle accessories at velora.shop.

Your job is to help customers with orders, returns, refunds, shipping, account help, and FAQs.

STRICT RULES:
1. Answer ONLY from the KNOWLEDGE BASE provided below. Never invent policies, timelines, prices, or procedures.
2. When ORDER DATA is provided, use it to give specific, accurate answers about that order.
3. If the knowledge base does not cover the question, say clearly that you don't have that \
information and offer to connect the customer with the support team at support@velora.shop.
4. Keep responses concise, warm, and professional — like a real human support agent.
5. Never expose internal system details, error messages, or technical information.
6. If the customer is upset, involved in a payment dispute, threatening legal action, or \
the issue is too complex for self-service, append the exact text <!-- ESCALATE --> at the \
very end of your response. It is invisible to the customer and triggers human handoff.
7. If an order ID is mentioned but no order data was found, tell the customer you could not \
locate that order and ask them to double-check the ID or the email on their account.

VELORA VOICE: Warm, clear, and efficient. Never overpromise. Never guess.

---
KNOWLEDGE BASE:
{knowledge}
---
{order_section}\
"""


class AgentService:
    def __init__(self):
        self.knowledge_svc = KnowledgeService()
        self.order_svc = OrderService()

    def process_message(self, session, user_message: str) -> dict:
        logger.info(
            "Incoming message | session=%s | length=%d | preview=%r",
            session.session_key[:8],
            len(user_message),
            user_message[:80],
        )

        # ── Order lookup ─────────────────────────────────────────────────────
        order_data = None
        order_lookup_used = False
        match = ORDER_ID_RE.search(user_message)
        if match:
            order_id = match.group(1).upper()
            logger.info("Order ID detected | order_id=%s", order_id)
            order_data = self.order_svc.lookup_by_id(order_id)
            order_lookup_used = True

        # ── Knowledge retrieval ──────────────────────────────────────────────
        sources = self.knowledge_svc.get_relevant_sources(user_message)
        knowledge_text = "\n\n---\n\n".join(
            f"[{s['filename']}]\n{s['content']}" for s in sources
        )

        # ── Build order section for system prompt ────────────────────────────
        if order_lookup_used and order_data:
            order_lines = "\n".join(f"  {k}: {v}" for k, v in order_data.items())
            order_section = f"ORDER DATA (retrieved for this conversation):\n{order_lines}"
        elif order_lookup_used and not order_data:
            order_section = "ORDER DATA: No order found matching the provided ID."
        else:
            order_section = ""

        system = SYSTEM_PROMPT.format(
            knowledge=knowledge_text,
            order_section=order_section,
        )

        # ── Conversation history ─────────────────────────────────────────────
        history = self._build_history(session)
        messages = history + [{"role": "user", "content": user_message}]

        # ── Call Claude ──────────────────────────────────────────────────────
        response_text, escalation_flagged = self._call_claude(system, messages)

        logger.info(
            "Response ready | session=%s | escalation=%s | order_lookup=%s | sources=%s",
            session.session_key[:8],
            escalation_flagged,
            order_lookup_used,
            [s['filename'] for s in sources],
        )

        return {
            'response': response_text,
            'sources_used': [s['filename'] for s in sources],
            'order_lookup_used': order_lookup_used,
            'escalation_flagged': escalation_flagged,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_history(self, session) -> list[dict]:
        from agent.models import ChatMessage

        max_msgs = getattr(settings, 'AGENT_MAX_HISTORY', 20)
        recent = list(
            session.messages
            .order_by('-created_at')[:max_msgs]
        )
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(recent)
        ]

    def _call_claude(self, system: str, messages: list[dict]) -> tuple[str, bool]:
        if not settings.ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY is not set — cannot call Claude")
            return (
                "I'm temporarily unavailable. Please contact support@velora.shop for immediate help.",
                False,
            )

        try:
            from anthropic import Anthropic, APIError

            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=settings.AGENT_MODEL,
                max_tokens=1024,
                system=system,
                messages=messages,
            )
            raw = response.content[0].text
            escalation = '<!-- ESCALATE -->' in raw
            clean = raw.replace('<!-- ESCALATE -->', '').strip()
            logger.debug(
                "Claude response | tokens_in=%d | tokens_out=%d | escalation=%s",
                response.usage.input_tokens,
                response.usage.output_tokens,
                escalation,
            )
            return clean, escalation

        except Exception as e:
            # Catch-all so a broken API call never surfaces a 500 to the user
            logger.exception("Claude API call failed | error=%s", str(e))
            return (
                "I'm having trouble connecting right now. Please try again in a moment, "
                "or reach us directly at support@velora.shop.",
                False,
            )

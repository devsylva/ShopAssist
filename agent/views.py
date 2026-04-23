import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from agent.models import ChatSession, ChatMessage
from agent.services.agent import AgentService

logger = logging.getLogger('agent')

WELCOME_MESSAGE = (
    "Hi! I'm ShopAssist, Velora's support assistant. "
    "I can help with orders, returns, shipping, and account questions. "
    "How can I help you today?"
)


def chat_view(request):
    if not request.session.session_key:
        request.session.create()

    session, created = ChatSession.objects.get_or_create(
        session_key=request.session.session_key
    )
    if created:
        logger.info("New chat session | session=%s", session.session_key[:8])

    messages = session.messages.order_by('created_at')
    return render(request, 'agent/chat.html', {
        'messages': messages,
        'welcome_message': WELCOME_MESSAGE,
    })


@require_POST
def api_chat(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    user_message = data.get('message', '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)
    if len(user_message) > 2000:
        return JsonResponse({'error': 'Message is too long (max 2000 characters)'}, status=400)

    if not request.session.session_key:
        request.session.create()

    session, _ = ChatSession.objects.get_or_create(
        session_key=request.session.session_key
    )

    ChatMessage.objects.create(session=session, role='user', content=user_message)

    svc = AgentService()
    result = svc.process_message(session, user_message)

    ChatMessage.objects.create(
        session=session,
        role='assistant',
        content=result['response'],
        sources_used=result.get('sources_used', []),
        order_lookup_used=result.get('order_lookup_used', False),
        escalation_flagged=result.get('escalation_flagged', False),
    )

    return JsonResponse({
        'response': result['response'],
        'escalation': result.get('escalation_flagged', False),
    })

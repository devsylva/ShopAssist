from django.contrib import admin
from .models import Order, ChatSession, ChatMessage


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_name', 'email', 'item_name', 'shipping_status', 'payment_status', 'refund_eligible', 'order_date']
    list_filter = ['shipping_status', 'payment_status', 'refund_eligible']
    search_fields = ['order_id', 'customer_name', 'email']


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'created_at', 'sources_used', 'order_lookup_used', 'escalation_flagged']
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'created_at', 'message_count']
    readonly_fields = ['session_key', 'created_at']
    inlines = [ChatMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'short_content', 'order_lookup_used', 'escalation_flagged', 'created_at']
    list_filter = ['role', 'order_lookup_used', 'escalation_flagged']
    readonly_fields = ['session', 'role', 'content', 'created_at', 'sources_used', 'order_lookup_used', 'escalation_flagged']

    def short_content(self, obj):
        return obj.content[:80]
    short_content.short_description = 'Content'

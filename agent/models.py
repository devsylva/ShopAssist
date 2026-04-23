from django.db import models


class Order(models.Model):
    SHIPPING_STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('refund_processing', 'Refund Processing'),
        ('refunded', 'Refunded'),
        ('payment_failed', 'Payment Failed'),
    ]

    order_id = models.CharField(max_length=20, unique=True, db_index=True)
    customer_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    item_name = models.CharField(max_length=200)
    order_date = models.DateField()
    shipping_status = models.CharField(max_length=30, choices=SHIPPING_STATUS_CHOICES)
    delivery_eta = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=50, blank=True)
    refund_eligible = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.order_id} — {self.customer_name}"


class ChatSession(models.Model):
    session_key = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_key[:8]}… ({self.created_at:%Y-%m-%d})"


class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Observability fields — useful for later tracing/monitoring
    sources_used = models.JSONField(default=list)
    order_lookup_used = models.BooleanField(default=False)
    escalation_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"

import logging

logger = logging.getLogger('agent')


class OrderService:
    def lookup_by_id(self, order_id: str) -> dict | None:
        from agent.models import Order

        try:
            order = Order.objects.get(order_id=order_id.upper())
            logger.info("Order lookup hit | order_id=%s | status=%s", order.order_id, order.shipping_status)
            return self._serialize(order)
        except Order.DoesNotExist:
            logger.info("Order lookup miss | order_id=%s", order_id)
            return None
        except Exception as e:
            logger.error("Order lookup error | order_id=%s | error=%s", order_id, str(e))
            return None

    def lookup_by_email(self, email: str) -> list[dict]:
        from agent.models import Order

        try:
            orders = Order.objects.filter(email__iexact=email.strip()).order_by('-order_date')
            results = [self._serialize(o) for o in orders]
            logger.info("Email order lookup | email=%s | count=%d", email, len(results))
            return results
        except Exception as e:
            logger.error("Email order lookup error | email=%s | error=%s", email, str(e))
            return []

    def _serialize(self, order) -> dict:
        return {
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'item_name': order.item_name,
            'order_date': str(order.order_date),
            'shipping_status': order.get_shipping_status_display(),
            'delivery_eta': str(order.delivery_eta) if order.delivery_eta else 'N/A',
            'tracking_number': order.tracking_number or 'Not yet assigned',
            'payment_status': order.get_payment_status_display(),
            'refund_eligible': order.refund_eligible,
        }

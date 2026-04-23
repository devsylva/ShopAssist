from datetime import date
from django.core.management.base import BaseCommand
from agent.models import Order

ORDERS = [
    {
        'order_id': 'SA-10001',
        'customer_name': 'Marcus Williams',
        'email': 'marcus.williams@email.com',
        'item_name': 'Linen Throw Pillow Set (2-pack, Sage)',
        'order_date': date(2026, 3, 15),
        'shipping_status': 'delivered',
        'delivery_eta': date(2026, 3, 22),
        'tracking_number': 'VLR-84729103',
        'refund_eligible': False,   # delivered > 30 days ago
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10002',
        'customer_name': 'Sarah Chen',
        'email': 'sarah.chen@gmail.com',
        'item_name': 'Aromatherapy Diffuser (White, 300ml)',
        'order_date': date(2026, 4, 18),
        'shipping_status': 'in_transit',
        'delivery_eta': date(2026, 4, 26),
        'tracking_number': 'VLR-39201847',
        'refund_eligible': True,
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10003',
        'customer_name': 'Jordan Taylor',
        'email': 'jordan.taylor@outlook.com',
        'item_name': 'Bamboo Desk Organizer (Natural)',
        'order_date': date(2026, 4, 20),
        'shipping_status': 'processing',
        'delivery_eta': date(2026, 4, 29),
        'tracking_number': '',
        'refund_eligible': True,
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10004',
        'customer_name': 'Emma Rodriguez',
        'email': 'emma.rodriguez@email.com',
        'item_name': 'Weighted Blanket (Navy, 15 lb)',
        'order_date': date(2026, 4, 10),
        'shipping_status': 'delivered',
        'delivery_eta': date(2026, 4, 17),
        'tracking_number': 'VLR-55012948',
        'refund_eligible': True,    # delivered 6 days ago
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10005',
        'customer_name': 'David Kim',
        'email': 'david.kim@gmail.com',
        'item_name': 'Glass Water Bottle Set (3-pack, Frost)',
        'order_date': date(2026, 4, 5),
        'shipping_status': 'cancelled',
        'delivery_eta': None,
        'tracking_number': '',
        'refund_eligible': False,   # cancelled — refund handled separately
        'payment_status': 'refund_processing',
    },
    {
        'order_id': 'SA-10006',
        'customer_name': 'Aisha Johnson',
        'email': 'aisha.johnson@email.com',
        'item_name': 'Ceramic Planter Set (3 sizes, Terracotta)',
        'order_date': date(2026, 2, 10),
        'shipping_status': 'delivered',
        'delivery_eta': date(2026, 2, 17),
        'tracking_number': 'VLR-20938471',
        'refund_eligible': False,   # delivered > 30 days ago
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10007',
        'customer_name': 'Tyler Brown',
        'email': 'tyler.brown@outlook.com',
        'item_name': 'Essential Oil Starter Kit (6 bottles)',
        'order_date': date(2026, 4, 19),
        'shipping_status': 'shipped',
        'delivery_eta': date(2026, 4, 27),
        'tracking_number': 'VLR-77463019',
        'refund_eligible': True,
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10008',
        'customer_name': 'Priya Patel',
        'email': 'priya.patel@gmail.com',
        'item_name': 'Minimalist Wall Clock (12", Matte Black)',
        'order_date': date(2026, 4, 22),
        'shipping_status': 'processing',
        'delivery_eta': date(2026, 4, 30),
        'tracking_number': '',
        'refund_eligible': True,
        'payment_status': 'paid',
    },
    {
        'order_id': 'SA-10009',
        'customer_name': 'Connor Walsh',
        'email': 'connor.walsh@email.com',
        'item_name': 'Velvet Storage Basket Set (2-pack, Cream)',
        'order_date': date(2026, 4, 21),
        'shipping_status': 'processing',
        'delivery_eta': None,
        'tracking_number': '',
        'refund_eligible': False,
        'payment_status': 'payment_failed',
    },
    {
        'order_id': 'SA-10010',
        'customer_name': 'Lisa Nakamura',
        'email': 'lisa.nakamura@gmail.com',
        'item_name': 'Scented Candle Collection (4-pack, Eucalyptus & Cedar)',
        'order_date': date(2026, 4, 1),
        'shipping_status': 'delivered',
        'delivery_eta': date(2026, 4, 8),
        'tracking_number': 'VLR-61829304',
        'refund_eligible': True,    # delivered 15 days ago
        'payment_status': 'paid',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with mock Velora orders'

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for data in ORDERS:
            _, created = Order.objects.get_or_create(
                order_id=data['order_id'],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created {data['order_id']} — {data['customer_name']}")
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Created {created_count} orders, skipped {skipped_count} existing."
            )
        )

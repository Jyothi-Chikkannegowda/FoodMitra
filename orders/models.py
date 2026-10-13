from django.db import models
from django.contrib.auth.models import User
from accounts.models import CookProfile
from menu.models import MenuItem

class Order(models.Model):
    STATUS_CHOICES = [
        ('awaiting_payment', 'Awaiting Payment'),  # NEW: brief pre-payment state, hidden from order lists
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
    ]

    DELIVERY_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup')
    order_time = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    is_preorder = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.customer.username}"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.id}"
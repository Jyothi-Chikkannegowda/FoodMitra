from django.db import models
from django.contrib.auth.models import User
from accounts.models import CookProfile
from orders.models import Order

class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer.username} for {self.cook.user.username}"
from django.db import models
from django.contrib.auth.models import User

class CookProfile(models.Model):
    KITCHEN_TYPE_CHOICES = [
        ('veg', 'Pure Veg'),
        ('nonveg', 'Non-Veg'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    speciality = models.CharField(max_length=200, blank=True)
    profile_photo = models.ImageField(upload_to='cook_photos/', blank=True)
    home_address = models.TextField()
    phone = models.CharField(max_length=15, blank=True)
    aadhaar_number = models.CharField(max_length=12)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    rating = models.FloatField(default=0.0)
    cooking_since = models.IntegerField(default=2020)
    total_orders = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # coordinates derived from home_address, used to check distance to
    # customers when they browse the menu.
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # a cook is either a Pure Veg kitchen or a Non-Veg kitchen -
    # chosen once at registration. Every dish they post must match this,
    # enforced in menu/views.py (post_menu/edit_menu), so a Pure Veg
    # cook can never have a non-veg item on their menu, guaranteeing
    # customers there's no shared kitchen/cross-contamination concern.
    kitchen_type = models.CharField(
        max_length=10,
        choices=KITCHEN_TYPE_CHOICES,
        default='veg',
    )

    def __str__(self):
        return f"{self.user.username} - Cook Profile"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='customer_photos/', blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # coordinates derived from address, used to check distance to cooks.
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Customer Profile"
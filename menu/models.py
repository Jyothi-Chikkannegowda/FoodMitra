from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import CookProfile

class MenuItem(models.Model):
    CUISINE_CHOICES = [
        ('north_indian', 'North Indian'),
        ('south_indian', 'South Indian'),
        ('chinese', 'Chinese'),
        ('continental', 'Continental'),
        ('other', 'Other'),
    ]

    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='food_photos/', blank=True)
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(10), MaxValueValidator(500)]
    )
    quantity_available = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    cuisine_type = models.CharField(max_length=50, choices=CUISINE_CHOICES)
    is_veg = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    date = models.DateField(auto_now_add=True)
    available_date = models.DateField(null=True, blank=True)
    is_preorder = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_name} by {self.cook.user.username}"
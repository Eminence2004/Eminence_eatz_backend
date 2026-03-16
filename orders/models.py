from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField


# ---------------------------
# Restaurant Model
# ---------------------------
class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    image = CloudinaryField('image', blank=True, null=True)
    base_delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)

    def __str__(self):
        return self.name


# ---------------------------
# Menu Item Model
# ---------------------------
class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = CloudinaryField('image', blank=True, null=True)
    extra_delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


# ---------------------------
# App Configuration Model
# ---------------------------
class AppConfig(models.Model):
    welcome_image = CloudinaryField('image', blank=True, null=True)
    welcome_title = models.CharField(max_length=100, default="Eminence Eatz")
    welcome_subtitle = models.TextField(default="Order your favorite meals from top restaurants in Ghana.")
    promo_text = models.CharField(max_length=100, default="FREE DELIVERY", blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "App Configuration"

    def __str__(self):
        return "App Configuration"


# ---------------------------
# Order Model
# ---------------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PREPARING', 'Preparing'),
        ('DELIVERING', 'Delivering'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField(MenuItem, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.CharField(max_length=255, default="Pick up at restaurant")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


# ---------------------------
# Payment Model
# ---------------------------
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('MOMO', 'Mobile Money'),
        ('CARD', 'Card'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='MOMO')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"


# ---------------------------
# Profile Model
# ---------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username
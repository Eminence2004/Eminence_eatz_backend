from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class OTPRecord(models.Model):
    """Track OTP requests for analytics and rate limiting"""
    phone_number = models.CharField(max_length=15, db_index=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='otp_records'
    )
    request_count = models.IntegerField(default=1)
    last_request_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['phone_number', 'user']
        verbose_name = 'OTP Record'
        verbose_name_plural = 'OTP Records'
        ordering = ['-last_request_at']
        
    def __str__(self):
        user_info = f" - {self.user.email}" if self.user else ""
        return f"{self.phone_number}{user_info} ({self.request_count} requests)"
    
    def is_verified(self):
        return self.verified_at is not None
    is_verified.boolean = True
    is_verified.short_description = 'Verified'
    
    def time_since_last_request(self):
        if self.last_request_at:
            delta = timezone.now() - self.last_request_at
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{hours}h {minutes}m ago"
        return "Never"
    time_since_last_request.short_description = 'Last Request'
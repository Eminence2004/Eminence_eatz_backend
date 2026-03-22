from django.urls import path
from . import views

app_name = 'otp_verification'

urlpatterns = [
    # Main OTP endpoints
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    
    # User account linking (authenticated)
    path('api/verify-and-link/', views.verify_and_link_user, name='verify_and_link'),
    
    # Status and health checks
    path('api/status/', views.check_otp_status, name='otp_status'),
    path('api/health/', views.health_check, name='otp_health'),
]
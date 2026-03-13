# backend/api/utils.py
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_via_email(email, otp):
    subject = "Your Verification Code - Eminence Eatz"
    message = f"Your OTP code is {otp}. It expires in 10 minutes."
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    send_mail(subject, message, email_from, recipient_list)

def send_otp_via_sms(phone_number, otp):
    # Simulate sending SMS by printing to console
    print(f"------------ SMS SIMULATION ------------")
    print(f"To: {phone_number}")
    print(f"Code: {otp}")
    print(f"----------------------------------------")
    return True
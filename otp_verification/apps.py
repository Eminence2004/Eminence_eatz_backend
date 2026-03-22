from django.apps import AppConfig

class OtpVerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'otp_verification'
    verbose_name = 'OTP Verification'
    
    def ready(self):
        # Import signals here if you add them later
        pass
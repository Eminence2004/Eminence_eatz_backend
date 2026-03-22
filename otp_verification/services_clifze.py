import requests
import logging
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from .models import OTPRecord

logger = logging.getLogger(__name__)

class ClifzeSMSService:
    """Handle OTP generation and verification with Clifze SMS"""
    
    BASE_URL = "https://www.clifze.shop/api/v1"
    
    def __init__(self):
        self.api_key = getattr(settings, 'CLIFZE_API_KEY', None)
        self.sender_id = getattr(settings, 'CLIFZE_SENDER_ID', 'Eminence')
        self.expiry_minutes = getattr(settings, 'CLIFZE_OTP_EXPIRY', 10)
        
        if not self.api_key:
            logger.error("CLIFZE_API_KEY not set in settings")
            raise ValueError("CLIFZE_API_KEY not set in settings")
        
        logger.info(f"Clifze SMS Service initialized with sender ID: {self.sender_id}")
    
    def send_otp(self, phone_number, user=None, custom_message=None):
        """
        Send OTP to phone number using Clifze SMS
        
        Args:
            phone_number: Can be in format '024XXXXXXX' or '233XXXXXXXXX'
            user: Optional user instance for tracking
            custom_message: Optional custom message (must contain [otp])
            
        Returns:
            dict: Response with status and message
        """
        # Format phone number to local format (024XXXXXXX) for Clifze
        formatted_phone = self._format_phone_number(phone_number, keep_local=True)
        
        # Validate phone number format
        if not formatted_phone or len(formatted_phone) < 10:
            return {
                "success": False,
                "message": "Invalid phone number format. Please use a valid Ghana number (e.g., 024XXXXXXX)",
                "code": "INVALID_PHONE"
            }
        
        # Check rate limiting
        can_send, message = self._check_rate_limit(formatted_phone, user)
        if not can_send:
            return {
                "success": False,
                "message": message,
                "code": "RATE_LIMIT"
            }
        
        # Prepare the message (must contain [otp] placeholder)
        if custom_message and '[otp]' in custom_message:
            message_text = custom_message
        else:
            message_text = "Your Eminence verification code is [otp]"
        
        # Prepare request data - simplified to match their documentation exactly
        data = {
            "api_key": self.api_key,
            "sender_id": self.sender_id,
            "recipient": formatted_phone,
            "message": message_text
        }
        
        # Only add expiry if it's explicitly set and not default
        if self.expiry_minutes != 10:
            data["expiry"] = self.expiry_minutes
        
        logger.info(f"Sending OTP via Clifze to {formatted_phone}")
        logger.debug(f"Request data: {data}")
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/otp/send",
                data=data,
                timeout=15,
                headers={
                    'User-Agent': 'Django-Clifze-OTP/1.0',
                    'Accept': 'application/json'
                }
            )
            
            # Log the raw response for debugging
            logger.debug(f"Clifze response status: {response.status_code}")
            logger.debug(f"Clifze response text: {response.text}")
            
            # Try to parse JSON response
            try:
                result = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response: {response.text}")
                result = {"status": "error", "message": "Invalid response from server"}
            
            # Update OTP record for tracking
            self._update_otp_record(formatted_phone, user)
            
            # Check if successful (based on their example response)
            if response.status_code == 200 and result.get('status') == 'success':
                logger.info(f"OTP sent successfully to {formatted_phone}")
                
                # Store expiry info in cache if available
                if result.get('expiry_at'):
                    cache_key = f"otp_expiry_{formatted_phone}"
                    cache.set(cache_key, result['expiry_at'], timeout=self.expiry_minutes * 60)
                
                return {
                    "success": True,
                    "message": result.get('message', 'OTP sent successfully'),
                    "data": {
                        "credit_balance": result.get('credit_balance'),
                        "expiry_at": result.get('expiry_at'),
                        "phone": formatted_phone
                    }
                }
            else:
                error_msg = result.get('message', f"Error {response.status_code}")
                error_code = result.get('code', str(response.status_code))
                
                # Log the full error details for debugging
                logger.error(f"Clifze OTP failed. Status: {response.status_code}, Response: {result}, Request Data: {data}")
                
                return {
                    "success": False,
                    "message": error_msg,
                    "code": error_code,
                    "details": result if response.status_code != 200 else None
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending OTP to {formatted_phone}")
            return {
                "success": False,
                "message": "Request timeout. Please try again.",
                "code": "TIMEOUT"
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error sending OTP to {formatted_phone}")
            return {
                "success": False,
                "message": "Network connection error. Please check your internet.",
                "code": "CONNECTION_ERROR"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending OTP to {formatted_phone}: {str(e)}")
            return {
                "success": False,
                "message": "Network error. Please try again.",
                "code": "NETWORK_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending OTP: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "An unexpected error occurred.",
                "code": "UNKNOWN_ERROR"
            }
    
    def verify_otp(self, phone_number, code):
        """
        Verify OTP code using Clifze SMS
        
        Args:
            phone_number: The phone number the OTP was sent to
            code: The 6-digit OTP code received
            
        Returns:
            dict: Verification result
        """
        formatted_phone = self._format_phone_number(phone_number, keep_local=True)
        
        # Validate phone number
        if not formatted_phone:
            return {
                "success": False,
                "message": "Invalid phone number",
                "code": "INVALID_PHONE"
            }
        
        # Validate code format (Clifze uses 6-digit codes)
        if not code or not code.isdigit():
            return {
                "success": False,
                "message": "Please enter a valid numeric code.",
                "code": "INVALID_FORMAT"
            }
        
        if len(code) != 6:
            return {
                "success": False,
                "message": "Please enter a valid 6-digit code.",
                "code": "INVALID_LENGTH"
            }
        
        # Prepare request data
        data = {
            "api_key": self.api_key,
            "recipient": formatted_phone,
            "otp_code": code
        }
        
        logger.info(f"Verifying OTP for {formatted_phone}")
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/otp/verify",
                data=data,
                timeout=10,
                headers={
                    'User-Agent': 'Django-Clifze-OTP/1.0',
                    'Accept': 'application/json'
                }
            )
            
            logger.debug(f"Verify response status: {response.status_code}")
            logger.debug(f"Verify response text: {response.text}")
            
            try:
                result = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response: {response.text}")
                result = {"status": "error", "message": "Invalid response from server"}
            
            # Check verification success
            if response.status_code == 200 and result.get('status') == 'success':
                logger.info(f"OTP verified successfully for {formatted_phone}")
                
                # Mark as verified in records
                self._mark_as_verified(formatted_phone)
                
                # Clear any cached expiry
                cache_key = f"otp_expiry_{formatted_phone}"
                cache.delete(cache_key)
                
                return {
                    "success": True,
                    "message": result.get('message', 'Verification successful'),
                    "data": {
                        "verified": True,
                        "phone": formatted_phone
                    }
                }
            else:
                error_msg = result.get('message', 'Verification failed')
                error_code = result.get('code', str(response.status_code))
                
                logger.warning(f"OTP verification failed for {formatted_phone}: {error_msg}")
                
                return {
                    "success": False,
                    "message": error_msg,
                    "code": error_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error verifying OTP for {formatted_phone}: {str(e)}")
            return {
                "success": False,
                "message": "Network error. Please try again.",
                "code": "NETWORK_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error verifying OTP: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "An unexpected error occurred.",
                "code": "UNKNOWN_ERROR"
            }
    
    def check_balance(self):
        """
        Check Clifze SMS account balance
        Note: Returns the last known credit balance from send_otp responses
        """
        return {
            "success": False,
            "message": "Balance information is returned in each OTP send response. Please check the 'credit_balance' field when sending OTPs.",
            "code": "BALANCE_VIA_SEND"
        }
    
    def _format_phone_number(self, phone_number, keep_local=True):
        """
        Format phone number for Clifze SMS
        
        Args:
            phone_number: Raw phone number input
            keep_local: If True, keep in local format (024...), else convert to 233 format
        
        Returns:
            Formatted phone number string
        """
        if not phone_number:
            return None
            
        # Convert to string and remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(phone_number)))
        
        if not cleaned:
            return None
        
        # Handle different formats
        if keep_local:
            # Convert to local format (0XX...)
            if cleaned.startswith('233'):
                # Remove 233 and add leading 0
                cleaned = '0' + cleaned[3:]
            elif cleaned.startswith('0'):
                # Already in local format
                pass
            elif len(cleaned) == 9:
                # If it's 9 digits (e.g., 547327938), add leading 0
                cleaned = '0' + cleaned
            # Ensure it's exactly 10 digits for Ghana numbers
            if len(cleaned) > 10:
                cleaned = cleaned[:10]
            return cleaned
        else:
            # Convert to 233 format (for internal storage)
            if cleaned.startswith('0'):
                cleaned = '233' + cleaned[1:]
            elif cleaned.startswith('233'):
                # Already in correct format
                pass
            elif len(cleaned) == 9:
                cleaned = '233' + cleaned
            return cleaned
    
    def _check_rate_limit(self, phone_number, user=None):
        """Check if user has exceeded rate limits"""
        if not user:
            return True, None
            
        try:
            # Check in database
            record, created = OTPRecord.objects.get_or_create(
                phone_number=self._format_phone_number(phone_number, keep_local=False),
                user=user,
                defaults={'request_count': 0}
            )
            
            # Reset count if last request was more than 24 hours ago
            if timezone.now() - record.last_request_at > timezone.timedelta(hours=24):
                record.request_count = 0
                record.save()
            
            # Check max requests per day
            max_requests = getattr(settings, 'OTP_MAX_REQUESTS_PER_DAY', 10)
            if record.request_count >= max_requests:
                return False, f"Maximum OTP requests ({max_requests}) reached for today. Please try again tomorrow."
            
            # Check cooldown period
            cooldown_minutes = getattr(settings, 'OTP_COOLDOWN_MINUTES', 2)
            if not created:
                time_since_last = timezone.now() - record.last_request_at
                if time_since_last.total_seconds() < cooldown_minutes * 60:
                    wait_seconds = int(cooldown_minutes * 60 - time_since_last.total_seconds())
                    return False, f"Please wait {wait_seconds} seconds before requesting another code."
            
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True, None  # Allow on error
    
    def _update_otp_record(self, phone_number, user=None):
        """Update OTP request record"""
        if user:
            try:
                formatted_phone = self._format_phone_number(phone_number, keep_local=False)
                record, created = OTPRecord.objects.get_or_create(
                    phone_number=formatted_phone,
                    user=user,
                    defaults={'request_count': 1}
                )
                if not created:
                    # Reset count if last request was more than 24 hours ago
                    if timezone.now() - record.last_request_at > timezone.timedelta(hours=24):
                        record.request_count = 1
                    else:
                        record.request_count += 1
                    record.save()
            except Exception as e:
                logger.error(f"Error updating OTP record: {str(e)}")
    
    def _mark_as_verified(self, phone_number):
        """Mark phone number as verified"""
        try:
            formatted_phone = self._format_phone_number(phone_number, keep_local=False)
            OTPRecord.objects.filter(phone_number=formatted_phone).update(
                verified_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error marking as verified: {str(e)}")
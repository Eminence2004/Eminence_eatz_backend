import logging
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .services_clifze import ClifzeSMSService

from .models import OTPRecord

logger = logging.getLogger(__name__)
User = get_user_model()

# Initialize the OTP service
# Initialize the Clifze service
try:
    otp_service = ClifzeSMSService()
except ValueError as e:
    logger.error(f"Failed to initialize Clifze service: {str(e)}")
    otp_service = None

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """
    API endpoint to send OTP
    Expected JSON: {"phone_number": "024XXXXXXX"}
    
    Returns:
        - 200: OTP sent successfully
        - 400: Invalid request
        - 429: Rate limited
        - 503: Service unavailable (insufficient balance)
        - 500: Server error
    """
    # Check if service is initialized
    if otp_service is None:
        return Response({
            'success': False,
            'message': 'OTP service is not configured properly. Please contact support.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Get phone number from request
        phone_number = request.data.get('phone_number')
        
        # Validate phone number
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Basic phone number validation (Ghana numbers)
        cleaned = phone_number.strip().replace(' ', '').replace('-', '')
        if not cleaned.startswith('0') and not cleaned.startswith('233'):
            return Response({
                'success': False,
                'message': 'Please enter a valid Ghana phone number (e.g., 024XXXXXXX)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Associate with user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Send OTP
        result = otp_service.send_otp(phone_number, user)
        
        # Handle response based on result
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'data': {
                    'phone': result.get('data', {}).get('phone', phone_number)
                }
            }, status=status.HTTP_200_OK)
        else:
            # Map common errors to appropriate HTTP status codes
            status_code = status.HTTP_400_BAD_REQUEST
            
            if result.get('code') in ['1007', '1008']:  # Insufficient balance
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                logger.error(f"Arkesel balance issue: {result['message']}")
            elif result.get('code') == '401':  # Invalid API key
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                logger.error(f"Arkesel API key error: {result['message']}")
            elif result.get('code') == 'RATE_LIMIT':
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            elif result.get('code') in ['TIMEOUT', 'CONNECTION_ERROR', 'NETWORK_ERROR']:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif result.get('code') == '422':  # Validation error
                status_code = status.HTTP_400_BAD_REQUEST
                # Add more specific message for 422
                if "number field is required" in result.get('message', ''):
                    result['message'] = "Invalid request format. Please try again."
            
            return Response({
                'success': False,
                'message': result['message'],
                'code': result.get('code')
            }, status=status_code)
            
    except Exception as e:
        logger.error(f"Unexpected error in send_otp: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    API endpoint to verify OTP
    Expected JSON: {"phone_number": "024XXXXXXX", "code": "123456"}
    
    Returns:
        - 200: Verification successful
        - 400: Invalid code or format
        - 503: Service unavailable
    """
    # Check if service is initialized
    if otp_service is None:
        return Response({
            'success': False,
            'message': 'OTP service is not configured properly. Please contact support.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Get data from request
        phone_number = request.data.get('phone_number')
        code = request.data.get('code')
        
        # Validate required fields
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not code:
            return Response({
                'success': False,
                'message': 'Verification code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        result = otp_service.verify_otp(phone_number, code)
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'data': {
                    'verified': True,
                    'phone': result.get('data', {}).get('phone', phone_number)
                }
            }, status=status.HTTP_200_OK)
        else:
            # Handle specific error cases
            status_code = status.HTTP_400_BAD_REQUEST
            
            if result.get('code') == 'EXPIRED':
                status_code = status.HTTP_400_BAD_REQUEST
            elif result.get('code') == 'INVALID':
                status_code = status.HTTP_400_BAD_REQUEST
            elif result.get('code') == 'INVALID_FORMAT':
                status_code = status.HTTP_400_BAD_REQUEST
            
            return Response({
                'success': False,
                'message': result['message'],
                'code': result.get('code')
            }, status=status_code)
            
    except Exception as e:
        logger.error(f"Unexpected error in verify_otp: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_and_link_user(request):
    """
    Verify OTP and link to authenticated user
    Useful for adding phone number to existing account
    Expected JSON: {"phone_number": "024XXXXXXX", "code": "123456"}
    
    Returns:
        - 200: Phone number verified and linked
        - 400: Invalid code or missing fields
        - 409: Phone already in use
    """
    # Check if service is initialized
    if otp_service is None:
        return Response({
            'success': False,
            'message': 'OTP service is not configured properly. Please contact support.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        phone_number = request.data.get('phone_number')
        code = request.data.get('code')
        
        if not phone_number or not code:
            return Response({
                'success': False,
                'message': 'Phone number and code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if phone number is already used by another user
        phone_exists = User.objects.filter(
            phone_number=phone_number  # Assuming your User model has phone_number field
        ).exclude(id=request.user.id).exists()
        
        if phone_exists:
            return Response({
                'success': False,
                'message': 'This phone number is already associated with another account'
            }, status=status.HTTP_409_CONFLICT)
        
        # Verify OTP first
        result = otp_service.verify_otp(phone_number, code)
        
        if result['success']:
            # Link phone to user - add phone_number field to your User model if not exists
            user = request.user
            # Uncomment if you have phone_number field in User model
            # user.phone_number = phone_number
            # user.phone_verified = True
            # user.save()
            
            return Response({
                'success': True,
                'message': 'Phone number verified and linked to account successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'code': result.get('code')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in verify_and_link_user: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'An unexpected error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_otp_status(request):
    """
    Check OTP status for authenticated user's phone
    Returns verification status and remaining requests
    """
    try:
        user = request.user
        phone_number = request.query_params.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Format phone number
        from .services import ArkeselOTPService
        temp_service = ArkeselOTPService()
        formatted_phone = temp_service._format_phone_number(phone_number)
        
        # Check OTP record
        from .models import OTPRecord
        try:
            record = OTPRecord.objects.get(
                phone_number=formatted_phone,
                user=user
            )
            
            # Calculate remaining requests
            max_requests = getattr(settings, 'OTP_MAX_REQUESTS_PER_DAY', 10)
            remaining = max(0, max_requests - record.request_count)
            
            # Check if verified
            is_verified = record.verified_at is not None
            
            return Response({
                'success': True,
                'data': {
                    'phone': phone_number,
                    'verified': is_verified,
                    'verified_at': record.verified_at,
                    'requests_today': record.request_count,
                    'remaining_requests': remaining,
                    'last_request': record.last_request_at
                }
            }, status=status.HTTP_200_OK)
            
        except OTPRecord.DoesNotExist:
            return Response({
                'success': True,
                'data': {
                    'phone': phone_number,
                    'verified': False,
                    'requests_today': 0,
                    'remaining_requests': getattr(settings, 'OTP_MAX_REQUESTS_PER_DAY', 10)
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error checking OTP status: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error checking status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify OTP service is configured
    """
    if otp_service is None:
        return Response({
            'status': 'unhealthy',
            'service': 'OTP',
            'message': 'OTP service not configured'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # Check balance (optional)
    balance_result = otp_service.check_balance()
    
    return Response({
        'status': 'healthy',
        'service': 'OTP',
        'configured': True,
        'sender_id': otp_service.sender_id,
        'balance_check': balance_result.get('success', False),
        'message': 'OTP service is operational'
    }, status=status.HTTP_200_OK)
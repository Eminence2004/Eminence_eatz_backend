import os
from decimal import Decimal
from twilio.rest import Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Restaurant, MenuItem, Order, Payment, Profile, AppConfig  
from .serializers import (
    RestaurantSerializer, MenuItemSerializer, OrderSerializer, PaymentSerializer
)
from .paystack import initialize_transaction, verify_transaction

# --- CRUD VIEWS ---

class RestaurantListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [AllowAny]

class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        queryset = MenuItem.objects.all()
        rid = self.request.query_params.get('restaurant')
        if rid: queryset = queryset.filter(restaurant_id=rid)
        return queryset

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

# =======================================
#           PAYMENT LOGIC
# =======================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_paystack_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or unauthorized"}, status=403)

    user_email = request.user.email
    if not user_email or user_email == "":
        user_email = f"{request.user.username}@fooddelivery.com"

    food_total = sum(item.price for item in order.items.all())
    
    # Get delivery fee from AppConfig instead of hardcoding
    config = AppConfig.objects.first()
    delivery_fee = config.delivery_fee if config else Decimal('15.00')
    
    total = food_total + delivery_fee
    order.total_price = total
    order.save()

    amount_in_pesewas = int(total * 100)
    res = initialize_transaction(user_email, amount_in_pesewas, order.id)

    if res.get("status"):
        return Response({
            "authorization_url": res["data"]["authorization_url"],
            "reference": res["data"]["reference"]
        })
    return Response({"error": res.get("message", "Paystack error")}, status=400)

@api_view(['GET'])
def verify_paystack_payment(request, reference):
    res = verify_transaction(reference)
    if res.get("status"):
        metadata = res["data"].get("metadata", {})
        oid = metadata.get("order_id")

        if oid:
            Order.objects.filter(id=oid).update(status="PAID")
        return Response({"message": "Payment Verified Successfully"})

    return Response({"error": "Payment verification failed"}, status=400)

# =======================================
#           AUTH & VERIFICATION
# =======================================

def get_twilio_client():
    return Client(
        os.environ.get('TWILIO_ACCOUNT_SID'),
        os.environ.get('TWILIO_AUTH_TOKEN')
    )

def format_phone(phone):
    if phone.startswith('0'):
        phone = '+233' + phone[1:]
    if not phone.startswith('+'):
        phone = '+233' + phone
    return phone


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    full_name = request.data.get('full_name')
    email = request.data.get('email')
    password = request.data.get('password')
    phone = request.data.get('phone')

    if not all([full_name, email, password, phone]):
        return Response({'error': 'All fields are required'}, status=400)

    phone = format_phone(phone)

    if User.objects.filter(username=phone).exists():
        return Response({'error': 'Phone number already registered'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=400)

    User.objects.create_user(
        username=phone,
        email=email,
        password=password,
        first_name=full_name,
    )

    return Response({'message': 'User created successfully'}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    phone = request.data.get('phone')

    if not phone:
        return Response({'error': 'Phone number required'}, status=400)

    phone = format_phone(phone)

    try:
        client = get_twilio_client()
        client.verify.v2.services(
            os.environ.get('TWILIO_VERIFY_SID')
        ).verifications.create(to=phone, channel='sms')
        return Response({'message': 'OTP sent successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')

    if not phone or not otp:
        return Response({'error': 'Phone and OTP are required'}, status=400)

    phone = format_phone(phone)

    try:
        client = get_twilio_client()
        result = client.verify.v2.services(
            os.environ.get('TWILIO_VERIFY_SID')
        ).verification_checks.create(to=phone, code=otp)

        if result.status == 'approved':
            try:
                user = User.objects.get(username=phone)
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=200)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)
        else:
            return Response({'error': 'Invalid or expired OTP'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_send_otp(request):
    phone = request.data.get('phone')

    if not phone:
        return Response({'error': 'Phone number required'}, status=400)

    phone = format_phone(phone)

    if not User.objects.filter(username=phone).exists():
        return Response({'error': 'Account not found. Please register.'}, status=404)

    try:
        client = get_twilio_client()
        client.verify.v2.services(
            os.environ.get('TWILIO_VERIFY_SID')
        ).verifications.create(to=phone, channel='sms')
        return Response({'message': 'OTP sent'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_app_config(request):
    from .models import AppConfig
    config = AppConfig.objects.first()
    if config:
        from .serializers import AppConfigSerializer
        return Response(AppConfigSerializer(config).data)
    return Response({
        'welcome_image': None,
        'welcome_title': 'Eminence Eatz',
        'welcome_subtitle': 'Order your favorite meals from top restaurants in Ghana.',
        'promo_text': 'FREE DELIVERY',
    })
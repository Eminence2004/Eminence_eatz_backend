import os
from decimal import Decimal
import random
from django.core.cache import cache
from twilio.rest import Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Restaurant, MenuItem, Order, Payment, Profile
from .serializers import (
    RestaurantSerializer, MenuItemSerializer, OrderSerializer, PaymentSerializer
)
from .utils import generate_otp
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
    delivery_fee = Decimal(15.00)
    total = food_total + delivery_fee
    
    order.total_price = total
    order.save()

    amount_in_pesewas = int(total * 100)

    res = initialize_transaction(
        user_email, 
        amount_in_pesewas, 
        order.id
    )

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

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    full_name = request.data.get('full_name')
    email = request.data.get('email')
    password = request.data.get('password')
    phone = request.data.get('phone')

    if User.objects.filter(username=phone).exists():
        return Response({'error': 'Phone number already registered'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=400)

    user = User.objects.create_user(
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

    # Format phone number
    if phone.startswith('0'):
        phone = '+233' + phone[1:]

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # Save OTP in cache for 5 minutes
    cache.set(f'otp_{phone}', otp, timeout=300)

    # Send via Twilio
    try:
        client = Client(
            os.environ.get('TWILIO_ACCOUNT_SID'),
            os.environ.get('TWILIO_AUTH_TOKEN')
        )
        client.messages.create(
            body=f'Your Eminence Eatz verification code is: {otp}',
            from_=os.environ.get('TWILIO_PHONE_NUMBER'),
            to=phone
        )
        return Response({'message': 'OTP sent successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')

    if phone.startswith('0'):
        phone = '+233' + phone[1:]

    cached_otp = cache.get(f'otp_{phone}')

    if cached_otp is None:
        return Response({'error': 'OTP expired. Please request a new one.'}, status=400)

    if cached_otp != otp:
        return Response({'error': 'Invalid OTP'}, status=400)

    # OTP correct — log the user in
    try:
        user = User.objects.get(username=phone)
        refresh = RefreshToken.for_user(user)
        cache.delete(f'otp_{phone}')
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=200)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_send_otp(request):
    phone = request.data.get('phone')

    if phone.startswith('0'):
        phone = '+233' + phone[1:]

    if not User.objects.filter(username=phone).exists():
        return Response({'error': 'Account not found. Please register.'}, status=404)

    # Reuse send_otp logic
    otp = str(random.randint(100000, 999999))
    cache.set(f'otp_{phone}', otp, timeout=300)

    try:
        client = Client(
            os.environ.get('TWILIO_ACCOUNT_SID'),
            os.environ.get('TWILIO_AUTH_TOKEN')
        )
        client.messages.create(
            body=f'Your Eminence Eatz login code is: {otp}',
            from_=os.environ.get('TWILIO_PHONE_NUMBER'),
            to=phone
        )
        return Response({'message': 'OTP sent'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def clear_test_users(request):
    User.objects.filter(is_superuser=False).delete()
    return Response({'message': 'Cleared'}, status=200)    
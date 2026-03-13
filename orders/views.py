from decimal import Decimal
import random
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
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=request.data['username'], 
                email=request.data['email'], 
                password=request.data['password']
            )
            user.save()
            Profile.objects.create(user=user)
            return Response({"message": "User registered successfully"}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Checks if phone exists before Firebase sends SMS"""
    phone = request.data.get('username')
    if User.objects.filter(username=phone).exists():
        return Response({"message": "User exists"}, status=200)
    return Response({"error": "Account not found. Please register."}, status=404)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    try:
        user = User.objects.get(username=phone)
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token), 
            "refresh": str(refresh),
            "message": "Login successful"
        }, status=200)
    except User.DoesNotExist:
        return Response({"error": "User profile not found"}, status=404)

@api_view(['POST'])
@permission_classes([AllowAny])
def calculate_delivery_eta(request):
    return Response({
        "eta": f"{random.randint(15, 35)} mins", 
        "status": random.choice(["Clear", "Moderate Traffic", "Heavy Traffic"])
    })
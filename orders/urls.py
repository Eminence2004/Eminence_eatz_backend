from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RestaurantListView, 
    MenuItemViewSet, 
    OrderViewSet, 
    PaymentViewSet, 
    start_paystack_payment, 
    verify_paystack_payment,
    register_user, 
    login_user,
    verify_otp, 
    calculate_delivery_eta
)

router = DefaultRouter()
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('restaurants/', RestaurantListView.as_view(), name='restaurant-list'),
    
    # Auth
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('verify-otp/', verify_otp, name='verify-otp'),

    # Payments
    path('pay/<int:order_id>/', start_paystack_payment, name='pay-start'),
    path('verify-payment/<str:reference>/', verify_paystack_payment, name='pay-verify'),

    # Misc
    path('calculate-eta/', calculate_delivery_eta, name='calculate-eta'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    RestaurantListView,
    MenuItemViewSet,
    OrderViewSet,
    PaymentViewSet,
    start_paystack_payment,
    verify_paystack_payment,
)

router = DefaultRouter()
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('restaurants/', RestaurantListView.as_view(), name='restaurant-list'),

    # Auth
    path('register/', views.register_user, name='register'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login-otp/', views.login_send_otp, name='login_send_otp'),

    # Payments
    path('pay/<int:order_id>/', start_paystack_payment, name='pay-start'),
    path('verify-payment/<str:reference>/', verify_paystack_payment, name='pay-verify'),

    path('app-config/', views.get_app_config, name='app-config'),
    path('debug-cloudinary/', views.debug_cloudinary, name='debug-cloudinary'),
    path('profile/', views.get_user_profile, name='profile'),

    
]
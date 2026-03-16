import os
from rest_framework import serializers
from .models import Restaurant, MenuItem, Order, Payment, AppConfig
from django.contrib.auth.models import User

CLOUDINARY_BASE = f"https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME', 'dbe0l5g7w')}/image/upload/"


def get_cloudinary_url(image_field):
    if not image_field:
        return None
    value = str(image_field)
    if value.startswith('http'):
        return value
    return f"{CLOUDINARY_BASE}{value}"


class MenuItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'restaurant', 'name', 'description', 'price', 'image', 'extra_delivery_fee']

    def get_image(self, obj):
        return get_cloudinary_url(obj.image)


class RestaurantSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    menu_items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = '__all__'

    def get_image(self, obj):
        return get_cloudinary_url(obj.image)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['user']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AppConfigSerializer(serializers.ModelSerializer):
    welcome_image = serializers.SerializerMethodField()

    class Meta:
        model = AppConfig
        fields = '__all__'

    def get_welcome_image(self, obj):
        return get_cloudinary_url(obj.welcome_image)
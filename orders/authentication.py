import os
import firebase_admin
from firebase_admin import auth, credentials
from django.contrib.auth.models import User
from rest_framework import authentication, exceptions
from django.conf import settings

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # 1. Get the Authorization Header (Bearer <token>)
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        # 2. Extract the token
        id_token = auth_header.split(' ').pop()

        try:
            # 3. Verify the token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            
            # 4. Get the phone number (Firebase UID or phone_number)
            # Since you use Phone Auth, 'phone_number' is the most reliable
            phone_number = decoded_token.get('phone_number')

            if not phone_number:
                raise exceptions.AuthenticationFailed('No phone number associated with this Firebase account.')

            # 5. Find or Create the User in Django
            # We use the phone number as the username
            user, created = User.objects.get_or_create(
                username=phone_number,
                defaults={
                    'is_active': True,
                }
            )

            # 6. Return the user and None (for the auth pointer)
            return (user, None)

        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Firebase Authentication Error: {str(e)}')
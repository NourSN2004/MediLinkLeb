from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class AuthenticationService:
    @staticmethod
    def signup_user(email, password, user_type, first_name='', last_name=''):
        """Create a new user account"""
        try:
            # Create full name from first and last name
            name = f"{first_name} {last_name}".strip() or email.split('@')[0]
            
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                name=name,
                role=user_type
            )
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def login_user(email, password):
        """Authenticate and login a user"""
        user = authenticate(username=email, password=password)
        if user and user.is_active:
            return user
        return None
    
    @staticmethod
    def send_verification_email(user):
        """Send verification email to user"""
        verification_token = str(uuid.uuid4())
        # In production, store token in database or cache
        verification_link = f"{settings.SITE_URL}/verify-email/{verification_token}"
        
        try:
            send_mail(
                'Verify your email',
                f'Please click this link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False
    
    @staticmethod
    def initiate_password_reset(email):
        """Initiate password reset process"""
        try:
            user = User.objects.get(email=email)
            token = str(uuid.uuid4())
            user.reset_password_token = token
            user.reset_password_expires = timezone.now() + timedelta(hours=24)
            user.save()
            
            reset_link = f"{settings.SITE_URL}/reset-password/{token}"
            send_mail(
                'Reset your password',
                f'Click this link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return True
        except User.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error initiating password reset: {e}")
            return False
    
    @staticmethod
    def reset_password(token, new_password):
        """Reset user password with valid token"""
        try:
            user = User.objects.get(
                reset_password_token=token,
                reset_password_expires__gt=timezone.now()
            )
            user.set_password(new_password)
            user.reset_password_token = None
            user.reset_password_expires = None
            user.save()
            return True
        except User.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error resetting password: {e}")
            return False
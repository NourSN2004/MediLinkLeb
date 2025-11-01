from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.utils.html import strip_tags
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
    
    # @staticmethod
    # def send_verification_email(user):
    #     """Send verification email to user"""
    #     verification_token = str(uuid.uuid4())
    #     # In production, store token in database or cache
    #     verification_link = f"{settings.SITE_URL}/verify-email/{verification_token}"
        
    #     try:
    #         send_mail(
    #             'Verify your email',
    #             f'Please click this link to verify your email: {verification_link}',
    #             settings.DEFAULT_FROM_EMAIL,
    #             [user.email],
    #             fail_silently=False,
    #         )
    #         return True
    #     except Exception as e:
    #         print(f"Error sending verification email: {e}")
    #         return False
    
    @staticmethod
    def send_verification_email(user, request):
        """
        Send verification email to user with token stored in database
        
        Args:
            user: User instance
            request: HTTP request object (needed to build absolute URL)
        
        Returns:
            EmailVerificationToken instance or None on failure
        """
        from .models import EmailVerificationToken
        
        try:
            # Create verification token
            token = EmailVerificationToken.objects.create(user=user)
            
            # Build verification URL
            verification_url = request.build_absolute_uri(
                f'/verify-email/{token.token}/'
            )
            
            # Email context
            context = {
                'user': user,
                'user_name': user.name or user.email.split('@')[0],
                'verification_url': verification_url,
                'site_name': 'MediLink Clinic Platform',
                'expiry_hours': 24,
            }
            
            # Render email templates
            html_message = render_to_string('emails/verification_email.html', context)
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject='Verify your email address - MediLink',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return token
            
        except Exception as e:
            print(f"Error sending verification email: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def resend_verification_email(user, request):
        """
        Resend verification email to user
        Invalidates old tokens and creates a new one
        
        Args:
            user: User instance
            request: HTTP request object
        
        Returns:
            EmailVerificationToken instance or None on failure
        """
        from .models import EmailVerificationToken
        
        try:
            # Invalidate all previous unused tokens for this user
            EmailVerificationToken.objects.filter(
                user=user,
                is_used=False
            ).update(is_used=True)
            
            # Send new verification email
            return AuthenticationService.send_verification_email(user, request)
            
        except Exception as e:
            print(f"Error resending verification email: {e}")
            return None
    
    @staticmethod
    def verify_email_token(token_string):
        """
        Verify email using token
        
        Args:
            token_string: The token string from the URL
        
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        from .models import EmailVerificationToken
        
        try:
            token = EmailVerificationToken.objects.select_related('user').get(
                token=token_string,
                is_used=False
            )
            
            if not token.is_valid():
                return False, "This verification link has expired. Please request a new one.", None
            
            # Mark token as used
            token.mark_as_used()
            
            # Verify user's email
            user = token.user
            user.verify_email()
            
            return True, "Your email has been verified successfully!", user
            
        except EmailVerificationToken.DoesNotExist:
            return False, "Invalid verification link. Please check the URL or request a new verification email.", None
        except Exception as e:
            print(f"Error verifying email token: {e}")
            return False, "An error occurred during verification. Please try again.", None
    
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
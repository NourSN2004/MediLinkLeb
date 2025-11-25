"""
Serializers for Auth & Access Service
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - used for user info responses"""

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'phone_number', 'email_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'email_verified']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'name', 'role', 'phone_number', 'password', 'password_confirm']

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_role(self, value):
        """Validate role is one of the allowed choices"""
        if value not in [User.Role.DOCTOR, User.Role.PATIENT, User.Role.PHARMACY]:
            raise serializers.ValidationError("Invalid role selected.")
        return value

    def create(self, validated_data):
        """Create a new user with encrypted password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Generate username from email (Django requires it)
        validated_data['username'] = validated_data['email']

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate credentials and authenticate user"""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Try to get the user by email
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")

            # Authenticate using username (email is stored as username)
            user = authenticate(
                request=self.context.get('request'),
                username=user_obj.username,
                password=password
            )

            if not user:
                raise serializers.ValidationError("Invalid email or password.")

            if not user.is_active:
                raise serializers.ValidationError("This account is inactive.")

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include email and password.")


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for password reset request"""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate that email exists"""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist for security
            pass
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""

    token = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password when logged in"""

    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification"""

    token = serializers.CharField()

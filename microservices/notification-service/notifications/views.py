"""
Notification Service Views
Handles API endpoints for notifications
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import connection
from django.utils import timezone
from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationPreferenceSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification CRUD operations
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    def get_queryset(self):
        """Filter notifications by user and status"""
        queryset = Notification.objects.all()

        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for a user"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        count = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return Response({'marked_read': count})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications for a user"""
        user_id = request.query_params.get('user')
        if not user_id:
            return Response(
                {'error': 'user parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).order_by('-created_at')

        serializer = NotificationListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for a user"""
        user_id = request.query_params.get('user')
        if not user_id:
            return Response(
                {'error': 'user parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        count = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).count()

        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def send_bulk(self, request):
        """Send notifications to multiple users"""
        user_ids = request.data.get('user_ids', [])
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'general')

        if not user_ids or not title or not message:
            return Response(
                {'error': 'user_ids, title, and message are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notifications = []
        for user_id in user_ids:
            notification = Notification.objects.create(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type
            )
            notifications.append(notification)

        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NotificationPreference CRUD operations
    """
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    lookup_field = 'user_id'

    def get_queryset(self):
        """Filter by user_id"""
        queryset = NotificationPreference.objects.all()
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset


# Health Check Views
class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy'}, status=status.HTTP_200_OK)


class ReadinessCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            return Response({'status': 'ready'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'status': 'not ready', 'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

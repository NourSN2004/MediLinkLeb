"""
Scheduling Service Views
Handles API endpoints for appointments and scheduling
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.models import Q
from datetime import datetime, date, timedelta
from .models import Appointment, AppointmentNote
from .serializers import (
    AppointmentSerializer,
    AppointmentListSerializer,
    AppointmentNoteSerializer
)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment CRUD operations
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer

    def get_queryset(self):
        """Filter appointments by doctor, patient, date, or status"""
        queryset = Appointment.objects.all()

        # Filter by doctor
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        # Filter by patient
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        # Filter by date
        apt_date = self.request.query_params.get('date')
        if apt_date:
            queryset = queryset.filter(appointment_date=apt_date)

        # Filter by status
        apt_status = self.request.query_params.get('status')
        if apt_status:
            queryset = queryset.filter(status=apt_status)

        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)

        return queryset.order_by('appointment_date', 'start_time')

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        if appointment.status != Appointment.Status.SCHEDULED:
            return Response(
                {'error': 'Only scheduled appointments can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        if not appointment.can_be_cancelled():
            return Response(
                {'error': 'This appointment cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = Appointment.Status.CANCELLED
        appointment.cancellation_reason = request.data.get('reason', '')
        appointment.cancelled_at = datetime.now()
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark appointment as in progress"""
        appointment = self.get_object()
        if appointment.status not in [Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]:
            return Response(
                {'error': 'Can only start scheduled or confirmed appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = Appointment.Status.IN_PROGRESS
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark appointment as completed"""
        appointment = self.get_object()
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_no_show(self, request, pk=None):
        """Mark appointment as no show"""
        appointment = self.get_object()
        appointment.status = Appointment.Status.NO_SHOW
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        doctor_id = request.query_params.get('doctor')
        patient_id = request.query_params.get('patient')

        queryset = Appointment.objects.filter(
            appointment_date__gte=date.today(),
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
        ).order_by('appointment_date', 'start_time')

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        serializer = AppointmentListSerializer(queryset[:20], many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments"""
        doctor_id = request.query_params.get('doctor')
        patient_id = request.query_params.get('patient')

        queryset = Appointment.objects.filter(
            appointment_date=date.today()
        ).order_by('start_time')

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)


class AppointmentNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AppointmentNote CRUD operations
    """
    queryset = AppointmentNote.objects.all()
    serializer_class = AppointmentNoteSerializer

    def get_queryset(self):
        """Filter notes by appointment"""
        queryset = AppointmentNote.objects.all()
        appointment_id = self.request.query_params.get('appointment')

        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)

        return queryset.select_related('appointment')


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

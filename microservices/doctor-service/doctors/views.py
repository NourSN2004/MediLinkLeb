"""
Doctor Service Views
Complete implementation with business logic
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db import connection
from datetime import datetime, timedelta, time
from .models import Doctor, DoctorWorkingHours, DoctorTimeOff
from .serializers import (
    DoctorSerializer,
    DoctorCreateSerializer,
    DoctorListSerializer,
    DoctorWorkingHoursSerializer,
    DoctorTimeOffSerializer,
    DoctorAvailabilityRequestSerializer
)


class HealthCheckView(APIView):
    """Health check for Kubernetes liveness probe"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy'}, status=status.HTTP_200_OK)


class ReadinessCheckView(APIView):
    """Readiness check for Kubernetes readiness probe"""
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


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Doctor CRUD operations
    """
    queryset = Doctor.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DoctorListSerializer
        elif self.action == 'create':
            return DoctorCreateSerializer
        return DoctorSerializer

    def get_queryset(self):
        """
        Optionally filter doctors by specialty
        """
        queryset = Doctor.objects.all()
        specialty = self.request.query_params.get('specialty', None)
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        return queryset

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Calculate available time slots for a doctor on a specific date

        Query params:
        - date: YYYY-MM-DD (required)
        - duration_minutes: appointment duration (default: 15)

        Returns: List of available time slots
        """
        doctor = self.get_object()

        # Validate request
        serializer = DoctorAvailabilityRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        date = serializer.validated_data['date']
        duration_minutes = serializer.validated_data.get('duration_minutes', 15)

        # Get day of week (1=Monday, 7=Sunday)
        day_of_week = date.isoweekday()

        # Get working hours for this day
        try:
            working_hours = DoctorWorkingHours.objects.get(
                doctor=doctor,
                day_of_week=day_of_week
            )
        except DoctorWorkingHours.DoesNotExist:
            return Response({
                'date': str(date),
                'available_slots': [],
                'message': 'Doctor does not work on this day'
            })

        # Get time-off periods for this date
        time_off_periods = DoctorTimeOff.objects.filter(
            doctor=doctor,
            date=date
        )

        # Calculate available slots
        available_slots = self._calculate_available_slots(
            working_hours.start_time,
            working_hours.end_time,
            duration_minutes,
            time_off_periods
        )

        # TODO: Filter out booked slots from Scheduling Service
        # booked_slots = self._get_booked_slots_from_scheduling(doctor_id, date)

        return Response({
            'date': str(date),
            'day_of_week': working_hours.get_day_of_week_display(),
            'working_hours': {
                'start': str(working_hours.start_time),
                'end': str(working_hours.end_time)
            },
            'duration_minutes': duration_minutes,
            'available_slots': available_slots,
            'time_off': [
                {
                    'start': str(to.start_time),
                    'end': str(to.end_time),
                    'reason': to.reason
                }
                for to in time_off_periods
            ]
        })

    def _calculate_available_slots(self, start_time, end_time, duration_minutes, time_off_periods):
        """
        Calculate all available time slots in 15-minute increments
        """
        slots = []
        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        while current_time + timedelta(minutes=duration_minutes) <= end_datetime:
            slot_start = current_time.time()
            slot_end = (current_time + timedelta(minutes=duration_minutes)).time()

            # Check if slot conflicts with time-off
            is_available = True
            for time_off in time_off_periods:
                if self._times_overlap(slot_start, slot_end, time_off.start_time, time_off.end_time):
                    is_available = False
                    break

            if is_available:
                slots.append({
                    'start': str(slot_start),
                    'end': str(slot_end)
                })

            # Move to next 15-minute slot
            current_time += timedelta(minutes=15)

        return slots

    def _times_overlap(self, start1, end1, start2, end2):
        """Check if two time ranges overlap"""
        return start1 < end2 and end1 > start2

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """
        Get doctor dashboard data
        Aggregates appointments and alerts from other services
        """
        doctor = self.get_object()
        serializer = self.get_serializer(doctor)

        # TODO: Get today's appointments from Scheduling Service
        # TODO: Get upcoming appointments from Scheduling Service
        # TODO: Get missed appointment alerts from Notification Service

        return Response({
            'doctor': serializer.data,
            'today_appointments': [],  # From Scheduling Service
            'upcoming_appointments': [],  # From Scheduling Service
            'missed_appointments': []  # From Notification Service
        })


class DoctorWorkingHoursViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor working hours
    """
    serializer_class = DoctorWorkingHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by doctor_id from URL"""
        doctor_id = self.kwargs.get('doctor_pk')
        if doctor_id:
            return DoctorWorkingHours.objects.filter(doctor_id=doctor_id)
        return DoctorWorkingHours.objects.none()

    def perform_create(self, serializer):
        """Set doctor from URL parameter"""
        doctor_id = self.kwargs.get('doctor_pk')
        doctor = Doctor.objects.get(pk=doctor_id)
        serializer.save(doctor=doctor)


class DoctorTimeOffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor time-off
    """
    serializer_class = DoctorTimeOffSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by doctor_id from URL"""
        doctor_id = self.kwargs.get('doctor_pk')
        if doctor_id:
            return DoctorTimeOff.objects.filter(doctor_id=doctor_id)
        return DoctorTimeOff.objects.none()

    def perform_create(self, serializer):
        """Set doctor from URL parameter"""
        doctor_id = self.kwargs.get('doctor_pk')
        doctor = Doctor.objects.get(pk=doctor_id)
        serializer.save(doctor=doctor)

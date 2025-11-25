"""
Patient Service Views
Handles API endpoints for patients, test results, and prescriptions
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.models import Q
from .models import Patient, PatientTestResult, Prescription
from .serializers import (
    PatientSerializer,
    PatientTestResultSerializer,
    PrescriptionSerializer
)


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient CRUD operations
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'user_id'

    @action(detail=True, methods=['get'])
    def test_results(self, request, user_id=None):
        """Get all test results for a patient"""
        patient = self.get_object()
        test_results = patient.test_results.all()
        serializer = PatientTestResultSerializer(test_results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, user_id=None):
        """Get all prescriptions for a patient"""
        patient = self.get_object()
        prescriptions = patient.prescriptions.all()

        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            prescriptions = prescriptions.filter(status=status_filter)

        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search patients by national_id or user_id"""
        query = request.query_params.get('q', '')
        if query:
            patients = Patient.objects.filter(
                Q(national_id__icontains=query) | Q(user_id=query)
            )
        else:
            patients = Patient.objects.all()

        serializer = self.get_serializer(patients, many=True)
        return Response(serializer.data)


class PatientTestResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PatientTestResult CRUD operations
    """
    queryset = PatientTestResult.objects.all()
    serializer_class = PatientTestResultSerializer

    def get_queryset(self):
        """Filter by patient if patient_user_id is provided"""
        queryset = PatientTestResult.objects.all()
        patient_user_id = self.request.query_params.get('patient')

        if patient_user_id:
            queryset = queryset.filter(patient__user_id=patient_user_id)

        return queryset.select_related('patient')


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Prescription CRUD operations
    """
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        """Filter prescriptions by patient or doctor"""
        queryset = Prescription.objects.all()

        patient_user_id = self.request.query_params.get('patient')
        doctor_id = self.request.query_params.get('doctor')
        status_filter = self.request.query_params.get('status')

        if patient_user_id:
            queryset = queryset.filter(patient__user_id=patient_user_id)

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related('patient')

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark prescription as completed"""
        prescription = self.get_object()
        prescription.status = Prescription.Status.COMPLETED
        prescription.save()
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_cancelled(self, request, pk=None):
        """Mark prescription as cancelled"""
        prescription = self.get_object()
        prescription.status = Prescription.Status.CANCELLED
        prescription.save()
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)


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

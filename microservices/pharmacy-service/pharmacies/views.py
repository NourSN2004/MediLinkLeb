"""
Pharmacy Service Views
Handles pharmacy profiles and staff management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.models import Q
from .models import Pharmacy, PharmacistStaff
from .serializers import (
    PharmacySerializer,
    PharmacyDetailSerializer,
    PharmacistStaffSerializer
)


class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy'}, status=status.HTTP_200_OK)


class ReadinessCheckView(APIView):
    """Readiness check endpoint"""
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


class PharmacyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for pharmacy profiles
    Provides CRUD operations for pharmacies
    """
    queryset = Pharmacy.objects.all()
    serializer_class = PharmacySerializer

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return PharmacyDetailSerializer
        return PharmacySerializer

    @action(detail=True, methods=['get'])
    def staff(self, request, pk=None):
        """
        Get all staff members for a pharmacy
        GET /api/pharmacies/{id}/staff/
        """
        pharmacy = self.get_object()
        staff = pharmacy.staff.all()
        serializer = PharmacistStaffSerializer(staff, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search pharmacies by name or address
        GET /api/pharmacies/search/?q=keyword
        """
        query = request.query_params.get('q', '')
        if query:
            # Search by address or license number
            pharmacies = Pharmacy.objects.filter(
                Q(address__icontains=query) |
                Q(license_number__icontains=query)
            )
        else:
            pharmacies = Pharmacy.objects.all()

        serializer = self.get_serializer(pharmacies, many=True)
        return Response(serializer.data)


class PharmacistStaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for pharmacist staff
    Provides CRUD operations for staff members
    """
    queryset = PharmacistStaff.objects.all()
    serializer_class = PharmacistStaffSerializer

    def get_queryset(self):
        """Filter by pharmacy if pharmacy_pk is provided"""
        pharmacy_pk = self.kwargs.get('pharmacy_pk')
        if pharmacy_pk:
            return PharmacistStaff.objects.filter(pharmacy_id=pharmacy_pk)
        return PharmacistStaff.objects.all()

    def perform_create(self, serializer):
        """Create staff member with pharmacy from URL"""
        pharmacy_pk = self.kwargs.get('pharmacy_pk')
        if pharmacy_pk:
            try:
                pharmacy = Pharmacy.objects.get(pk=pharmacy_pk)
                serializer.save(pharmacy=pharmacy)
            except Pharmacy.DoesNotExist:
                return Response(
                    {'error': 'Pharmacy not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            serializer.save()

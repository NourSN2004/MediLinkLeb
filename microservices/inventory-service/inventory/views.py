"""
Inventory Service Views
Handles API endpoints for medicines and stock management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.models import Q, Sum
from datetime import date, timedelta
from .models import Medicine, PharmacyStock, StockTransaction
from .serializers import (
    MedicineSerializer,
    PharmacyStockSerializer,
    PharmacyStockListSerializer,
    StockTransactionSerializer
)


class MedicineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Medicine CRUD operations
    """
    queryset = Medicine.objects.filter(is_active=True)
    serializer_class = MedicineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter medicines by various criteria"""
        queryset = Medicine.objects.filter(is_active=True)

        # Search by name or generic name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(generic_name__icontains=search)
            )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by prescription requirement
        requires_prescription = self.request.query_params.get('requires_prescription')
        if requires_prescription:
            queryset = queryset.filter(requires_prescription=requires_prescription.lower() == 'true')

        return queryset.order_by('name')

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of all medicine categories"""
        categories = Medicine.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        return Response(list(categories))


class PharmacyStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PharmacyStock CRUD operations
    """
    queryset = PharmacyStock.objects.all()
    serializer_class = PharmacyStockSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return PharmacyStockListSerializer
        return PharmacyStockSerializer

    def get_queryset(self):
        """Filter stock by pharmacy, medicine, or status"""
        queryset = PharmacyStock.objects.select_related('medicine')

        # Filter by pharmacy
        pharmacy_id = self.request.query_params.get('pharmacy')
        if pharmacy_id:
            queryset = queryset.filter(pharmacy_id=pharmacy_id)

        # Filter by medicine
        medicine_id = self.request.query_params.get('medicine')
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)

        # Filter low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = [stock for stock in queryset if stock.is_low_stock()]

        return queryset.order_by('pharmacy_id', 'medicine__name')

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock items"""
        pharmacy_id = request.query_params.get('pharmacy')
        queryset = PharmacyStock.objects.select_related('medicine')

        if pharmacy_id:
            queryset = queryset.filter(pharmacy_id=pharmacy_id)

        low_stock_items = [stock for stock in queryset if stock.is_low_stock()]
        serializer = PharmacyStockListSerializer(low_stock_items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get medicines expiring within 30 days"""
        pharmacy_id = request.query_params.get('pharmacy')
        days = int(request.query_params.get('days', 30))

        expiry_threshold = date.today() + timedelta(days=days)
        queryset = PharmacyStock.objects.filter(
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=date.today()
        ).select_related('medicine')

        if pharmacy_id:
            queryset = queryset.filter(pharmacy_id=pharmacy_id)

        serializer = PharmacyStockListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired medicines"""
        pharmacy_id = request.query_params.get('pharmacy')
        queryset = PharmacyStock.objects.filter(
            expiry_date__lt=date.today()
        ).select_related('medicine')

        if pharmacy_id:
            queryset = queryset.filter(pharmacy_id=pharmacy_id)

        serializer = PharmacyStockListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        """Restock medicine"""
        stock = self.get_object()
        quantity = request.data.get('quantity', 0)

        if quantity <= 0:
            return Response(
                {'error': 'Quantity must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create transaction
        transaction = StockTransaction.objects.create(
            pharmacy_stock=stock,
            transaction_type=StockTransaction.TransactionType.PURCHASE,
            quantity_change=quantity,
            quantity_before=stock.quantity,
            quantity_after=stock.quantity + quantity,
            notes=request.data.get('notes', 'Restocked')
        )

        # Update stock
        stock.quantity += quantity
        stock.last_restocked_at = transaction.transaction_date
        stock.save()

        serializer = self.get_serializer(stock)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def sell(self, request, pk=None):
        """Record a sale"""
        stock = self.get_object()
        quantity = request.data.get('quantity', 0)

        if quantity <= 0:
            return Response(
                {'error': 'Quantity must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if stock.quantity < quantity:
            return Response(
                {'error': 'Insufficient stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create transaction
        transaction = StockTransaction.objects.create(
            pharmacy_stock=stock,
            transaction_type=StockTransaction.TransactionType.SALE,
            quantity_change=-quantity,
            quantity_before=stock.quantity,
            quantity_after=stock.quantity - quantity,
            prescription_id=request.data.get('prescription_id'),
            notes=request.data.get('notes', '')
        )

        # Update stock
        stock.quantity -= quantity
        stock.save()

        serializer = self.get_serializer(stock)
        return Response(serializer.data)


class StockTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StockTransaction operations
    """
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionSerializer

    def get_queryset(self):
        """Filter transactions"""
        queryset = StockTransaction.objects.select_related('pharmacy_stock__medicine')

        # Filter by pharmacy
        pharmacy_id = self.request.query_params.get('pharmacy')
        if pharmacy_id:
            queryset = queryset.filter(pharmacy_stock__pharmacy_id=pharmacy_id)

        # Filter by stock
        stock_id = self.request.query_params.get('stock')
        if stock_id:
            queryset = queryset.filter(pharmacy_stock_id=stock_id)

        # Filter by transaction type
        trans_type = self.request.query_params.get('type')
        if trans_type:
            queryset = queryset.filter(transaction_type=trans_type)

        return queryset.order_by('-transaction_date')


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

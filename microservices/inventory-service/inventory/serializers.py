"""
Inventory Service Serializers
Handles serialization for medicines and stock
"""
from rest_framework import serializers
from .models import Medicine, PharmacyStock, StockTransaction
import requests
from django.conf import settings


def get_pharmacy_info(pharmacy_id):
    """Fetch pharmacy information from Pharmacy Service"""
    try:
        response = requests.get(
            f"{settings.PHARMACY_SERVICE_URL}/api/pharmacies/{pharmacy_id}/",
            headers={'X-Service-Auth': settings.SERVICE_SECRET_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching pharmacy info: {e}")
    return None


class MedicineSerializer(serializers.ModelSerializer):
    """Serializer for Medicine model"""
    stock_count = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'manufacturer',
            'form', 'strength', 'description', 'category',
            'requires_prescription', 'base_price', 'is_active',
            'created_at', 'updated_at', 'stock_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_stock_count(self, obj):
        """Get total stock across all pharmacies"""
        return obj.stock_levels.aggregate(total=models.Sum('quantity'))['total'] or 0


class StockTransactionSerializer(serializers.ModelSerializer):
    """Serializer for stock transactions"""
    medicine_name = serializers.CharField(source='pharmacy_stock.medicine.name', read_only=True)

    class Meta:
        model = StockTransaction
        fields = [
            'id', 'pharmacy_stock', 'transaction_type',
            'quantity_change', 'quantity_before', 'quantity_after',
            'prescription_id', 'user_id', 'notes', 'transaction_date',
            'medicine_name'
        ]
        read_only_fields = ['transaction_date', 'quantity_before', 'quantity_after']

    def create(self, validated_data):
        """Create transaction and update stock"""
        pharmacy_stock = validated_data['pharmacy_stock']

        # Set before/after quantities
        validated_data['quantity_before'] = pharmacy_stock.quantity
        validated_data['quantity_after'] = pharmacy_stock.quantity + validated_data['quantity_change']

        # Update stock quantity
        pharmacy_stock.quantity = validated_data['quantity_after']
        pharmacy_stock.save()

        return super().create(validated_data)


class PharmacyStockSerializer(serializers.ModelSerializer):
    """Serializer for pharmacy stock with medicine details"""
    medicine_details = MedicineSerializer(source='medicine', read_only=True)
    pharmacy_info = serializers.SerializerMethodField()
    is_low_stock = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    recent_transactions = StockTransactionSerializer(source='transactions', many=True, read_only=True)

    class Meta:
        model = PharmacyStock
        fields = [
            'id', 'pharmacy_id', 'medicine', 'medicine_details',
            'quantity', 'reorder_level', 'max_stock_level',
            'batch_number', 'expiry_date', 'manufacturing_date',
            'selling_price', 'shelf_location',
            'is_low_stock', 'is_expiring_soon', 'is_expired', 'days_until_expiry',
            'last_restocked_at', 'created_at', 'updated_at',
            'pharmacy_info', 'recent_transactions'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_pharmacy_info(self, obj):
        """Fetch pharmacy details from Pharmacy Service"""
        return get_pharmacy_info(obj.pharmacy_id)

    def validate(self, data):
        """Validate stock data"""
        if data.get('quantity', 0) < 0:
            raise serializers.ValidationError({'quantity': 'Quantity cannot be negative'})

        if data.get('reorder_level', 0) < 0:
            raise serializers.ValidationError({'reorder_level': 'Reorder level cannot be negative'})

        return data


class PharmacyStockListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing stock"""
    medicine = serializers.SerializerMethodField()
    is_low_stock = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()

    class Meta:
        model = PharmacyStock
        fields = [
            'id', 'pharmacy_id', 'medicine',
            'quantity', 'reorder_level', 'expiry_date', 'batch_number',
            'selling_price', 'is_low_stock', 'is_expiring_soon'
        ]

    def get_medicine(self, obj):
        """Return medicine details as nested object"""
        return {
            'id': obj.medicine.id,
            'name': obj.medicine.name,
            'generic_name': obj.medicine.generic_name,
            'form': obj.medicine.form,
            'strength': obj.medicine.strength,
            'manufacturer': obj.medicine.manufacturer,
        }


# Import models for stock_count calculation
from django.db import models

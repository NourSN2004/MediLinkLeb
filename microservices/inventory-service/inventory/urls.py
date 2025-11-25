"""
Inventory Service URL Configuration
Defines API endpoints for medicines and stock
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicineViewSet,
    PharmacyStockViewSet,
    StockTransactionViewSet
)

# Main router
router = DefaultRouter()
router.register(r'medicines', MedicineViewSet, basename='medicine')
router.register(r'stock', PharmacyStockViewSet, basename='stock')
router.register(r'transactions', StockTransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]

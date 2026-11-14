from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrderItemViewSet, OrderViewSet, ProductViewSet, ShippingBoxViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"shipping-boxes", ShippingBoxViewSet, basename="shipping-box")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="order-item")

urlpatterns = [
    path("", include(router.urls)),
]

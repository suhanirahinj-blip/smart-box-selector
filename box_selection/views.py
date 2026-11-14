from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Order, OrderItem, Product, ShippingBox
from .services.box_selection import find_best_box_for_order
from .serializers import (
    OrderItemSerializer,
    OrderSerializer,
    ProductSerializer,
    ShippingBoxSerializer,
)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ShippingBoxViewSet(ModelViewSet):
    queryset = ShippingBox.objects.all()
    serializer_class = ShippingBoxSerializer


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.prefetch_related("items__product").all()
    serializer_class = OrderSerializer

    @staticmethod
    def _serialize_box(box):
        if box is None:
            return None

        return {
            "id": box.pk,
            "code": box.code,
            "dimensions": {
                "length_cm": str(box.internal_length_cm),
                "width_cm": str(box.internal_width_cm),
                "height_cm": str(box.internal_height_cm),
            },
            "max_weight_kg": str(box.max_weight_kg),
            "cost": str(box.cost),
            "currency": box.currency,
        }

    @staticmethod
    def _serialize_placement(placement):
        return {
            "product": {
                "id": placement.product_id,
                "name": placement.product_name,
                "dimensions": {
                    "length_cm": str(placement.length_cm),
                    "width_cm": str(placement.width_cm),
                    "height_cm": str(placement.height_cm),
                },
            },
            "coordinates": {
                "x": str(placement.x),
                "y": str(placement.y),
                "z": str(placement.z),
            },
        }

    @action(detail=True, methods=["get"], url_path="recommend-box")
    def recommend_box(self, request, pk=None):
        order = self.get_object()
        result = find_best_box_for_order(order)
        payload = dict(result)
        payload["box"] = self._serialize_box(result.get("box"))
        payload["placements"] = [
            self._serialize_placement(placement) for placement in result.get("placements", [])
        ]

        if payload.get("total_weight_kg") is not None:
            payload["total_weight_kg"] = str(payload["total_weight_kg"])
        if payload.get("box_cost") is not None:
            payload["box_cost"] = str(payload["box_cost"])

        if result["success"]:
            return Response(payload, status=status.HTTP_200_OK)

        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class OrderItemViewSet(ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "product").all()
    serializer_class = OrderItemSerializer

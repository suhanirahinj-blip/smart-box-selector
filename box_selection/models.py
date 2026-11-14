from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


POSITIVE_DECIMAL = Decimal("0.001")


class Product(models.Model):
    """Physical product definition used for packing calculations."""

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True)
    length_cm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    width_cm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    height_cm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        constraints = [
            models.CheckConstraint(check=models.Q(length_cm__gt=0), name="product_length_cm_positive"),
            models.CheckConstraint(check=models.Q(width_cm__gt=0), name="product_width_cm_positive"),
            models.CheckConstraint(check=models.Q(height_cm__gt=0), name="product_height_cm_positive"),
            models.CheckConstraint(check=models.Q(weight_kg__gt=0), name="product_weight_kg_positive"),
        ]

    def __str__(self):
        return self.name 


class ShippingBox(models.Model):
    """Shipping box template containing packing volume and cost information."""

    code = models.CharField(max_length=50, unique=True)
    internal_length_cm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    internal_width_cm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    internal_height_cm = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    max_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(POSITIVE_DECIMAL)],
    )
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(max_length=3, choices=[("INR", "INR")], default="INR")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["cost", "internal_length_cm", "internal_width_cm", "internal_height_cm"]
        verbose_name = "Shipping box"
        verbose_name_plural = "Shipping boxes"
        constraints = [
            models.CheckConstraint(check=models.Q(internal_length_cm__gt=0), name="shippingbox_internal_length_cm_positive"),
            models.CheckConstraint(check=models.Q(internal_width_cm__gt=0), name="shippingbox_internal_width_cm_positive"),
            models.CheckConstraint(check=models.Q(internal_height_cm__gt=0), name="shippingbox_internal_height_cm_positive"),
            models.CheckConstraint(check=models.Q(max_weight_kg__gt=0), name="shippingbox_max_weight_kg_positive"),
            models.CheckConstraint(check=models.Q(cost__gte=0), name="shippingbox_cost_non_negative"),
            models.CheckConstraint(check=models.Q(currency__in=["INR"]), name="shippingbox_currency_inr"),
        ]

    def __str__(self):
        return self.code


class Order(models.Model):
    """Customer order containing one or more line items."""

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    """Line item linking a product to an order with quantity."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "product"]
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        constraints = [
            models.CheckConstraint(check=models.Q(quantity__gt=0), name="orderitem_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity} ({self.order})"

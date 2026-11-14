from django.contrib import admin

from .models import Order, OrderItem, Product, ShippingBox


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "weight_kg", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("is_active",)


@admin.register(ShippingBox)
class ShippingBoxAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "max_weight_kg", "cost", "currency", "is_active")
    search_fields = ("code",)
    list_filter = ("is_active", "currency")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "order_number", "status", "created_at")
    search_fields = ("order_number",)
    list_filter = ("status", "created_at")
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity")
    search_fields = ("order__order_number", "product__name")
    list_filter = ("created_at",)
    autocomplete_fields = ("order", "product")
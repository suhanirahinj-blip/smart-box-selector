"""Deterministic greedy 3D box-selection heuristic for orders.

This module keeps the packing logic independent of DRF views and serializers.
It evaluates active shipping boxes for an order and returns the cheapest box
that can fit the complete set of expanded order items without overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations
from typing import Any, Iterable, Sequence

from ..models import Order, Product, ShippingBox

ZERO = Decimal("0")


@dataclass(frozen=True)
class Placement:
    """A successfully placed product inside a box."""

    product_id: int
    product_name: str
    x: Decimal
    y: Decimal
    z: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal


@dataclass(frozen=True)
class FreeSpace:
    """An axis-aligned free rectangular volume remaining in a box."""

    x: Decimal
    y: Decimal
    z: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal

    @property
    def volume(self) -> Decimal:
        return self.length_cm * self.width_cm * self.height_cm

    def is_valid(self) -> bool:
        return (
            self.length_cm > ZERO
            and self.width_cm > ZERO
            and self.height_cm > ZERO
            and self.x >= ZERO
            and self.y >= ZERO
            and self.z >= ZERO
        )

    def intersects(self, other: "FreeSpace") -> bool:
        return not (
            self.x + self.length_cm <= other.x
            or other.x + other.length_cm <= self.x
            or self.y + self.width_cm <= other.y
            or other.y + other.width_cm <= self.y
            or self.z + self.height_cm <= other.z
            or other.z + other.height_cm <= self.z
        )

    def contains(self, other: "FreeSpace") -> bool:
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.z <= other.z
            and self.x + self.length_cm >= other.x + other.length_cm
            and self.y + self.width_cm >= other.y + other.width_cm
            and self.z + self.height_cm >= other.z + other.height_cm
        )


def _product_volume(product: Product) -> Decimal:
    return product.length_cm * product.width_cm * product.height_cm


def _normalize_order_products(order: Order) -> list[Product]:
    """Expand each order item into individual product instances using quantity."""
    if not isinstance(order, Order):
        return []

    expanded_products: list[Product] = []
    order_items = order.items.select_related("product").all() if order.pk else []

    for item in order_items:
        if item.product is None:
            continue
        quantity = item.quantity or 0
        if quantity <= 0:
            continue
        expanded_products.extend([item.product] * int(quantity))

    expanded_products.sort(key=lambda product: _product_volume(product), reverse=True)
    return expanded_products


def _orientation_variants(product: Product) -> list[tuple[Decimal, Decimal, Decimal]]:
    """Return all six axis-aligned orientations for a rectangular product."""
    dimensions = [product.length_cm, product.width_cm, product.height_cm]
    variants: list[tuple[Decimal, Decimal, Decimal]] = []
    seen: set[tuple[Decimal, Decimal, Decimal]] = set()

    for orientation in permutations(dimensions):
        normalized = tuple(orientation)
        if normalized in seen:
            continue
        seen.add(normalized)
        variants.append(normalized)

    return variants


def _space_fits(space: FreeSpace, product_dims: tuple[Decimal, Decimal, Decimal]) -> bool:
    return (
        product_dims[0] <= space.length_cm
        and product_dims[1] <= space.width_cm
        and product_dims[2] <= space.height_cm
    )


def _placement_intersects_existing(
    placement: Placement,
    existing_placements: Sequence[Placement],
) -> bool:
    """Return True when the proposed placement intersects an already placed product."""
    placement_x_end = placement.x + placement.length_cm
    placement_y_end = placement.y + placement.width_cm
    placement_z_end = placement.z + placement.height_cm

    for existing in existing_placements:
        existing_x_end = existing.x + existing.length_cm
        existing_y_end = existing.y + existing.width_cm
        existing_z_end = existing.z + existing.height_cm

        if not (
            placement_x_end <= existing.x
            or existing_x_end <= placement.x
            or placement_y_end <= existing.y
            or existing_y_end <= placement.y
            or placement_z_end <= existing.z
            or existing_z_end <= placement.z
        ):
            return True

    return False


def _subtract_space_from_space(region: FreeSpace, obstacle: FreeSpace) -> list[FreeSpace]:
    """Return the non-overlapping remainder of a free space after subtracting an obstacle cuboid."""
    if not region.intersects(obstacle):
        return [region]

    x_start = max(region.x, obstacle.x)
    x_end = min(region.x + region.length_cm, obstacle.x + obstacle.length_cm)
    y_start = max(region.y, obstacle.y)
    y_end = min(region.y + region.width_cm, obstacle.y + obstacle.width_cm)
    z_start = max(region.z, obstacle.z)
    z_end = min(region.z + region.height_cm, obstacle.z + obstacle.height_cm)

    pieces: list[FreeSpace] = []

    if region.x < x_start:
        pieces.append(
            FreeSpace(
                x=region.x,
                y=region.y,
                z=region.z,
                length_cm=x_start - region.x,
                width_cm=region.width_cm,
                height_cm=region.height_cm,
            )
        )

    if x_end < region.x + region.length_cm:
        pieces.append(
            FreeSpace(
                x=x_end,
                y=region.y,
                z=region.z,
                length_cm=region.x + region.length_cm - x_end,
                width_cm=region.width_cm,
                height_cm=region.height_cm,
            )
        )

    if region.y < y_start:
        pieces.append(
            FreeSpace(
                x=x_start,
                y=region.y,
                z=region.z,
                length_cm=max(ZERO, x_end - x_start),
                width_cm=y_start - region.y,
                height_cm=region.height_cm,
            )
        )

    if y_end < region.y + region.width_cm:
        pieces.append(
            FreeSpace(
                x=x_start,
                y=y_end,
                z=region.z,
                length_cm=max(ZERO, x_end - x_start),
                width_cm=region.y + region.width_cm - y_end,
                height_cm=region.height_cm,
            )
        )

    if region.z < z_start:
        pieces.append(
            FreeSpace(
                x=x_start,
                y=y_start,
                z=region.z,
                length_cm=max(ZERO, x_end - x_start),
                width_cm=max(ZERO, y_end - y_start),
                height_cm=z_start - region.z,
            )
        )

    if z_end < region.z + region.height_cm:
        pieces.append(
            FreeSpace(
                x=x_start,
                y=y_start,
                z=z_end,
                length_cm=max(ZERO, x_end - x_start),
                width_cm=max(ZERO, y_end - y_start),
                height_cm=region.z + region.height_cm - z_end,
            )
        )

    return _prune_redundant_spaces(pieces)


def _prune_redundant_spaces(spaces: Iterable[FreeSpace]) -> list[FreeSpace]:
    """Drop invalid and fully redundant free spaces."""
    normalized: list[FreeSpace] = []
    items = list(spaces)

    for space in items:
        if not space.is_valid():
            continue
        if any(other is not space and other.contains(space) for other in items):
            continue
        normalized.append(space)

    return normalized


def _split_free_space(space: FreeSpace, product_dims: tuple[Decimal, Decimal, Decimal]) -> list[FreeSpace]:
    """Split a parent free space into three non-overlapping regions.

    A product of dimensions (length, width, height) placed at the origin of a
    free space yields three remaining regions:
    1. right: remaining length along x, full width and height
    2. behind: product length along x, remaining width along y, full height
    3. above: product length and width, remaining height along z
    """
    length_cm, width_cm, height_cm = product_dims

    candidates = [
        FreeSpace(
            x=space.x + length_cm,
            y=space.y,
            z=space.z,
            length_cm=space.length_cm - length_cm,
            width_cm=space.width_cm,
            height_cm=space.height_cm,
        ),
        FreeSpace(
            x=space.x,
            y=space.y + width_cm,
            z=space.z,
            length_cm=length_cm,
            width_cm=space.width_cm - width_cm,
            height_cm=space.height_cm,
        ),
        FreeSpace(
            x=space.x,
            y=space.y,
            z=space.z + height_cm,
            length_cm=length_cm,
            width_cm=width_cm,
            height_cm=space.height_cm - height_cm,
        ),
    ]

    valid_regions = [candidate for candidate in candidates if candidate.is_valid()]
    return _prune_redundant_spaces(valid_regions)


def _can_pack_products_in_box(box: ShippingBox, products: Sequence[Product]) -> tuple[bool, list[Placement]]:
    """Attempt to pack all products in this box using a deterministic greedy heuristic."""
    if not products:
        return True, []

    total_weight = sum((product.weight_kg for product in products), ZERO)
    if box.max_weight_kg < total_weight:
        return False, []

    remaining_spaces = [
        FreeSpace(
            x=ZERO,
            y=ZERO,
            z=ZERO,
            length_cm=box.internal_length_cm,
            width_cm=box.internal_width_cm,
            height_cm=box.internal_height_cm,
        )
    ]
    placed: list[Placement] = []

    for product in products:
        item_placed = False
        for orientation in _orientation_variants(product):
            for space in remaining_spaces:
                if not _space_fits(space, orientation):
                    continue

                placement = Placement(
                    product_id=product.pk,
                    product_name=product.name,
                    x=space.x,
                    y=space.y,
                    z=space.z,
                    length_cm=orientation[0],
                    width_cm=orientation[1],
                    height_cm=orientation[2],
                )

                if placement.x < ZERO:
                    continue
                if placement.y < ZERO:
                    continue
                if placement.z < ZERO:
                    continue
                if placement.x + placement.length_cm > box.internal_length_cm:
                    continue
                if placement.y + placement.width_cm > box.internal_width_cm:
                    continue
                if placement.z + placement.height_cm > box.internal_height_cm:
                    continue
                if _placement_intersects_existing(placement, placed):
                    continue

                placed.append(placement)

                product_block = FreeSpace(
                    x=space.x,
                    y=space.y,
                    z=space.z,
                    length_cm=orientation[0],
                    width_cm=orientation[1],
                    height_cm=orientation[2],
                )

                new_spaces: list[FreeSpace] = []
                for existing_space in remaining_spaces:
                    if existing_space is space:
                        new_spaces.extend(_split_free_space(existing_space, orientation))
                    else:
                        new_spaces.extend(_subtract_space_from_space(existing_space, product_block))

                remaining_spaces = _prune_redundant_spaces(new_spaces)
                item_placed = True
                break

            if item_placed:
                break

        if not item_placed:
            return False, []

    return True, placed


def find_best_box_for_order(order: Order) -> dict[str, Any]:
    """Return the cheapest feasible shipping box for an order, or a clear no-box result."""
    if not isinstance(order, Order):
        return {
            "success": False,
            "box": None,
            "reason": "Input must be an Order instance.",
            "placements": [],
            "total_weight_kg": ZERO,
            "box_cost": None,
            "currency": None,
        }

    if order.pk is None:
        return {
            "success": False,
            "box": None,
            "reason": "Order must be saved before box selection is evaluated.",
            "placements": [],
            "total_weight_kg": ZERO,
            "box_cost": None,
            "currency": None,
        }

    expanded_products = _normalize_order_products(order)
    if not expanded_products:
        return {
            "success": False,
            "box": None,
            "reason": "Order contains no valid products to pack.",
            "placements": [],
            "total_weight_kg": ZERO,
            "box_cost": None,
            "currency": None,
        }

    total_order_weight = sum((product.weight_kg for product in expanded_products), ZERO)
    candidate_boxes = ShippingBox.objects.filter(is_active=True).order_by(
        "cost",
        "internal_length_cm",
        "internal_width_cm",
        "internal_height_cm",
    )

    for box in candidate_boxes:
        if box.max_weight_kg < total_order_weight:
            continue

        packable, placements = _can_pack_products_in_box(box, expanded_products)
        if packable:
            return {
                "success": True,
                "box": box,
                "placements": placements,
                "total_weight_kg": total_order_weight,
                "box_cost": box.cost,
                "currency": box.currency,
                "reason": "Cheapest feasible box found.",
            }

    return {
        "success": False,
        "box": None,
        "reason": "No active shipping box can accommodate the complete order.",
        "placements": [],
        "total_weight_kg": total_order_weight,
        "box_cost": None,
        "currency": None,
    }

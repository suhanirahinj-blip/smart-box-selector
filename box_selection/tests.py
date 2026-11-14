from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Order, OrderItem, Product, ShippingBox
from .services.box_selection import find_best_box_for_order


class BoxSelectionTests(TestCase):
	def create_product(
		self,
		*,
		name="Test product",
		length="4.000",
		width="3.000",
		height="2.000",
		weight="1.000",
	):
		return Product.objects.create(
			name=name,
			length_cm=Decimal(length),
			width_cm=Decimal(width),
			height_cm=Decimal(height),
			weight_kg=Decimal(weight),
		)

	def create_order_with_product(self, product, *, quantity=1, order_number="ORDER-1"):
		order = Order.objects.create(order_number=order_number)
		OrderItem.objects.create(order=order, product=product, quantity=quantity)
		return order

	def create_box(
		self,
		*,
		code="BOX-1",
		length="5.000",
		width="5.000",
		height="5.000",
		max_weight="10.000",
		cost="12.30",
	):
		return ShippingBox.objects.create(
			code=code,
			internal_length_cm=Decimal(length),
			internal_width_cm=Decimal(width),
			internal_height_cm=Decimal(height),
			max_weight_kg=Decimal(max_weight),
			cost=Decimal(cost),
		)

	def test_successful_box_recommendation(self):
		product = self.create_product()
		order = self.create_order_with_product(product)
		box = self.create_box()

		result = find_best_box_for_order(order)

		self.assertTrue(result["success"])
		self.assertEqual(result["box"], box)
		self.assertEqual(result["total_weight_kg"], Decimal("1.000"))
		self.assertEqual(result["box_cost"], Decimal("12.30"))
		self.assertEqual(len(result["placements"]), 1)
		self.assertEqual(result["placements"][0].product_id, product.pk)

	def test_no_suitable_box_is_available(self):
		product = self.create_product(length="10.000", width="10.000", height="10.000")
		order = self.create_order_with_product(product)
		self.create_box(length="5.000", width="5.000", height="5.000")

		result = find_best_box_for_order(order)

		self.assertFalse(result["success"])
		self.assertIsNone(result["box"])
		self.assertEqual(result["placements"], [])
		self.assertEqual(result["reason"], "No active shipping box can accommodate the complete order.")

	def test_product_rotation_allows_a_fit(self):
		product = self.create_product(length="8.000", width="3.000", height="2.000")
		order = self.create_order_with_product(product)
		self.create_box(length="3.000", width="8.000", height="2.000")

		result = find_best_box_for_order(order)

		self.assertTrue(result["success"])
		placement = result["placements"][0]
		self.assertEqual(
			(placement.length_cm, placement.width_cm, placement.height_cm),
			(Decimal("3.000"), Decimal("8.000"), Decimal("2.000")),
		)

	def test_order_exceeding_box_maximum_weight_is_rejected(self):
		product = self.create_product(weight="2.500")
		order = self.create_order_with_product(product)
		self.create_box(max_weight="2.000")

		result = find_best_box_for_order(order)

		self.assertFalse(result["success"])
		self.assertIsNone(result["box"])
		self.assertEqual(result["total_weight_kg"], Decimal("2.500"))

	def test_cheapest_suitable_box_is_selected(self):
		product = self.create_product()
		order = self.create_order_with_product(product)
		self.create_box(code="BOX-EXPENSIVE", cost="20.00")
		cheaper_box = self.create_box(code="BOX-CHEAP", cost="4.50")

		result = find_best_box_for_order(order)

		self.assertTrue(result["success"])
		self.assertEqual(result["box"], cheaper_box)
		self.assertEqual(result["box_cost"], Decimal("4.50"))

	def test_recommendation_endpoint_returns_expected_response(self):
		product = self.create_product(weight="1.250")
		order = self.create_order_with_product(product)
		box = self.create_box()

		response = self.client.get(
			reverse("order-recommend-box", kwargs={"pk": order.pk})
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			response.json(),
			{
				"success": True,
				"box": {
					"id": box.pk,
					"code": "BOX-1",
					"dimensions": {
						"length_cm": "5.000",
						"width_cm": "5.000",
						"height_cm": "5.000",
					},
					"max_weight_kg": "10.000",
					"cost": "12.30",
					"currency": "INR",
				},
				"placements": [
					{
						"product": {
							"id": product.pk,
							"name": "Test product",
							"dimensions": {
								"length_cm": "4.000",
								"width_cm": "3.000",
								"height_cm": "2.000",
							},
						},
						"coordinates": {"x": "0", "y": "0", "z": "0"},
					}
				],
				"total_weight_kg": "1.250",
				"box_cost": "12.30",
				"currency": "INR",
				"reason": "Cheapest feasible box found.",
			},
		)

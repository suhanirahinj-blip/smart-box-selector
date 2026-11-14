# Smart Box Selector

Smart Box Selector is a Django REST Framework API for managing products, shipping boxes, and orders, and recommending a shipping box for an order.

## Overview

The system evaluates active shipping boxes against all product units in a saved order. It checks the combined product weight and attempts to place each item within the box's internal dimensions. When multiple boxes fit, it returns the feasible box with the lowest cost.

The packing implementation is a deterministic greedy 3D heuristic. It sorts product units by volume and tries axis-aligned rotations while placing items into available free spaces. It is an approximation, not a globally optimal solver, and it does not use a trained AI model.

## Features

- CRUD API for products, shipping boxes, orders, and order items.
- Box recommendations for individual orders, including selected box details and product placements.
- Product dimensions and box capacity represented in centimeters and kilograms.
- Order item quantities expanded into individual product units for packing.
- Active-box filtering and maximum-weight checks.
- Recommendation failures include a reason and return an HTTP 400 response.

## Technologies

- Python
- Django 5.2.19
- Django REST Framework 3.18.3
- SQLite, as configured by default in `config/settings.py`

Dependencies are listed in `requirements.txt`.

## Windows Setup

Open PowerShell in the project directory and create a virtual environment:

```powershell
py -m venv .venv
```

Activate it. If PowerShell blocks activation scripts, enable them for the current process first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Database and Server

Apply database migrations:

```powershell
python manage.py migrate
```

Start the development server:

```powershell
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`. Django admin is available at `http://127.0.0.1:8000/admin/`.

## API Endpoints

All API routes are under `/api/` and use trailing slashes. The CRUD routes are provided by Django REST Framework `ModelViewSet`s.

| Resource | Collection methods | Detail methods | Route |
| --- | --- | --- | --- |
| Products | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/products/`, `/api/products/{id}/` |
| Shipping boxes | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/shipping-boxes/`, `/api/shipping-boxes/{id}/` |
| Orders | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/orders/`, `/api/orders/{id}/` |
| Order items | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/order-items/`, `/api/order-items/{id}/` |

| Action | Method | Route |
| --- | --- | --- |
| Recommend a box for an order | `GET` | `/api/orders/{id}/recommend-box/` |

The recommendation action requires a saved order with order items and evaluates active shipping boxes. Shipping box currency is currently constrained to `INR` by the model.

## Box Recommendation Example

This request assumes order `42` already exists, contains at least one product, and there is at least one active box to evaluate. The action does not require a request body.

```http
GET /api/orders/42/recommend-box/ HTTP/1.1
Host: 127.0.0.1:8000
Accept: application/json
```

Successful response (`200 OK`):

```json
{
  "success": true,
  "box": {
    "id": 3,
    "code": "BX-SMALL",
    "dimensions": {
      "length_cm": "20.000",
      "width_cm": "15.000",
      "height_cm": "10.000"
    },
    "max_weight_kg": "5.000",
    "cost": "75.00",
    "currency": "INR"
  },
  "placements": [
    {
      "product": {
        "id": 8,
        "name": "Desk Organizer",
        "dimensions": {
          "length_cm": "10.000",
          "width_cm": "8.000",
          "height_cm": "4.000"
        }
      },
      "coordinates": {
        "x": "0",
        "y": "0",
        "z": "0"
      }
    }
  ],
  "total_weight_kg": "0.500",
  "box_cost": "75.00",
  "currency": "INR",
  "reason": "Cheapest feasible box found."
}
```

Decimal quantities are returned as strings to preserve precision. When no active box can accommodate the order, the action returns `400 Bad Request` with `success: false`, `box: null`, an empty `placements` list, and a reason.

## Automated Tests

Run the app's Django tests from the project directory:

```powershell
python manage.py test box_selection
```

The tests cover successful and unsuccessful recommendations, rotation, weight limits, cheapest suitable box selection, and the recommendation API response.
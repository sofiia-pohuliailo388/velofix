# VeloFix

A Django web application for managing a small bicycle repair shop. It keeps customers, bicycles, repair orders, services and spare parts in one place, so the shop does not lose agreements with customers, miss deadlines or forget the repair history of a bike.

**Demo login:** click **Log in as demo** on the login page, or use `demo` / `your-demo-password`
The demo database contains fictional data only.

## The problem

A small workshop usually runs on paper notes and chat messages. That leads to:

- lost agreements with customers;
- repairs that quietly pass their deadline;
- no history of what was done to a bicycle before;
- unclear scope of work and price.

VeloFix gives staff one workflow: accept a bike, describe the problem, build the list of services, move the order through its stages, and hand the bike back.

## Features

- **Customers**: create, edit, delete, search by name or phone, pagination. A customer can own several bicycles.
- **Bicycles**: brand, model, type, optional frame number (unique when filled in). Each bicycle has its own page with the full repair history.
- **Service catalog**: create, edit, archive and delete services. Archived services disappear from new orders but stay in old ones.
- **Repair orders**: created from a bicycle with the customer's complaint, the condition of the bike and a deadline.
  - Services are added from the catalog with a quantity. The price is **copied into the order line**, so later price changes never affect old orders.
  - The total is calculated in the database from the order lines.
  - Orders move through defined stages: accepted, diagnosis, in progress, ready for pickup, delivered, or cancelled.
- **Order list**: search by customer, brand, model or frame number (every word is matched separately), filter by status, "overdue only" filter, pagination that keeps the filters.
- **Dashboard**: active orders, overdue orders, bikes waiting for pickup, and parts that are low on stock.
- **Authentication**: all pages require login.

## Business rules

| Rule | How it is enforced |
|---|---|
| A customer or bicycle with history cannot be deleted | `on_delete=PROTECT`, and the view turns the error into a clear message |
| A service used in an order cannot be deleted, only archived | `PROTECT` plus an archive toggle |
| Old orders keep their prices | price snapshot in `OrderService.unit_price` |
| Work cannot start without at least one service | checked in `services.change_status` |
| Stages cannot be skipped | transition table in `models.py`, checked again on the server |
| Completion and delivery dates are set automatically | set when the status changes to ready or delivered |
| Closed orders (delivered or cancelled) cannot be edited | buttons hidden for closed orders |
| Frame numbers are unique only when filled in | conditional `UniqueConstraint` |
| Prices and quantities cannot be negative or zero | `CheckConstraint` plus form validation |

## Tech stack

- Python 3.12, Django
- SQLite 
- Bootstrap 5

## Data model

Eight main models plus one link table:

`Mechanic` (custom user), `Customer`, `Bicycle`, `Service`, `Part`, `RepairOrder`, `OrderService`, `OrderPart`, and `RepairOrderMechanic` (link table between orders and mechanics).

## Project structure

```
velofix/
├── config/            # settings, root urls
├── apps/
│   ├── accounts/      # Mechanic (custom user)
│   ├── customers/     # Customer, Bicycle
│   ├── catalog/       # Service, Part
│   ├── orders/        # RepairOrder and order lines, status rules (services.py)
│   └── dashboard/     # home page
├── templates/         # base layout, partials, one folder per app
├── fixtures/          # demo data
└── requirements/
```

Business rules for status changes live in `apps/orders/services.py`, so views stay thin.

## Run locally

```bash
git clone https://github.com/sofiia-pohuliailo388/velofix.git
cd velofix

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt

cp .env.example .env                 # then set SECRET_KEY
python manage.py migrate
python manage.py loaddata fixtures/demo_data.json
python manage.py createsuperuser
python manage.py runserver



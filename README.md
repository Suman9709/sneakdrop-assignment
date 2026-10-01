# SneakDrop

SneakDrop is a small, Docker-first limited sneaker drop application. It prevents overselling by reserving one of 20 pairs for five minutes, handles a FIFO waitlist, and processes an idempotent fake payment callback.

## Reviewer quick start

### Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- Git (only needed to clone the repository)

### Start the project

Clone the repository, open a terminal in the project directory, then run:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The first startup downloads images, installs frontend packages, applies migrations, seeds the limited sneaker, and creates the local demo user. Wait until the containers are healthy, then open:

| Service | URL |
| --- | --- |
| Customer application | http://localhost:3000 |
| Django admin | http://localhost:8000/admin/ |
| API inventory endpoint | http://localhost:8000/api/inventory/ |

## Demo login

Use these credentials in the application's **Sign in** page or in Django Admin:

```text
Username: admin
Password: Begusarai@1
```

These are intentionally public, local-development credentials only. They must be changed or disabled before any real deployment.

On a fresh database, Docker runs `python manage.py seed_demo_user` after migrations. The command creates `admin` only if it does not already exist, so it never overwrites an existing password.

## Reviewer walkthrough

1. Open http://localhost:3000 and confirm that the live stock count appears.
2. Click **Sign in** and use the demo credentials.
3. Click **Reserve one pair**. The backend atomically decrements available stock and sends you to the cart.
4. On **Cart**, confirm the live five-minute reservation timer. Refreshing the page keeps the local checkout state for that browser session.
5. Click **Continue to payment**.
6. Enter any valid-looking demo card number, for example `4242 4242 4242 4242`, plus any name, expiry date, and CVC. Card fields are never sent to the backend or stored.
7. Click **Pay and confirm order**. The fake payment endpoint marks the hold as paid and creates one order and payment event.
8. Return to the stock page and verify that inventory has decreased.

The application enforces one active hold at a time and a maximum of two paid pairs per user. If the demo `admin` user has already reached the limit, create another user in Django Admin and sign in with that account.

## Key behavior to inspect

- **Stock safety:** inventory-changing actions use database transactions and row locking.
- **Reservation expiry:** Celery Beat calls the expiry task every 15 seconds. Expired holds return stock and promote waiting users in FIFO order.
- **Waitlist:** when stock is zero, signed-in users can join the queue. A released pair creates a new five-minute hold for the first eligible user.
- **Payment idempotency:** `PaymentEvent.event_id` is unique, so duplicate payment-provider deliveries do not create duplicate orders.
- **Frontend:** React, React Router, and TanStack Query provide stock polling, cart state, countdown, login, reservation, waitlist, and demo payment screens.

## Useful commands

Run commands from the repository root.

```powershell
# Start in the background
docker compose up --build -d

# View all service logs
docker compose logs -f

# Run Django checks
docker compose exec backend python manage.py check

# Run frontend checks
docker compose exec frontend npm run lint
docker compose exec frontend npm run build

# Stop containers while retaining database data
docker compose down
```

## Database access with DataGrip

Use the PostgreSQL values in `.env`:

```text
Host: 127.0.0.1
Port: value of POSTGRES_EXPOSED_PORT (default: 5433)
Database: value of POSTGRES_DB
Username: value of POSTGRES_USER
Password: value of POSTGRES_PASSWORD
Schema: public
```

The main tables are `inventory_inventory`, `reservation_hold`, `waitlist_waitlistentry`, `orders_order`, and `payment_paymentevent`.

## Reset local demo data

This deletes all local PostgreSQL, Redis, and frontend dependency volume data:

```powershell
docker compose down -v
docker compose up --build
```

Use this only when you want a completely fresh local demo database. It cannot be undone.

# Ondo State Intelligent Logistics Platform — Backend API

A full-stack intelligent logistics system that standardises waybill pricing through machine learning and enables real-time parcel tracking for Ondo State, Nigeria.

Nigeria's informal logistics sector — the waybill system — operates with two core failures:

1. Pricing is entirely unregulated (a driver charges whatever they feel like)
2. Once a parcel is handed over at a motor park, it enters a black box

This platform solves both problems:

- ML-generated fair pricing that neither party can override
- Real-time GPS tracking visible to the sender throughout delivery

---

# Features

- Role-based authentication — Sender, Driver, and Admin roles with JWT tokens
- Driver OTP verification — Email OTP required before a driver can accept orders
- ML pricing engine — XGBoost model trained on real waybill transaction data; falls back to a deterministic baseline formula if model is not yet trained
- Enforced pricing — System sets the price. No negotiation. Driver sees it, sender pays it
- Order state machine — Strict status transitions:

```text
pending → accepted → picked_up → in_transit → delivered
```

- Real-time GPS tracking — Driver PWA sends GPS via REST; sender receives live updates via WebSocket
- Preloaded Ondo State routes — All known motor park routes seeded with coordinates and road risk levels
- Admin dashboard — Order volume, route activity, driver verification stats
- Email notifications — Order status updates sent to sender automatically

---

# Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend Framework | FastAPI (Python) | REST API + WebSocket server |
| Authentication | fastapi-users | JWT auth, registration, password reset |
| ORM | SQLAlchemy 2.0 async | Database models and queries |
| Migrations | Alembic | Database schema versioning |
| Primary Database | PostgreSQL via Supabase | Users, orders, routes |
| Cache | Redis | OTP storage with expiry |
| ML Model | XGBoost + Scikit-learn | Price prediction |
| ML Serialisation | Joblib | Save and load trained pipeline |
| Email | fastapi-mail | OTP and notification emails |
| Real-time | WebSocket FastAPI | Live driver GPS to sender |
| Data Processing | Pandas + NumPy | ML feature engineering |
| Distance API | Google Maps Distance Matrix | Route distance enrichment |

---

# Project Structure

```text
.

├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── route.py
│   │   └── pricing_record.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── pricing.py
│   │   ├── tracking.py
│   │   ├── route.py
│   │   ├── admin.py
│   │   └── otp.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── orders.py
│   │   ├── pricing.py
│   │   ├── tracking.py
│   │   ├── routes.py
│   │   ├── admin.py
│   │   └── deps.py
│   ├── services/
│   │   ├── otp_service.py
│   │   ├── order_service.py
│   │   ├── pricing_service.py
│   │   ├── route_service.py
│   │   ├── tracking_service.py
│   │   └── admin_service.py
│   ├── core/
│   │   ├── users.py
│   │   ├── email.py
│   │   ├── otp.py
│   │   ├── redis.py
│   │   └── ws_manager.py
│   └── ml/
│       ├── baseline.py
│       ├── feature_engineering.py
│       ├── predictor.py
│       ├── train.py
│       ├── evaluate.py
│       ├── dummy_data.py
│       └── data_collection/
│           ├── pipeline.py
│           ├── scraper.py
│           └── distance_enrichment.py
│
├── scripts/
│   ├── seed_routes.py
│   └── run_pipeline.py
│
├── trained_models/
│   └── pricing_pipeline.joblib
│
├── data/
│   ├── dummy_waybill_data.csv
│   └── waybill_pricing_clean.csv
│
├── alembic/
├── alembic.ini
├── .env
└── requirements.txt
```

---

# Prerequisites

- Python 3.11+
- PostgreSQL (or a Supabase project)
- Redis (local or Redis Cloud)
- Google Maps API key (Distance Matrix API enabled)
- Gmail account with App Password enabled

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/your-username/ondo-logistics-api.git

cd ondo-logistics-api
```

## 2. Create and activate virtual environment

```bash
python -m venv venv

source venv/bin/activate

# Windows
venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] \
    fastapi-users[sqlalchemy] fastapi-mail python-multipart \
    xgboost scikit-learn pandas joblib numpy \
    httpx beautifulsoup4 requests \
    redis python-dotenv websockets
```

## 4. Create your `.env` file

```bash
cp .env.example .env
```

Fill in all values — see Environment Variables section below.

## 5. Run database migrations

```bash
alembic upgrade head
```

## 6. Seed Ondo State routes

```bash
python -m scripts.seed_routes
```

## 7. Generate dummy data and train the model

```bash
python -m app.ml.dummy_data

python -m scripts.run_pipeline --survey data/dummy_waybill_data.csv
```

## 8. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at:

```text
http://localhost:8000/docs
```

---

# Environment Variables

| Variable | Description | Example |
|---|---|---|
| DATABASE_URL | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| JWT_SECRET | Secret for signing JWT tokens | `your-long-random-secret` |
| RESET_PASSWORD_SECRET | Secret for password reset tokens | `another-random-secret` |
| VERIFICATION_SECRET | Secret for email verification tokens | `yet-another-secret` |
| GOOGLE_MAPS_API_KEY | Google Maps Distance Matrix API key | `AIza...` |
| MAIL_USERNAME | Gmail address | `yourapp@gmail.com` |
| MAIL_PASSWORD | Gmail App Password not account password | `xxxx xxxx xxxx xxxx` |
| MAIL_FROM | From address shown in emails | `yourapp@gmail.com` |
| MAIL_PORT | SMTP port | `587` |
| MAIL_SERVER | SMTP server | `smtp.gmail.com` |
| MAIL_STARTTLS | Use STARTTLS | `true` |
| MAIL_SSL_TLS | Use SSL/TLS | `false` |
| REDIS_URL | Redis connection string | `redis://localhost:6379/0` |
| ML_MODEL_PATH | Path to trained joblib file | `trained_models/pricing_pipeline.joblib` |
| OTP_EXPIRY_SECONDS | OTP validity window in seconds | `600` |
| FRONTEND_URL | Frontend origin for CORS | `http://localhost:5173` |

---

# Running the Application

## Development

```bash
uvicorn app.main:app --reload --port 8000
```

## Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "healthy",
  "ml_model": "loaded"
}
```

---

# ML Pipeline

The ML system runs entirely on your laptop before deployment. The server only loads the trained model — it never trains anything.

## The Two Worlds

```text
LAPTOP (runs once)                     SERVER (runs forever)

──────────────────                     ─────────────────────

python -m app.ml.dummy_data            uvicorn app.main:app

python -m scripts.seed_routes               |

python -m scripts.run_pipeline              | loads .joblib at startup

        |                                   |

        v                                   v

trained_models/                        pricing_predictor.predict()

  pricing_pipeline.joblib  ─────────►  returns price per request
```

---

# Package Size Options

| Option | Description | Volume estimate |
|---|---|---|
| envelope | Flat, fits in one hand | 2,625 cm3 |
| small | Fits on your lap, shoebox size | 30,000 cm3 |
| medium | Needs both hands, microwave-sized | 70,000 cm3 |
| large | Needs two people, TV or big carton | 175,000 cm3 |
| extra_large | Multiple cartons, bulk load | 360,000 cm3 |

---

# Package Weight Options

| Option | Description | Estimate |
|---|---|---|
| very_light | Like holding a phone or book | 1 kg |
| light | Like a laptop bag | 3.5 kg |
| medium | Like a bag of rice, carry with one hand | 10 kg |
| heavy | Needs both hands, it is a struggle | 22 kg |
| very_heavy | Cannot carry alone | 40 kg |

---

# Step 1 — Generate Dummy Data

```bash
python -m app.ml.dummy_data
```

Output:

```text
data/dummy_waybill_data.csv (300 records)
```

Run once. Thrown away when real survey data arrives.

---

# Step 2 — Seed Routes Into Database

```bash
python -m scripts.seed_routes
```

Seeds 14 Ondo State routes with coordinates and risk levels.

Run once. Re-run only if you add new routes.

---

# Step 3 — Train the Model

```bash
python -m scripts.run_pipeline --survey data/dummy_waybill_data.csv
```

Output:

```text
trained_models/pricing_pipeline.joblib
```

---

# Step 4 — Retrain With Real Field Survey Data

```bash
python -m scripts.run_pipeline --survey data/field_survey.csv
```

Same command, real data.

- New `.joblib` replaces the dummy one
- Deploy updated `.joblib` to server

---

# Example Training Output

```text
========== STEP 1: BUILD DATASET ==========

Loading field survey data...

  Field records: 300

Loading published price benchmarks...

  Published records: 18

Combined: 318 records

Distance enrichment completed: 318 rows

Final clean dataset: 312 records

========== STEP 2: TRAIN MODEL ==========

CV RMSE: 412.33 (+/- 89.22)

CV MAE:  298.17 (+/- 45.11)

===== MODEL COMPARISON =====

Metric     XGBoost         Baseline        ML Wins?

RMSE       412.33          698.45          YES

MAE        298.17          521.33          YES

ML improves MAE by 42.8% over baseline

========== DONE ==========

Model saved to: trained_models/pricing_pipeline.joblib
```

The MAE and RMSE numbers go into Chapter 4 of the project report.

---

# What Each ML File Does

| File | Purpose | When it runs |
|---|---|---|
| baseline.py | Deterministic price formula | Every price request on server |
| feature_engineering.py | Convert words to numbers | Training only, on laptop |
| predictor.py | Load model and serve predictions | Every price request on server |
| train.py | Train XGBoost, save .joblib | Training only, on laptop |
| evaluate.py | Compare ML vs baseline, print table | Training only, on laptop |
| dummy_data.py | Generate fake survey records | Once, already done |
| data_collection/pipeline.py | Build master dataset from all sources | Training only, on laptop |
| data_collection/scraper.py | Published price table from blogs | Training only, on laptop |
| data_collection/distance_enrichment.py | Google Maps distance lookup | Training only, on laptop |

---

# API Endpoints

# Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | None | Register sender, driver, or admin |
| POST | `/auth/jwt/login` | None | Login, returns JWT token |
| POST | `/auth/otp/request` | None | Request OTP email, drivers only |
| POST | `/auth/otp/verify` | None | Verify OTP to activate driver account |
| POST | `/auth/forgot-password` | None | Request password reset email |
| POST | `/auth/reset-password` | None | Reset password with token |
| GET | `/users/me` | JWT | Get current user profile |
| PATCH | `/users/me` | JWT | Update profile |

## Register Body

```json
{
  "email": "john@example.com",
  "password": "strongpassword",
  "full_name": "John Doe",
  "phone": "+2348012345678",
  "role": "sender"
}
```

## Login Response

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

# Routes

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/routes/origins` | None | All available origin parks |
| GET | `/routes/destinations?origin=...` | None | Destinations from a given origin |
| GET | `/routes` | None | All routes |
| POST | `/routes` | Admin | Add a new route |
| PATCH | `/routes/{id}/risk?risk_level=3` | Admin | Update route risk level |

## Origins Response

```json
[
  "Ondo Garage Akure",
  "South Gate Akure",
  "Ondo Town Park",
  "Owo Park",
  "Ikare Park"
]
```

## Destinations Response

```json
[
  {
    "id": "uuid",
    "origin": "Ondo Garage Akure",
    "destination": "Lagos",
    "origin_lat": 7.2526,
    "origin_lng": 5.2103,
    "destination_lat": 6.5244,
    "destination_lng": 3.3792,
    "distance_km": 311.0,
    "estimated_duration_mins": 270,
    "risk_level": 2
  }
]
```

---

# Pricing

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/pricing/quick-quote` | None | Price estimate, no login required |

## Request

```json
{
  "origin_park": "Ondo Garage Akure",
  "destination": "Lagos",
  "package_size": "medium",
  "package_weight": "light",
  "vehicle_type": "small_car"
}
```

## Response

```json
{
  "origin": "Ondo Garage Akure",
  "destination": "Lagos",
  "distance_km": 311.0,
  "estimated_duration_mins": 270,
  "price": 8500.00
}
```

---

# Orders

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/orders` | Sender | Create a new order |
| GET | `/orders/my` | JWT | My orders, role-aware |
| GET | `/orders/available` | Verified Driver | Pending orders available to accept |
| GET | `/orders/track/{waybill}` | None | Track by waybill number, public |
| GET | `/orders/{id}` | JWT | Get single order |
| PATCH | `/orders/{id}/status` | JWT | Update order status |

## Create Order Request

```json
{
  "package_description": "Bag of clothes",
  "package_size": "medium",
  "package_weight": "light",
  "origin_park": "Ondo Garage Akure",
  "destination": "Lagos",
  "vehicle_type": "small_car",
  "recipient_name": "Jane Doe",
  "recipient_phone": "+2348098765432",
  "day_of_week": 4,
  "is_festive_period": false,
  "fuel_price_per_litre": 700
}
```

## Order Response

```json
{
  "id": "uuid",
  "waybill_number": "OND-12345678",
  "price": 8500.00,
  "status": "pending",
  "origin_lat": 7.2526,
  "origin_lng": 5.2103,
  "destination_lat": 6.5244,
  "destination_lng": 3.3792,
  "distance_km": 311.0,
  "estimated_duration_mins": 270
}
```

## Status Update

```json
{
  "status": "accepted"
}
```

---

# Order Status State Machine

```text
[PENDING] ──── Driver accepts ──────────────► [ACCEPTED]
                                                   |
                                         Driver picks up parcel
                                                   |
                                                   v
                                             [PICKED_UP]
                                                   |
                                           Driver starts journey
                                                   |
                                                   v
                                             [IN_TRANSIT]
                                                   |
                                           Driver delivers parcel
                                                   |
                                                   v
                                             [DELIVERED]

[PENDING] or [ACCEPTED] ── cancelled ──► [CANCELLED]
```

| Transition | Who can do it |
|---|---|
| pending → accepted | Verified driver only |
| accepted → picked_up | Assigned driver only |
| picked_up → in_transit | Assigned driver only |
| in_transit → delivered | Assigned driver only |
| pending → cancelled | Sender of that order or Admin |
| accepted → cancelled | Assigned driver or Admin |

---

# Tracking

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/tracking/update` | Verified Driver | Driver sends GPS coordinates |
| WS | `/tracking/ws/{order_id}` | None | Sender listens for live location |
| DELETE | `/tracking/live/{order_id}` | Verified Driver | Clear GPS data on delivery |

## GPS Update Body

```json
{
  "order_id": "uuid",
  "latitude": 7.2480,
  "longitude": 5.2050,
  "accuracy": 15.0,
  "timestamp": 1234567890
}
```

## WebSocket Message Received By Sender

```json
{
  "driver_id": "uuid",
  "lat": 7.2480,
  "lng": 5.2050,
  "accuracy": 15.0,
  "updated_at": 1234567890
}
```

GPS data lives in server memory only. Not stored in any database table.

---

# Admin

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/admin/dashboard` | Admin | Platform stats |
| GET | `/admin/order-volume?days=30` | Admin | Order count over time |
| GET | `/admin/route-activity?limit=10` | Admin | Top routes by order count |

---

# WebSocket Documentation

## Sender Connects To Receive Live Location

```javascript
const ws = new WebSocket(`wss://your-api.com/tracking/ws/${orderId}`);

ws.onopen = () => console.log("Tracking connected");

ws.onmessage = (event) => {
  const { lat, lng, updated_at } = JSON.parse(event.data);

  updateMapMarker(lat, lng);
};

ws.onclose = () => {
  // Reconnect after 3 seconds
  setTimeout(() => connect(), 3000);
};
```

## Driver Sends GPS From PWA Browser

```javascript
navigator.geolocation.watchPosition(async (position) => {
  await fetch(`${API_URL}/tracking/update`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      order_id: orderId,
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      timestamp: Date.now()
    })
  });
});
```

---

# Full Tracking Flow

```text
Driver phone GPS
      |
      |  POST /tracking/update every 60 seconds
      v

FastAPI server

  stores in memory (TrackingManager dictionary)

  broadcasts to all WebSockets watching this order

      |
      |  WebSocket push, instant
      v

Sender browser

  map marker moves to new position
```

---

# Deployment

## Backend — Render (Free Tier)

1. Push code to GitHub and include:

```text
trained_models/pricing_pipeline.joblib
```

2. Create a new Web Service on Render

3. Set build command:

```bash
pip install -r requirements.txt && alembic upgrade head
```

4. Set start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Add all environment variables from the table above

6. Deploy

7. Run:

```bash
python -m scripts.seed_routes
```

once via Render shell after first deploy.

---

## Frontend — Vercel

Set these environment variables in the Vercel dashboard:

```env
VITE_API_URL=https://your-app.onrender.com

VITE_WS_URL=wss://your-app.onrender.com
```

---

## Database — Supabase

1. Create a new Supabase project
2. Copy the connection string under:

```text
Settings > Database > Session mode port 5432
```

3. Prefix with:

```text
postgresql+asyncpg://
```

in your `DATABASE_URL`.

---

## Redis — Redis Cloud

1. Create a free database at Redis Cloud
2. Copy the connection string into `REDIS_URL`

---

# Deployment Cost

| Component | Platform | Cost |
|---|---|---|
| FastAPI Backend | Render | Free |
| React Frontend | Vercel | Free |
| PostgreSQL | Supabase | Free |
| Redis | Redis Cloud | Free |

## Total

```text
Zero
```

---

# Adding New Routes

No code change needed. Admin posts to the API:

```http
POST /routes

Authorization: Bearer <admin_token>

Content-Type: application/json
```

```json
{
  "origin": "Ondo Garage Akure",
  "destination": "Ile-Ife",
  "origin_lat": 7.2526,
  "origin_lng": 5.2103,
  "destination_lat": 7.4762,
  "destination_lng": 4.5600,
  "distance_km": 112.0,
  "estimated_duration_mins": 120,
  "risk_level": 2
}
```

To get coordinates:

1. Open Google Maps
2. Search the location
3. Right-click the pin
4. Copy the lat/lng values shown

---

# Academic Project Notes

## ML Model Evaluation

The `run_pipeline.py` script prints a comparison table showing XGBoost RMSE and MAE against the deterministic baseline formula.

These numbers go directly into Chapter 4 of the project report as evidence of model performance.

---

## If Fewer Than 200 Survey Records Are Collected

The baseline formula will likely perform comparably to XGBoost.

This is an acceptable outcome.

The report states that with limited data:

- the deterministic model is competitive
- the ML model is expected to improve as more transaction data is collected over time

The system ships with the baseline as automatic fallback regardless.

---

## Defense Demonstration

The system runs entirely on free-tier platforms.

The live demo URL is stable for the defense date at zero cost.

---

# License

MIT License
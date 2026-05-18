# Deployment Guide
## Sales & Marketing Performance Tracking System

---

## Option 1 — Local Development (Recommended for Demo)

### Prerequisites
- Python 3.10 or higher
- Git

### Steps

1. Clone the repository:
```bash
git clone https://github.com/saakshi2014/sales-marketing-tracker.git
cd sales-marketing-tracker
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install packages:
```bash
pip install -r backend/requirements.txt
```

4. Add your Firebase credentials:
   - Download `firebase-service-account.json` from Firebase Console
   - Place it in the project root
   - Create `.env` file with your Firebase config

5. Seed initial data:
```bash
python backend/seed_all.py
python backend/seed_demo_data.py
```

6. Run the app:
```bash
cd backend
python app.py
```

7. Open browser: `http://127.0.0.1:5000`

---

## Option 2 — Docker (On-Premises)

### Prerequisites
- Docker Desktop installed
- Use home WiFi (not college/office network — TLS issues)

### Steps

1. Make sure `.env` and `firebase-service-account.json` are in root

2. Build and run:
```bash
docker compose up --build
```

3. Open browser: `http://localhost:5000`

4. To stop:
```bash
docker compose down
```

---

## Environment Variables (.env)
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Employee | employee@test.com | Test@1234 |
| M1 Manager | m1manager@test.com | Test@1234 |
| M2 Manager | m2manager@test.com | Test@1234 |

---

## Running Tests

```bash
python backend/tests/test_all.py
```

Expected output: 33/33 PASS

---

## Firestore Security Notes

- Test mode rules: expire after 30 days from first creation
- Production rules: deployed in Sprint 3 (Day 20)
- Rules file: available in Firebase Console under Firestore → Rules

---

## Known Issues

1. Docker TLS error on restricted networks
   - Workaround: Use home WiFi or mobile hotspot for Docker builds

2. Firestore test mode expiry
   - Workaround: Production security rules deployed in Sprint 3

3. Clock sync required
   - If you see "Token used too early" error
   - Fix: Sync Windows clock (Settings → Time & Language → Sync now)
# WorkSphere HR — Enterprise HRMS Platform

> A fully production-ready Human Resource Management System built with Django, PostgreSQL, Redis, Celery, and Flutter.

---

## 🚀 Quick Start (Docker)

```bash
# 1. Clone / extract project
cd worksphere_hr

# 2. Copy environment file
cp .env.example .env
# Edit .env with your values (especially SECRET_KEY and DB_PASSWORD)

# 3. Start everything
docker-compose up -d

# 4. Access the platform
# Web Admin:   http://localhost:80
# Django App:  http://localhost:8000
# API Docs:    http://localhost:8000/api/docs/
# Flower:      http://localhost:5555
```

**Demo Credentials:**
| Role        | Email                        | Password   |
|-------------|------------------------------|------------|
| Super Admin | admin@worksphere.hr          | Admin@123  |
| HR Admin    | hr@worksphere.hr             | Admin@123  |
| Manager     | manager@worksphere.hr        | Mgr@123    |
| Employee    | employee@worksphere.hr       | Emp@123    |
| Payroll     | payroll@worksphere.hr        | Pay@123    |

---

## 📋 Features

### Core Modules
- ✅ **Employee Management** — Full employee lifecycle, documents, org chart
- ✅ **Attendance Management** — Web + Mobile clock-in/out, GPS, selfie, geo-fencing
- ✅ **Leave Management** — Multi-level approval, 8+ leave types, holiday calendar
- ✅ **Payroll Processing** — Indian-compliant, PF/ESI/PT/TDS, PDF payslips
- ✅ **Shift Management** — General/Morning/Night/Rotational, swap requests
- ✅ **Self Service Portal** — Profile, documents, payslips, leave balance
- ✅ **On Duty (OD)** — Client visits, business travel with approval workflow
- ✅ **Short Time Off** — Minute/hour-level leave management
- ✅ **Reports & Analytics** — Attendance trends, payroll cost, department charts
- ✅ **Notifications** — Email, in-app, push notifications
- ✅ **Role-Based Access** — 6 roles with granular permissions
- ✅ **Audit Logging** — All write actions logged with IP/user-agent
- ✅ **Dark Mode** — Full dark theme support

### Mobile App (Flutter)
- ✅ Camera-based selfie at clock-in/clock-out
- ✅ GPS location capture and geo-fence validation
- ✅ Biometric authentication (Face ID / Fingerprint)
- ✅ Push notifications via Firebase
- ✅ Offline mode support
- ✅ Android + iOS

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│                    Nginx (Port 80/443)           │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│           Django + Gunicorn (Port 8000)         │
│  ┌────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Web UI    │ │  REST APIs  │ │  Admin     │ │
│  │ (Bootstrap)│ │  (DRF+JWT) │ │ (Django)   │ │
│  └────────────┘ └─────────────┘ └────────────┘ │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌────▼───┐
│  PG   │ │ Redis │ │Celery  │
│  DB   │ │ Cache │ │Workers │
└───────┘ └───────┘ └────────┘
```

---

## 📁 Project Structure

```
worksphere_hr/
├── apps/
│   ├── authentication/     # JWT auth, user management
│   ├── employees/          # Employee CRUD, departments
│   ├── attendance/         # Clock-in/out, GPS, regularization
│   ├── leave_management/   # Leave types, applications, balances
│   ├── payroll/            # Salary, payslips, statutory
│   ├── shifts/             # Shift creation and assignment
│   ├── notifications/      # Email, push, in-app notifications
│   ├── reports/            # Reports and analytics
│   ├── dashboard/          # Dashboard views and context
│   └── audit/              # Audit trail
├── mobile/                 # Flutter mobile app
│   └── lib/
│       ├── screens/
│       ├── services/
│       ├── widgets/
│       └── utils/
├── templates/              # Django HTML templates
├── static/                 # CSS, JS, images
├── nginx/                  # Nginx config
├── docker-compose.yml
├── Dockerfile
├── gunicorn.conf.py
├── requirements.txt
└── manage.py
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | `False` |
| `DB_NAME` | PostgreSQL database | `worksphere_hr` |
| `DB_PASSWORD` | PostgreSQL password | (required) |
| `REDIS_PASSWORD` | Redis password | (required) |
| `EMAIL_HOST` | SMTP host | — |
| `COMPANY_NAME` | Company branding | `WorkSphere HR` |
| `TIME_ZONE` | Timezone | `Asia/Kolkata` |

---

## 📱 Mobile App Setup

Install Flutter 3.10 or newer with the Android SDK and run these commands from the repository root:

```bash
cd mobile
flutter create --platforms=android .
flutter pub get

# Android emulator. 10.0.2.2 points to the host machine.
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Physical Android device on the same network as the computer.
flutter run --dart-define=API_BASE_URL=http://YOUR_COMPUTER_IP:8000

# Build release APK for production.
flutter build apk --release --dart-define=API_BASE_URL=https://your-domain.com

# The generated APK is at:
# build/app/outputs/flutter-apk/app-release.apk
```

For a physical device, add its computer IP to `ALLOWED_HOSTS` in `.env`, then restart Django. Start the backend with:

```bash
python manage.py runserver 0.0.0.0:8000
```

**Required Permissions (AndroidManifest.xml):**
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.USE_BIOMETRIC" />
```

---

## 🔌 API Documentation

Full Swagger UI: `http://your-domain/api/docs/`

### Key Endpoints

```
POST   /api/v1/auth/login/              → JWT login
POST   /api/v1/auth/token/refresh/      → Refresh token
GET    /api/v1/auth/profile/            → Current user profile

GET    /api/v1/employees/               → Employee list
POST   /api/v1/employees/               → Create employee
GET    /api/v1/employees/{id}/          → Employee details

POST   /api/v1/attendance/clock-in/     → Clock in (GPS + selfie)
POST   /api/v1/attendance/clock-out/    → Clock out
GET    /api/v1/attendance/today/        → Today's record
GET    /api/v1/attendance/monthly_summary/ → Monthly stats

GET    /api/v1/leave/                   → Leave applications
POST   /api/v1/leave/                   → Apply leave
PATCH  /api/v1/leave/{id}/approve/      → Approve leave
```

---

## 🔐 Security

- JWT authentication with refresh token rotation
- Account lockout after 5 failed login attempts (30 min lock)
- Password hashing with Django's PBKDF2-SHA256
- HTTPS enforced in production (Nginx)
- Rate limiting: 60 req/min API, 5 req/min login
- Audit logging for all write operations
- Geo-fence validation for attendance
- Role-based access control (RBAC)

---

## 📊 Indian Compliance

- **PF**: 12% employee + 12% employer (capped ₹15,000 basic)
- **ESI**: 0.75% employee + 3.25% employer (wages ≤ ₹21,000)
- **Professional Tax**: State-wise slabs
- **TDS**: New vs Old tax regime selection
- **Labour Welfare Fund**: State-wise deduction
- **UAN/PF/ESI** number management

---

## 🚢 Production Deployment

```bash
# 1. Update .env
SECRET_KEY=<50+ char random string>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_PASSWORD=<strong password>
REDIS_PASSWORD=<strong password>

# 2. Add SSL certificates
mkdir nginx/ssl
# Place cert.pem and key.pem in nginx/ssl/

# 3. Deploy
docker-compose -f docker-compose.yml up -d --build

# 4. Create superuser (if needed)
docker-compose exec django python manage.py createsuperuser
```

---

## 🧪 Running Tests

```bash
# Inside container
docker-compose exec django pytest --cov=apps --cov-report=html -v

# Locally
pip install -r requirements.txt
pytest tests/ -v
```

---

## 📞 Support

- Email: support@worksphere.hr
- Docs: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

---

*WorkSphere HR v1.0 — Enterprise HRMS for Indian Organizations*

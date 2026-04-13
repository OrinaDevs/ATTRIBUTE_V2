# Attribute Land Survey & Consultants — Django Portal

A full-featured client & staff management portal for a land survey and consultancy firm.

---

## Features

### Client Portal
- Register / login with email & password
- Browse services with descriptions and pricing
- Request custom quotations for any service
- View quotation status (Pending → Under Review → Awaiting Response)
- Accept or reject reviewed quotations
- On acceptance: Client profile created + Invoice generated automatically
- Make & confirm payment (M-PESA / Bank reference entry)
- Download invoice as PDF
- Track project progress stage-by-stage in real time
- Download public project documents

### Staff Dashboard (OTP-protected)
- Two-factor login: password → 6-digit OTP sent to email
- Review incoming quotations — set quoted amount, notes, and status
- Manage assigned projects — update stage status and notes
- View all clients and their project summaries
- Admin sees everything; staff sees only their assignments

### Admin (Django Admin Panel)
- Full CRUD for users, services, service categories
- Assign clients to staff
- Manage invoices and payments
- Inline project stage management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | Custom AbstractUser + email login |
| 2FA | Console/SMTP OTP (6-digit, 10-min expiry) |
| PDF | ReportLab |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Forms | django-crispy-forms + crispy-bootstrap5 |

---

## Quick Start

### Requirements
- Python 3.10+
- pip

### Option A — Automated setup (Linux/macOS)

```bash
git clone <repo> attribute_survey
cd attribute_survey
bash setup.sh
```

### Option B — Manual setup (Windows / any OS)

```bash
# 1. Clone / extract project
cd attribute_survey

# 2. Create & activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Seed demo data
python manage.py seed_data

# 6. Run server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## Demo Accounts

| Role | Email | Password | Notes |
|---|---|---|---|
| Admin | admin@attributesurvey.co.ke | admin1234 | Full access. Also has Django `/admin/` |
| Staff | staff@attributesurvey.co.ke | staff1234 | Requires OTP (see console output) |
| Client | client@example.com | client1234 | Standard client portal |

> **OTP Note:** In development, `EMAIL_BACKEND = console`. The OTP code is printed to the terminal — look for the email output after entering staff credentials.

---

## Project Structure

```
attribute_survey/
├── attribute_survey/       # Django project settings & URLs
│   ├── settings.py
│   └── urls.py
├── accounts/               # Custom User model, login, OTP, staff auth
│   ├── models.py           # User, OTPCode, StaffProfile
│   ├── views.py            # Client login/register, staff OTP flow
│   ├── staff_views.py      # Staff dashboard, quotation review, project stages
│   ├── urls.py
│   └── staff_urls.py
├── services/               # Service catalogue (admin-managed)
│   ├── models.py           # Service, ServiceCategory
│   └── views.py
├── quotations/             # Quotation request → review → accept/reject
│   ├── models.py
│   ├── forms.py
│   └── views.py
├── clients/                # Client profiles (auto-created on quotation accept)
│   ├── models.py
│   └── utils.py            # create_client_from_quotation()
├── projects/               # Projects with stage trackers
│   ├── models.py           # Project, ProjectStage, ProjectDocument
│   └── forms.py
├── payments/               # Invoices + PDF generation
│   ├── models.py           # Invoice
│   ├── views.py
│   └── pdf_generator.py    # ReportLab invoice PDF
├── core/                   # Homepage, about, contact, dashboard
│   ├── views.py
│   └── management/commands/seed_data.py
├── templates/              # All HTML templates
│   ├── base.html           # Sidebar layout for authenticated pages
│   ├── core/               # home, dashboard, about, contact
│   ├── registration/       # login, register
│   ├── staff/              # Staff dashboard, OTP, project management
│   ├── services/           # Service list & detail
│   ├── quotations/         # Request, list, detail
│   ├── projects/           # List, detail with progress tracker
│   └── payments/           # Invoice detail, payment confirm, list
├── static/                 # CSS, JS, images
├── media/                  # User uploads
├── requirements.txt
└── setup.sh
```

---

## Key Workflows

### 1. Quotation Lifecycle
```
Client requests quote  →  Staff reviews & sets price  →  Status: "Awaiting Client"
→  Client accepts  →  Client profile created  →  Invoice generated  →  Redirect to payment
→  Client pays & enters reference  →  Project activated
```

### 2. Staff OTP Login
```
Staff visits /staff/login/  →  Enters email + password  →  OTP emailed  →
Enters 6-digit code  →  Granted access to staff dashboard
```

### 3. Project Progress
```
Admin assigns project to staff  →  Staff opens project  →  Updates each stage status
(Pending → In Progress → Completed)  →  Progress % auto-calculates  →
Client sees live updates on their dashboard
```

---

## Production Checklist

1. **Set `DEBUG = False`** and update `ALLOWED_HOSTS` in `settings.py`
2. **Replace SQLite** with PostgreSQL:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'attribute_db',
           'USER': 'db_user',
           'PASSWORD': 'db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```
3. **Configure real email** (Gmail / SendGrid / Mailgun):
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'your@gmail.com'
   EMAIL_HOST_PASSWORD = 'app_password_here'
   ```
4. **Set a strong SECRET_KEY** (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
5. **Run** `python manage.py collectstatic`
6. **Configure NGINX + Gunicorn** or deploy to Railway / Heroku / DigitalOcean

---

## Customisation

| What to change | Where |
|---|---|
| Company name / phone / address | `settings.py` → `COMPANY_*` constants |
| OTP expiry time | `settings.py` → `OTP_EXPIRY_MINUTES` |
| Payment instructions (Paybill, bank account) | `templates/payments/detail.html`, `templates/payments/confirm_payment.html`, `payments/pdf_generator.py` |
| Invoice VAT rate | `payments/models.py` → `vat_amount` property |
| Default project stages | `clients/utils.py` → `default_stages` list |
| Logo / brand colours | `templates/base.html` → `:root` CSS variables |

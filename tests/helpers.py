"""
tests/helpers.py — shared factories and mixins for all test modules
"""
import datetime
from decimal import Decimal
from django.utils import timezone
from django.utils.text import slugify
from accounts.models import User, OTPCode, StaffProfile
from services.models import Service, ServiceCategory
from quotations.models import Quotation
from clients.models import Client
from projects.models import Project, ProjectStage
from payments.models import Invoice


# ── USER FACTORIES ────────────────────────────────────────────────────────────

def make_client_user(email='client@example.com', password='testpass123', **kwargs):
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=kwargs.pop('first_name', 'John'),
        last_name=kwargs.pop('last_name', 'Doe'),
        role=User.ROLE_CLIENT,
        phone=kwargs.pop('phone', '+254700000001'),
        **kwargs,
    )
    return user


def make_staff_user(email='staff@example.com', password='testpass123', **kwargs):
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=kwargs.pop('first_name', 'Jane'),
        last_name=kwargs.pop('last_name', 'Staff'),
        role=User.ROLE_STAFF,
        is_staff=True,
        phone=kwargs.pop('phone', '+254700000002'),
        **kwargs,
    )
    StaffProfile.objects.create(
        user=user,
        designation='Surveyor',
        department='Field',
        employee_id=f'EMP-{user.pk}',
    )
    return user


def make_admin_user(email='admin@example.com', password='testpass123', **kwargs):
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name='Admin',
        last_name='User',
        role=User.ROLE_ADMIN,
        is_staff=True,
        is_superuser=True,
        **kwargs,
    )
    return user


# ── SERVICE FACTORIES ─────────────────────────────────────────────────────────

def make_category(name='Boundary & Title', icon='geo-alt'):
    cat, _ = ServiceCategory.objects.get_or_create(name=name, defaults={'icon': icon})
    return cat


def make_service(name='Boundary Survey', base_price=25000, **kwargs):
    cat = kwargs.pop('category', None) or make_category()
    slug = kwargs.pop('slug', slugify(name))
    svc, _ = Service.objects.get_or_create(
        slug=slug,
        defaults={
            'name': name,
            'category': cat,
            'description': 'A professional survey service.',
            'short_description': 'Survey service.',
            'base_price': Decimal(str(base_price)),
            'is_active': True,
            'deliverables': 'Survey Report\nDeed Plan',
            'duration_estimate': '1-2 weeks',
            **kwargs,
        }
    )
    return svc


# ── QUOTATION FACTORIES ───────────────────────────────────────────────────────

def make_quotation(user, service=None, status='pending', quoted_amount=None, **kwargs):
    service = service or make_service()
    return Quotation.objects.create(
        user=user,
        service=service,
        property_location='Karen, Nairobi',
        property_size='2 acres',
        description='Need a boundary survey for my plot.',
        urgency='normal',
        status=status,
        quoted_amount=Decimal(str(quoted_amount)) if quoted_amount else None,
        **kwargs,
    )


def make_reviewed_quotation(user, service=None, quoted_amount=50000):
    """Quotation that staff has reviewed and sent to client."""
    q = make_quotation(user, service=service, status='awaiting_client',
                       quoted_amount=quoted_amount)
    return q


# ── CLIENT / PROJECT / INVOICE FACTORIES ──────────────────────────────────────

def make_client(user, assigned_staff=None, **kwargs):
    client, _ = Client.objects.get_or_create(
        user=user,
        defaults={
            'status': Client.STATUS_ACTIVE,
            'assigned_staff': assigned_staff,
            **kwargs,
        }
    )
    return client


def make_invoice(client, quotation=None, amount=50000, status='unpaid'):
    return Invoice.objects.create(
        client=client,
        quotation=quotation,
        amount=Decimal(str(amount)),
        description='Professional survey services.',
        due_date=timezone.now().date() + datetime.timedelta(days=14),
        status=status,
    )


def make_project(client, service=None, staff=None, status='not_started', **kwargs):
    service = service or make_service()
    return Project.objects.create(
        client=client,
        service=service,
        title=f'{service.name} – Karen',
        description='Project description.',
        property_location='Karen, Nairobi',
        status=status,
        assigned_staff=staff,
        progress_percentage=0,
        **kwargs,
    )


def make_stage(project, order=1, name='Site Visit', status='pending', **kwargs):
    return ProjectStage.objects.create(
        project=project,
        order=order,
        name=name,
        description='Stage description.',
        status=status,
        **kwargs,
    )


# ── AUTH MIXINS ───────────────────────────────────────────────────────────────

class ClientLoginMixin:
    """Log in as a client user before each test."""
    def setUp(self):
        super().setUp()
        self.client_user = make_client_user()
        self.client.login(username='client@example.com', password='testpass123')


class StaffLoginMixin:
    """Log in as a staff user with OTP session flag set."""
    def setUp(self):
        super().setUp()
        self.staff_user = make_staff_user()
        self.client.login(username='staff@example.com', password='testpass123')
        session = self.client.session
        session['staff_authenticated'] = True
        session.save()


class AdminLoginMixin:
    """Log in as an admin user with OTP session flag set."""
    def setUp(self):
        super().setUp()
        self.admin_user = make_admin_user()
        self.client.login(username='admin@example.com', password='testpass123')
        session = self.client.session
        session['staff_authenticated'] = True
        session.save()

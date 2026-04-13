"""
tests/test_clients.py — Client model, assignment, create_client_from_quotation utility
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from clients.models import Client
from clients.utils import create_client_from_quotation
from projects.models import Project, ProjectStage
from payments.models import Invoice
from tests.helpers import (
    make_client_user, make_staff_user, make_admin_user,
    make_service, make_quotation, make_reviewed_quotation,
    make_client, make_project,
    StaffLoginMixin, AdminLoginMixin,
)


# ── CLIENT MODEL ──────────────────────────────────────────────────────────────

class ClientModelTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.client_obj = make_client(self.user)

    def test_client_id_auto_generated(self):
        self.assertIsNotNone(self.client_obj.client_id)
        self.assertTrue(self.client_obj.client_id.startswith('CLT-'))

    def test_client_id_unique(self):
        user2 = make_client_user(email='user2@example.com')
        client2 = make_client(user2)
        self.assertNotEqual(self.client_obj.client_id, client2.client_id)

    def test_str_contains_client_id_and_name(self):
        result = str(self.client_obj)
        self.assertIn(self.client_obj.client_id, result)
        self.assertIn(self.user.get_full_name(), result)

    def test_default_status_is_active(self):
        self.assertEqual(self.client_obj.status, Client.STATUS_ACTIVE)

    def test_active_projects_count(self):
        service = make_service()
        make_project(self.client_obj, service, status='in_progress')
        make_project(self.client_obj, make_service(name='Other', slug='other'), status='completed')
        self.assertEqual(self.client_obj.active_projects, 1)

    def test_total_projects_count(self):
        service = make_service()
        make_project(self.client_obj, service, status='in_progress')
        make_project(self.client_obj, make_service(name='Other2', slug='other2'), status='completed')
        self.assertEqual(self.client_obj.total_projects, 2)

    def test_one_to_one_with_user(self):
        with self.assertRaises(Exception):
            Client.objects.create(user=self.user, status=Client.STATUS_ACTIVE)

    def test_assigned_staff_can_be_null(self):
        self.assertIsNone(self.client_obj.assigned_staff)

    def test_assign_staff(self):
        staff = make_staff_user()
        self.client_obj.assigned_staff = staff
        self.client_obj.save()
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.assigned_staff, staff)


# ── CREATE CLIENT FROM QUOTATION UTILITY ──────────────────────────────────────

class CreateClientFromQuotationTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.service = make_service()

    def test_creates_client(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        self.assertIsNotNone(client)
        self.assertEqual(client.user, self.user)

    def test_creates_invoice(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.amount, Decimal('50000'))
        self.assertEqual(invoice.client, client)

    def test_invoice_linked_to_quotation(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        self.assertEqual(invoice.quotation, q)

    def test_invoice_status_is_unpaid(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        self.assertEqual(invoice.status, Invoice.STATUS_UNPAID)

    def test_creates_project(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        self.assertTrue(Project.objects.filter(client=client).exists())

    def test_project_has_six_default_stages(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        project = Project.objects.get(client=client)
        self.assertEqual(project.stages.count(), 6)

    def test_all_default_stages_are_pending(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        project = Project.objects.get(client=client)
        statuses = project.stages.values_list('status', flat=True)
        self.assertTrue(all(s == 'pending' for s in statuses))

    def test_project_title_contains_service_name(self):
        q = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        client, invoice = create_client_from_quotation(q)
        project = Project.objects.get(client=client)
        self.assertIn(self.service.name, project.title)

    def test_second_call_reuses_existing_client(self):
        q1 = make_reviewed_quotation(self.user, self.service, quoted_amount=50000)
        create_client_from_quotation(q1)
        service2 = make_service(name='Topo Survey', slug='topo')
        q2 = make_reviewed_quotation(self.user, service2, quoted_amount=60000)
        create_client_from_quotation(q2)
        self.assertEqual(Client.objects.filter(user=self.user).count(), 1)

    def test_null_quoted_amount_defaults_to_zero(self):
        q = make_quotation(self.user, self.service, status='awaiting_client', quoted_amount=None)
        client, invoice = create_client_from_quotation(q)
        self.assertEqual(invoice.amount, Decimal('0'))


# ── STAFF CLIENTS VIEW ────────────────────────────────────────────────────────

class StaffClientsViewTest(StaffLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client_user = make_client_user()
        self.client_obj = make_client(self.client_user, assigned_staff=self.staff_user)

    def test_staff_clients_page_loads(self):
        response = self.client.get(reverse('staff_clients'))
        self.assertEqual(response.status_code, 200)

    def test_staff_sees_directly_assigned_clients(self):
        response = self.client.get(reverse('staff_clients'))
        self.assertContains(response, self.client_obj.client_id)

    def test_staff_sees_clients_from_assigned_projects(self):
        # Client not directly assigned but linked via a project
        unassigned_client_user = make_client_user(email='proj@example.com')
        unassigned_client = make_client(unassigned_client_user)
        service = make_service()
        make_project(unassigned_client, service, staff=self.staff_user)
        response = self.client.get(reverse('staff_clients'))
        self.assertContains(response, unassigned_client.client_id)

    def test_staff_does_not_see_unrelated_clients(self):
        other_staff = make_staff_user(email='other_staff@example.com')
        unrelated_user = make_client_user(email='unrelated@example.com')
        unrelated_client = make_client(unrelated_user, assigned_staff=other_staff)
        response = self.client.get(reverse('staff_clients'))
        self.assertNotContains(response, unrelated_client.client_id)


class AdminClientsViewTest(AdminLoginMixin, TestCase):

    def test_admin_sees_all_clients(self):
        user1 = make_client_user(email='c1@example.com')
        user2 = make_client_user(email='c2@example.com')
        c1 = make_client(user1)
        c2 = make_client(user2)
        response = self.client.get(reverse('staff_clients'))
        self.assertContains(response, c1.client_id)
        self.assertContains(response, c2.client_id)

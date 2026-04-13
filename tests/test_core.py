"""
tests/test_core.py — Homepage, dashboard, about, contact page tests
"""
from django.test import TestCase
from django.urls import reverse
from tests.helpers import make_client_user, make_staff_user, make_service, ClientLoginMixin


class HomepageTest(TestCase):

    def test_homepage_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_shows_services(self):
        svc = make_service(is_featured=True)
        response = self.client.get(reverse('home'))
        self.assertContains(response, svc.name)

    def test_homepage_has_login_link_when_unauthenticated(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('login'))

    def test_homepage_has_dashboard_link_when_authenticated(self):
        make_client_user()
        self.client.login(username='client@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('dashboard'))


class AboutPageTest(TestCase):

    def test_about_page_loads(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_about_page_contains_company_info(self):
        response = self.client.get(reverse('about'))
        self.assertContains(response, 'Attribute')


class ContactPageTest(TestCase):

    def test_contact_page_loads(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)

    def test_contact_form_post_redirects(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+254700000000',
            'subject': 'Enquiry',
            'message': 'Hello, I need a survey.',
        })
        self.assertRedirects(response, reverse('contact'))


class DashboardTest(ClientLoginMixin, TestCase):

    def test_dashboard_loads_for_client(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_to_login_when_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_staff_redirected_from_client_dashboard_to_staff_dashboard(self):
        self.client.logout()
        staff = make_staff_user()
        self.client.login(username='staff@example.com', password='testpass123')
        session = self.client.session
        session['staff_authenticated'] = True
        session.save()
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('staff_dashboard'))

    def test_dashboard_shows_username(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, self.client_user.first_name)

    def test_dashboard_shows_request_quotation_link(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, reverse('request_quotation'))


class ProfileViewTest(ClientLoginMixin, TestCase):

    def test_profile_page_loads(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        response = self.client.post(reverse('profile'), {
            'first_name': 'UpdatedName',
            'last_name': 'Doe',
            'phone': '+254711222333',
            'id_number': '',
            'address': 'Westlands, Nairobi',
        })
        self.assertRedirects(response, reverse('profile'))
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.first_name, 'UpdatedName')
        self.assertEqual(self.client_user.address, 'Westlands, Nairobi')

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

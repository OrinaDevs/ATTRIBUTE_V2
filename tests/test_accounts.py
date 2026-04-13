"""
tests/test_accounts.py — User model, OTP, registration, login, staff auth
"""
import datetime
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.utils import timezone
from accounts.models import User, OTPCode, StaffProfile
from tests.helpers import make_client_user, make_staff_user, make_admin_user


# ── USER MODEL ────────────────────────────────────────────────────────────────

class UserModelTest(TestCase):

    def test_create_client_user(self):
        user = make_client_user()
        self.assertEqual(user.role, User.ROLE_CLIENT)
        self.assertFalse(user.is_staff_member)
        self.assertFalse(user.is_admin_member)

    def test_create_staff_user(self):
        user = make_staff_user()
        self.assertEqual(user.role, User.ROLE_STAFF)
        self.assertTrue(user.is_staff_member)
        self.assertFalse(user.is_admin_member)

    def test_create_admin_user(self):
        user = make_admin_user()
        self.assertEqual(user.role, User.ROLE_ADMIN)
        self.assertTrue(user.is_staff_member)
        self.assertTrue(user.is_admin_member)

    def test_full_name_property(self):
        user = make_client_user()
        self.assertEqual(user.full_name, 'John Doe')

    def test_full_name_falls_back_to_email(self):
        user = User.objects.create_user(
            username='nk@example.com',
            email='nk@example.com',
            password='pass',
            first_name='',
            last_name='',
        )
        self.assertEqual(user.full_name, 'nk@example.com')

    def test_email_is_unique(self):
        make_client_user(email='dup@example.com')
        with self.assertRaises(Exception):
            make_client_user(email='dup@example.com')

    def test_str_representation(self):
        user = make_client_user()
        self.assertIn('client@example.com', str(user))


# ── OTP MODEL ─────────────────────────────────────────────────────────────────

class OTPCodeModelTest(TestCase):

    def setUp(self):
        self.user = make_staff_user()

    def test_generate_creates_six_digit_code(self):
        otp = OTPCode.generate(self.user)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())

    def test_generate_invalidates_previous_codes(self):
        otp1 = OTPCode.generate(self.user)
        otp2 = OTPCode.generate(self.user)
        otp1.refresh_from_db()
        self.assertTrue(otp1.used)
        self.assertFalse(otp2.used)

    def test_is_valid_returns_true_for_fresh_code(self):
        otp = OTPCode.generate(self.user)
        self.assertTrue(otp.is_valid)

    def test_is_valid_returns_false_for_used_code(self):
        otp = OTPCode.generate(self.user)
        otp.used = True
        otp.save()
        self.assertFalse(otp.is_valid)

    def test_is_valid_returns_false_for_expired_code(self):
        otp = OTPCode.generate(self.user)
        otp.expires_at = timezone.now() - datetime.timedelta(minutes=1)
        otp.save()
        self.assertFalse(otp.is_valid)

    def test_verify_correct_code_returns_true(self):
        otp = OTPCode.generate(self.user)
        result = OTPCode.verify(self.user, otp.code)
        self.assertTrue(result)

    def test_verify_marks_code_as_used(self):
        otp = OTPCode.generate(self.user)
        OTPCode.verify(self.user, otp.code)
        otp.refresh_from_db()
        self.assertTrue(otp.used)

    def test_verify_wrong_code_returns_false(self):
        OTPCode.generate(self.user)
        result = OTPCode.verify(self.user, '000000')
        self.assertFalse(result)

    def test_verify_expired_code_returns_false(self):
        otp = OTPCode.generate(self.user)
        otp.expires_at = timezone.now() - datetime.timedelta(minutes=1)
        otp.save()
        result = OTPCode.verify(self.user, otp.code)
        self.assertFalse(result)

    def test_verify_already_used_code_returns_false(self):
        otp = OTPCode.generate(self.user)
        OTPCode.verify(self.user, otp.code)
        result = OTPCode.verify(self.user, otp.code)
        self.assertFalse(result)


# ── REGISTRATION VIEW ─────────────────────────────────────────────────────────

class RegistrationViewTest(TestCase):

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')

    def test_successful_registration(self):
        response = self.client.post(reverse('register'), {
            'first_name': 'Alice',
            'last_name': 'Wanjiru',
            'email': 'alice@example.com',
            'phone': '+254722000000',
            'id_number': '12345678',
            'address': 'Nairobi',
            'password1': 'Str0ngPass!99',
            'password2': 'Str0ngPass!99',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(email='alice@example.com').exists())

    def test_registration_sets_role_to_client(self):
        self.client.post(reverse('register'), {
            'first_name': 'Bob',
            'last_name': 'Kamau',
            'email': 'bob@example.com',
            'phone': '+254733000000',
            'password1': 'Str0ngPass!99',
            'password2': 'Str0ngPass!99',
        })
        user = User.objects.get(email='bob@example.com')
        self.assertEqual(user.role, User.ROLE_CLIENT)

    def test_registration_with_mismatched_passwords_fails(self):
        response = self.client.post(reverse('register'), {
            'first_name': 'Carol',
            'last_name': 'Test',
            'email': 'carol@example.com',
            'phone': '+254744000000',
            'password1': 'Str0ngPass!99',
            'password2': 'WrongPass!00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='carol@example.com').exists())

    def test_duplicate_email_registration_fails(self):
        make_client_user(email='taken@example.com')
        response = self.client.post(reverse('register'), {
            'first_name': 'Dave',
            'last_name': 'Test',
            'email': 'taken@example.com',
            'phone': '+254755000000',
            'password1': 'Str0ngPass!99',
            'password2': 'Str0ngPass!99',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='taken@example.com').count(), 1)

    def test_authenticated_user_redirected_from_register(self):
        make_client_user()
        self.client.login(username='client@example.com', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('dashboard'))


# ── CLIENT LOGIN ──────────────────────────────────────────────────────────────

class ClientLoginViewTest(TestCase):

    def setUp(self):
        self.user = make_client_user()

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_successful_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'client@example.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_wrong_password_stays_on_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'client@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')

    def test_nonexistent_email_fails(self):
        response = self.client.post(reverse('login'), {
            'username': 'ghost@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects_to_home(self):
        self.client.login(username='client@example.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))


# ── STAFF LOGIN + OTP ─────────────────────────────────────────────────────────

class StaffLoginViewTest(TestCase):

    def setUp(self):
        self.staff = make_staff_user()

    def test_staff_login_page_loads(self):
        response = self.client.get(reverse('staff_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Portal')

    def test_staff_login_with_correct_credentials_redirects_to_otp(self):
        response = self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('staff_otp_verify'))

    def test_staff_login_stores_user_id_in_session(self):
        self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(self.client.session['staff_otp_user_id'], self.staff.pk)

    def test_staff_login_generates_otp(self):
        self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'testpass123',
        })
        self.assertTrue(OTPCode.objects.filter(user=self.staff, used=False).exists())

    def test_client_user_blocked_from_staff_login(self):
        client_user = make_client_user()
        response = self.client.post(reverse('staff_login'), {
            'username': 'client@example.com',
            'password': 'testpass123',
        })
        self.assertNotEqual(self.client.session.get('staff_otp_user_id'), client_user.pk)

    def test_staff_wrong_password_stays_on_login(self):
        response = self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(OTPCode.objects.filter(user=self.staff).exists())

    def test_otp_verify_page_loads_after_password_step(self):
        self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'testpass123',
        })
        response = self.client.get(reverse('staff_otp_verify'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OTP')

    def test_otp_verify_without_session_redirects_to_login(self):
        response = self.client.get(reverse('staff_otp_verify'))
        self.assertRedirects(response, reverse('staff_login'))

    def test_correct_otp_logs_in_staff(self):
        self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'testpass123',
        })
        otp = OTPCode.objects.filter(user=self.staff, used=False).latest('created_at')
        response = self.client.post(reverse('staff_otp_verify'), {'code': otp.code})
        self.assertRedirects(response, reverse('staff_dashboard'))
        self.assertTrue(self.client.session.get('staff_authenticated'))

    def test_wrong_otp_stays_on_verify_page(self):
        self.client.post(reverse('staff_login'), {
            'username': 'staff@example.com',
            'password': 'testpass123',
        })
        response = self.client.post(reverse('staff_otp_verify'), {'code': '000000'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.session.get('staff_authenticated'))

    def test_staff_dashboard_blocked_without_otp_session(self):
        self.client.login(username='staff@example.com', password='testpass123')
        response = self.client.get(reverse('staff_dashboard'))
        self.assertRedirects(response, reverse('staff_login'))

    def test_staff_dashboard_accessible_with_otp_session(self):
        self.client.login(username='staff@example.com', password='testpass123')
        session = self.client.session
        session['staff_authenticated'] = True
        session.save()
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)

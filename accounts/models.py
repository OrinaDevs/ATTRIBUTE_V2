from django.contrib.auth.models import AbstractUser
from django.db import models
import pyotp
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class User(AbstractUser):
    ROLE_CLIENT = 'client'
    ROLE_STAFF = 'staff'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Client'),
        (ROLE_STAFF, 'Staff'),
        (ROLE_ADMIN, 'Admin'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    phone = models.CharField(max_length=20, blank=True)
    id_number = models.CharField(max_length=30, blank=True, verbose_name='ID/Passport Number')
    address = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def is_staff_member(self):
        return self.role in [self.ROLE_STAFF, self.ROLE_ADMIN]

    @property
    def is_admin_member(self):
        return self.role == self.ROLE_ADMIN

    @property
    def full_name(self):
        return self.get_full_name() or self.email


class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, default='staff_login')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            )
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def generate(cls, user, purpose='staff_login'):
        # Invalidate old codes
        cls.objects.filter(user=user, purpose=purpose, used=False).update(used=True)
        code = ''.join(random.choices(string.digits, k=6))
        return cls.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(
                minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            )
        )

    @classmethod
    def verify(cls, user, code, purpose='staff_login'):
        try:
            otp = cls.objects.filter(
                user=user, code=code, purpose=purpose, used=False
            ).latest('created_at')
            if otp.is_valid:
                otp.used = True
                otp.save()
                return True
        except cls.DoesNotExist:
            pass
        return False


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=30, unique=True, blank=True)
    bio = models.TextField(blank=True)
    is_active_staff = models.BooleanField(default=True)

    def __str__(self):
        return f"Staff: {self.user.full_name}"

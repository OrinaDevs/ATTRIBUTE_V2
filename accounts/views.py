from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import User, OTPCode
from .forms import UserRegistrationForm, EmailAuthenticationForm, OTPForm, UserProfileForm
from projects.models import Project
from quotations.models import Quotation


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    user = request.user
    if user.is_staff_member:
        return redirect('staff_dashboard')

    context = {
        'quotations': Quotation.objects.filter(user=user).order_by('-created_at')[:5],
        'projects': Project.objects.filter(client__user=user).order_by('-created_at')[:5],
        'pending_quotations': Quotation.objects.filter(user=user, status='pending').count(),
        'active_projects': Project.objects.filter(client__user=user, status='in_progress').count(),
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# ── STAFF AUTH ──

def staff_login(request):
    """Step 1: Staff enters email + password"""
    if request.user.is_authenticated and request.user.is_staff_member and request.session.get('staff_authenticated'):
        return redirect('staff_dashboard')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff_member:
                messages.error(request, 'This portal is for staff only.')
                return redirect('staff_login')
            # Store user id in session for OTP step
            request.session['staff_otp_user_id'] = user.id
            # Generate and send OTP
            otp = OTPCode.generate(user, purpose='staff_login')
            _send_otp_email(user, otp.code)
            messages.info(request, f'OTP sent to {user.email}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes.')
            return redirect('staff_otp_verify')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'staff/login.html', {'form': form})


def staff_otp_verify(request):
    """Step 2: Staff enters OTP"""
    user_id = request.session.get('staff_otp_user_id')
    if not user_id:
        return redirect('staff_login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('staff_login')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if OTPCode.verify(user, code, purpose='staff_login'):
                del request.session['staff_otp_user_id']
                login(request, user)
                request.session['staff_authenticated'] = True
                messages.success(request, f'Welcome, {user.first_name}! Staff dashboard access granted.')
                return redirect('staff_dashboard')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
    else:
        form = OTPForm()
    return render(request, 'staff/otp_verify.html', {'form': form, 'email': user.email})


def staff_resend_otp(request):
    user_id = request.session.get('staff_otp_user_id')
    if not user_id:
        return redirect('staff_login')
    try:
        user = User.objects.get(id=user_id)
        otp = OTPCode.generate(user, purpose='staff_login')
        _send_otp_email(user, otp.code)
        messages.info(request, 'A new OTP has been sent to your email.')
    except User.DoesNotExist:
        pass
    return redirect('staff_otp_verify')


def _send_otp_email(user, code):
    send_mail(
        subject='Your Staff Login OTP – Attribute Land Survey',
        message=(
            f'Hello {user.first_name},\n\n'
            f'Your one-time password (OTP) for staff dashboard access is:\n\n'
            f'  {code}\n\n'
            f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n'
            f'If you did not request this, please contact the administrator immediately.\n\n'
            f'Attribute Land Survey & Consultants'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
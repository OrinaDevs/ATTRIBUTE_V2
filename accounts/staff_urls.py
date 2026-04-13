from django.urls import path
from . import views
from . import staff_views

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('otp/', views.staff_otp_verify, name='staff_otp_verify'),
    path('otp/resend/', views.staff_resend_otp, name='staff_resend_otp'),
    path('dashboard/', staff_views.staff_dashboard, name='staff_dashboard'),
    path('quotations/', staff_views.staff_quotations, name='staff_quotations'),
    path('quotations/<int:pk>/review/', staff_views.review_quotation, name='review_quotation'),
    path('projects/', staff_views.staff_projects, name='staff_projects'),
    path('projects/<int:pk>/', staff_views.staff_project_detail, name='staff_project_detail'),
    path('projects/<int:pk>/update-stage/', staff_views.update_project_stage, name='update_project_stage'),
    path('clients/', staff_views.staff_clients, name='staff_clients'),
]

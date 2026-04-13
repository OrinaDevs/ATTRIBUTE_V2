from django.urls import path
from . import views
from accounts.views import dashboard

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', dashboard, name='dashboard'),
]
